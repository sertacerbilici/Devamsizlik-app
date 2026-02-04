import streamlit as st
import pandas as pd
import io

# Sayfa Yapılandırması
st.set_page_config(page_title="Devamsızlık Takip Sistemi", layout="wide")

# CSS SİHRİ: Tüm İngilizce metinleri (Buton dahil) Türkçeleştirme
st.markdown("""
    <style>
    /* 1. Sürükle bırak talimatlarını değiştirme */
    [data-testid="stFileUploaderDropzoneInstructions"] div span {
        display: none;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] div::before {
        content: "Dosyayı buraya sürükleyip bırakın";
    }
    [data-testid="stFileUploaderDropzoneInstructions"] div::after {
        content: "Dosya sınırı: 200MB (.xlsx veya .xls)";
        display: block;
        font-size: 0.8em;
        color: gray;
    }

    /* 2. 'Browse Files' butonunu Türkçeleştirme */
    [data-testid="stFileUploader"] button {
        font-size: 0 !important;
    }
    [data-testid="stFileUploader"] button::before {
        content: "Dosyalara Göz At";
        font-size: 16px !important;
    }

    /* 3. Gereksiz uyarıları gizleme */
    [data-testid="stFileUploader"] label {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

# Türkçe Sıralama Fonksiyonu
def turkce_sirala(text):
    duzeltme = str.maketrans("çğıöşüİÇĞİÖŞÜ", "czioosicgiosu")
    alfabe = "abcçdefgğhıijklmnoöprsştuüvyz"
    return [alfabe.find(c.lower()) if c.lower() in alfabe else ord(c) for c in str(text)]

# Başlık ve Talimatlar
st.title("📊 Devamsızlık Takip Uygulaması")
st.markdown("""
**Lütfen,** e-Okul Devamsızlık Girişi sayfasında bulunan ekran raporlarından **OOK08001R060** kodlu raporu Excel olarak indirip aşağıya yükleyiniz.
**Not:** Devamsızlık hesaplamalarında F-Faaliyet ve N-Nöbet sayıları hesaplanmamaktadır.
""")

# Dosya Yükleme Alanı
uploaded_file = st.file_uploader("", type=["xlsx", "xls"])

if uploaded_file:
    df_raw = None
    try:
        try:
            df_raw = pd.read_excel(uploaded_file, header=None)
        except:
            uploaded_file.seek(0)
            df_raw = pd.read_excel(uploaded_file, header=None, engine='xlrd')
    except Exception as e:
        st.error(f"Dosya okunamadı: {e}")
        st.stop()

    if df_raw is not None:
        try:
            # Koordinatlardan veriyi çekme (F=5, K=10, M=12, O=14)
            df = df_raw.iloc[6:].copy() 
            df = df.iloc[:, [5, 10, 12, 14]]
            df.columns = ["Adı Soyadı", "Tarihi", "Türü", "Gün Sayısı"]
            
            # Veri Temizleme
            df = df[df["Adı Soyadı"].notna()]
            df = df[df["Adı Soyadı"].astype(str).str.contains("Adı Soyadı") == False]
            df["Tarihi"] = pd.to_datetime(df["Tarihi"], errors='coerce', dayfirst=True)
            df = df.dropna(subset=["Tarihi"])
            df["Gün Sayısı"] = pd.to_numeric(df["Gün Sayısı"], errors='coerce').fillna(0)
            
            # Ay Seçimi
            aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                     "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            secilen_ay_adi = st.selectbox("Lütfen Rapor İstediğiniz Ayı Seçin:", aylar)
            secilen_ay_no = aylar.index(secilen_ay_adi) + 1
            
            # Filtreleme
            df["Türü"] = df["Türü"].astype(str).str.strip().str.upper()
            mask = (df["Türü"] != "N") & (df["Türü"] != "F") & (df["Tarihi"].dt.month == secilen_ay_no)
            final_df = df[mask].copy()

            if not final_df.empty:
                # Gruplama ve Türkçe Sıralama
                ozet = final_df.groupby("Adı Soyadı")["Gün Sayısı"].sum().reset_index()
                ozet["sirala_key"] = ozet["Adı Soyadı"].apply(turkce_sirala)
                ozet = ozet.sort_values(by="sirala_key").drop(columns=["sirala_key"])
                
                # Formatlama (Ondalık basamak)
                ozet["Gün Sayısı"] = ozet["Gün Sayısı"].map('{:,.1f}'.format)
                ozet.index = range(1, len(ozet) + 1)
                
                # Başarı Mesajı
                st.success(f"✅ {secilen_ay_adi} ayı raporu hazır! Toplam {len(ozet)} öğrenci listelendi.")
                
                # Tablo Görünümü
                st.table(ozet)
                
                # Excel İndirme
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    ozet.to_excel(writer, index=True, index_label="Sıra No")
                
                st.download_button(
                    label="📥 Raporu Excel Olarak İndir",
                    data=output.getvalue(),
                    file_name=f"Devamsizlik_Raporu_{secilen_ay_adi}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning(f"Seçilen ayda ({secilen_ay_adi}) herhangi bir devamsızlık kaydı bulunamadı.")

        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
