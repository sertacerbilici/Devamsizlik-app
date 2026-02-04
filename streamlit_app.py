import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Devamsızlık Takip Sistemi", layout="centered")

st.title("📊 Devamsızlık Takip Uygulaması")
st.write("MEB'den aldığınız Excel (.xlsx veya .xls) dosyasını yükleyin ve raporunuzu anında alın.")

# 1. Dosya Yükleme Alanı
uploaded_file = st.file_uploader("Excel dosyasını buraya sürükleyin", type=["xlsx", "xls"])

if uploaded_file:
    # Dosya uzantısına göre motoru belirle
    file_ext = uploaded_file.name.split(".")[-1]
    engine = "xlrd" if file_ext == "xls" else "openpyxl"
    
    try:
        # Excel'i oku (Seçilen motorla)
        df = pd.read_excel(uploaded_file, header=7, engine=engine)
        
        # Sütun isimlerini belirle (E, J, L, N koordinatları)
        df = df.iloc[:, [4, 9, 11, 13]]
        df.columns = ["Adı Soyadı", "Tarihi", "Türü", "Gün Sayısı"]
        
        # Boş satırları temizle
        df = df.dropna(subset=["Adı Soyadı", "Tarihi"])
        
        # Tarih formatını düzelt
        df["Tarihi"] = pd.to_datetime(df["Tarihi"], errors='coerce')
        df = df.dropna(subset=["Tarihi"])
        
        # 2. Ay Seçimi
        aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        secilen_ay_adi = st.selectbox("Lütfen Rapor İstediğiniz Ayı Seçin:", aylar)
        secilen_ay_no = aylar.index(secilen_ay_adi) + 1
        
        # 3. Filtreleme Mantığı (N ve F'yi ele, Ayı süz)
        filtreli_df = df[
            (df["Türü"] != "N") & 
            (df["Türü"] != "F") & 
            (df.Tarihi.dt.month == secilen_ay_no)
        ]
        
        # 4. Gruplama ve Alfabetik Sıralama
        ozet_tablo = filtreli_df.groupby("Adı Soyadı")["Gün Sayısı"].sum().reset_index()
        ozet_tablo = ozet_tablo.sort_values(by="Adı Soyadı")
        
        # 5. Sonuçları Göster
        st.subheader(f"📅 {secilen_ay_adi} Ayı Devamsızlık Raporu")
        if not ozet_tablo.empty:
            st.dataframe(ozet_tablo, use_container_width=True)
            
            # Excel olarak indirme butonu
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                ozet_tablo.to_excel(writer, index=False, sheet_name='Rapor')
            
            st.download_button(
                label="📄 Raporu Excel Olarak İndir",
                data=output.getvalue(),
                file_name=f"Devamsizlik_Raporu_{secilen_ay_adi}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Seçilen ayda kriterlere uygun devamsızlık kaydı bulunamadı.")
            
    except Exception as e:
        st.error(f"Dosya okunurken bir hata oluştu. Lütfen dosyanın formatını kontrol edin.")
        st.info(f"Hata detayı: {e}")
