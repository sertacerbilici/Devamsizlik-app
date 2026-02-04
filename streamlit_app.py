import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Devamsızlık Takip Sistemi", layout="centered")

st.title("📊 Devamsızlık Takip Uygulaması")
st.write("MEB'den aldığınız dosyayı (.xlsx veya .xls) yükleyin.")

uploaded_file = st.file_uploader("Excel dosyasını buraya sürükleyin", type=["xlsx", "xls"])

if uploaded_file:
    df = None
    
    # DOSYA OKUMA STRATEJİSİ: Önce modern, olmazsa eski tip dene
    try:
        # 1. Deneme: Modern Excel (.xlsx) olarak oku
        df = pd.read_excel(uploaded_file, header=7)
    except:
        try:
            # 2. Deneme: Eski tip Excel (.xls) olarak oku
            uploaded_file.seek(0) # Dosyayı başa sar
            df = pd.read_excel(uploaded_file, header=7, engine='xlrd')
        except Exception as e:
            st.error("Dosya ne yazık ki okunamadı. Lütfen dosyayı bilgisayarınızda açıp 'Farklı Kaydet' diyerek 'Excel Çalışma Kitabı (.xlsx)' olarak tekrar kaydedip yüklemeyi deneyin.")
            st.info(f"Hata detayı: {e}")

    if df is not None:
        try:
            # Sütunları ayıkla (E, J, L, N koordinatları: 4, 9, 11, 13)
            # MEB dosyalarında bazen sütun sayısı değişebilir, güvenli seçim yapalım
            secilecek_sutunlar = [4, 9, 11, 13]
            df = df.iloc[:, secilecek_sutunlar]
            df.columns = ["Adı Soyadı", "Tarihi", "Türü", "Gün Sayısı"]
            
            # Veri temizleme
            df = df.dropna(subset=["Adı Soyadı", "Tarihi"])
            df["Tarihi"] = pd.to_datetime(df["Tarihi"], errors='coerce')
            df = df.dropna(subset=["Tarihi"])
            
            # Ay Seçimi
            aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                     "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            secilen_ay_adi = st.selectbox("Rapor İstediğiniz Ayı Seçin:", aylar)
            secilen_ay_no = aylar.index(secilen_ay_adi) + 1
            
            # Filtreleme
            filtreli_df = df[
                (df["Türü"] != "N") & 
                (df["Türü"] != "F") & 
                (df.Tarihi.dt.month == secilen_ay_no)
            ]
            
            # Özet Tablo
            ozet_tablo = filtreli_df.groupby("Adı Soyadı")["Gün Sayısı"].sum().reset_index()
            ozet_tablo = ozet_tablo.sort_values(by="Adı Soyadı")
            
            st.subheader(f"📅 {secilen_ay_adi} Ayı Raporu")
            if not ozet_tablo.empty:
                st.dataframe(ozet_tablo, use_container_width=True)
                
                # İndirme Butonu
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    ozet_tablo.to_excel(writer, index=False, sheet_name='Rapor')
                
                st.download_button(
                    label="📄 Excel Olarak İndir",
                    data=output.getvalue(),
                    file_name=f"Rapor_{secilen_ay_adi}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Bu ayda kriterlere uygun kayıt bulunamadı.")
        except Exception as e:
            st.error("Veriler işlenirken bir sorun oluştu.")
            st.write(f"Hata detayı: {e}")
