import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Devamsızlık Takip Sistemi", layout="wide")

st.title("📊 Devamsızlık Takip Uygulaması")
st.markdown("### MEB (e-Okul) Raporu İşleme Sistemi")
st.info("Sistem; İsimleri F, Tarihleri K, Türleri M ve Günleri O sütunundan alacak şekilde ayarlandı.")

uploaded_file = st.file_uploader("MEB'den aldığınız Excel dosyasını seçin", type=["xlsx", "xls"])

if uploaded_file:
    df_raw = None
    
    # 1. DOSYAYI OKUMA
    try:
        # MEB dosyaları genellikle eski tip olduğu için xlrd öncelikli denenebilir
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
            # 2. VERİLERİ SÜTUNLARDAN ÇEKME (Senin verdiğin koordinatlar)
            # Python'da sayım 0'dan başladığı için:
            # F = 5 (İsim), K = 10 (Tarih), M = 12 (Tür), O = 14 (Gün Sayısı)
            
            # Önce 6. satırdan (index 5) sonrasını alalım (Data başlangıcı)
            df = df_raw.iloc[6:].copy() 
            
            # Belirlediğimiz sütunları seçelim
            # Not: Eğer dosyanın sütun sayısı az ise hata vermemesi için kontrol ekliyoruz
            df = df.iloc[:, [5, 10, 12, 14]]
            df.columns = ["Adı Soyadı", "Tarihi", "Türü", "Gün Sayısı"]
            
            # 3. VERİ TEMİZLEME
            # İsim alanı boş olan veya içinde "Adı Soyadı" yazan (başlık tekrarı) satırları at
            df = df[df["Adı Soyadı"].notna()]
            df = df[df["Adı Soyadı"].astype(str).str.contains("Adı Soyadı") == False]
            
            # Tarihleri düzelt (Türkiye formatı)
            df["Tarihi"] = pd.to_datetime(df["Tarihi"], errors='coerce', dayfirst=True)
            df = df.dropna(subset=["Tarihi"])
            
            # Gün sayısını sayıya çevir
            df["Gün Sayısı"] = pd.to_numeric(df["Gün Sayısı"], errors='coerce').fillna(0)
            
            # 4. AY SEÇİMİ VE FİLTRELEME
            aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                     "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            secilen_ay_adi = st.selectbox("Rapor İstediğiniz Ayı Seçin:", aylar)
            secilen_ay_no = aylar.index(secilen_ay_adi) + 1
            
            # Türü temizle (N ve F'yi ele)
            df["Türü"] = df["Türü"].astype(str).str.strip().str.upper()
            mask = (df["Türü"] != "N") & (df["Türü"] != "F") & (df["Tarihi"].dt.month == secilen_ay_no)
            final_df = df[mask].copy()

            # 5. SONUÇLARI GÖSTER
            st.divider()
            if not final_df.empty:
                # İsimlere göre topla ve alfabetik diz
                ozet = final_df.groupby("Adı Soyadı")["Gün Sayısı"].sum().reset_index()
                ozet = ozet.sort_values("Adı Soyadı")
                
                st.success(f"✅ {secilen_ay_adi} ayı için toplam {len(ozet)} öğrenci listelendi.")
                
                # Tabloyu göster
                st.table(ozet) # dataframe yerine table daha okunaklı olabilir
                
                # İndirme Butonu
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    ozet.to_excel(writer, index=False, sheet_name='Devamsizlik_Raporu')
                
                st.download_button(
                    label="📄 Sonuçları Excel Olarak İndir",
                    data=output.getvalue(),
                    file_name=f"Devamsizlik_Raporu_{secilen_ay_adi}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning(f"Seçilen ayda ({secilen_ay_adi}) kriterlere uygun (N ve F harici) devamsızlık bulunamadı.")
                
                # Debug (Veri neden gelmiyor kontrolü)
                with st.expander("Dosya İçeriği Kontrolü (Hata varsa buraya bakın)"):
                    st.write("Uygulamanın dosyadan okuduğu ilk 10 satır:")
                    st.write(df.head(10))

        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
            st.info("Not: MEB dosyasının yapısı beklenen (F, K, M, O) sütunlarından farklı olabilir.")
