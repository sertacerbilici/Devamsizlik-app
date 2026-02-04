import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Devamsızlık Takip Sistemi", layout="wide")

# TÜRKÇE SIRALAMA İÇİN YARDIMCI FONKSİYON
def turkce_sirala(text):
    # Türkçe karakterlerin alfabedeki doğru yerlerini tanımlıyoruz
    duzeltme = str.maketrans("çğıöşüİÇĞİÖŞÜ", "czioosicgiosu")
    alfabe = "abcçdefgğhıijklmnoöprsştuüvyz"
    # Her harfi alfabedeki sırasına göre bir sayı dizisine çevirir
    return [alfabe.find(c.lower()) if c.lower() in alfabe else ord(c) for c in str(text)]

st.title("📊 Devamsızlık Takip Uygulaması")
st.info("Sistem; İsimleri F, Tarihleri K, Türleri M ve Günleri O sütunundan alacak şekilde ayarlandı.")

uploaded_file = st.file_uploader("MEB'den aldığınız Excel dosyasını seçin", type=["xlsx", "xls"])

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
            # 1. VERİLERİ SÜTUNLARDAN ÇEKME (F=5, K=10, M=12, O=14)
            df = df_raw.iloc[6:].copy() 
            df = df.iloc[:, [5, 10, 12, 14]]
            df.columns = ["Adı Soyadı", "Tarihi", "Türü", "Gün Sayısı"]
            
            # 2. TEMİZLİK VE TARİH DÖNÜŞÜMÜ
            df = df[df["Adı Soyadı"].notna()]
            df = df[df["Adı Soyadı"].astype(str).str.contains("Adı Soyadı") == False]
            df["Tarihi"] = pd.to_datetime(df["Tarihi"], errors='coerce', dayfirst=True)
            df = df.dropna(subset=["Tarihi"])
            
            # Gün sayısını 1 ondalık basamaklı sayıya çevir
            df["Gün Sayısı"] = pd.to_numeric(df["Gün Sayısı"], errors='coerce').fillna(0)
            
            # 3. AY SEÇİMİ VE FİLTRELEME
            aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                     "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            secilen_ay_adi = st.selectbox("Rapor İstediğiniz Ayı Seçin:", aylar)
            secilen_ay_no = aylar.index(secilen_ay_adi) + 1
            
            # Tür filtreleme (N ve F'yi ele)
            df["Türü"] = df["Türü"].astype(str).str.strip().str.upper()
            mask = (df["Türü"] != "N") & (df["Türü"] != "F") & (df["Tarihi"].dt.month == secilen_ay_no)
            final_df = df[mask].copy()

            # 4. ÖZET TABLO VE TÜRKÇE SIRALAMA
            if not final_df.empty:
                # Toplama yap
                ozet = final_df.groupby("Adı Soyadı")["Gün Sayısı"].sum().reset_index()
                
                # Türkçe karakterlere göre sırala
                ozet["sirala_key"] = ozet["Adı Soyadı"].apply(turkce_sirala)
                ozet = ozet.sort_values(by="sirala_key").drop(columns=["sirala_key"])
                
                # Gün sayısı formatını düzelt (Örn: 1.5)
                ozet["Gün Sayısı"] = ozet["Gün Sayısı"].map('{:,.1f}'.format)
                
                # NUMARALANDIRMAYI 1'DEN BAŞLAT
                ozet.index = range(1, len(ozet) + 1)
                
                st.success(f"✅ {secilen_ay_adi} ayı raporu hazır!")
                
                # TABLO GÖRÜNÜMÜ
                st.table(ozet)
                
                # EXCEL İNDİRME
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    ozet.to_excel(writer, index=True, index_label="Sıra No")
                
                st.download_button(
                    label="📄 Raporu Excel Olarak İndir",
                    data=output.getvalue(),
                    file_name=f"Devamsizlik_Raporu_{secilen_ay_adi}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning(f"Seçilen ayda ({secilen_ay_adi}) kayıt bulunamadı.")

        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
