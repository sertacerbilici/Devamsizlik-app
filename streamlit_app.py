import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Devamsızlık Takip Sistemi", layout="wide")

st.title("📊 Devamsızlık Takip Uygulaması (Gelişmiş Versiyon)")
st.info("MEB dosyasını yükleyin. Sistem, başlıkları otomatik olarak tarayıp bulacaktır.")

uploaded_file = st.file_uploader("Excel dosyasını seçin (.xlsx veya .xls)", type=["xlsx", "xls"])

if uploaded_file:
    df_raw = None
    
    # 1. DOSYAYI OKUMA (EN ESNEK YÖNTEM)
    try:
        # Önce dosyayı ham halde oku (başlık belirlemeden)
        df_raw = pd.read_excel(uploaded_file, header=None)
    except:
        try:
            uploaded_file.seek(0)
            df_raw = pd.read_excel(uploaded_file, header=None, engine='xlrd')
        except:
            st.error("Dosya okunamadı. Lütfen standart bir Excel dosyası yükleyin.")
            st.stop()

    if df_raw is not None:
        # 2. DOĞRU BAŞLIK SATIRINI VE SÜTUNLARI BULMA
        # Tabloyu tarayıp anahtar kelimeleri arıyoruz
        name_col, date_col, type_col, day_col = None, None, None, None
        header_idx = 0

        for i, row in df_raw.head(30).iterrows():
            row_str = row.astype(str).str.upper()
            if row_str.str.contains("ADI SOYADI").any() or row_str.str.contains("ÖĞRENCİ NO").any():
                header_idx = i
                # Sütunları isimlerine göre eşleştir
                for col_idx, value in enumerate(row):
                    val_upper = str(value).upper()
                    if "ADI SOYADI" in val_upper: name_col = col_idx
                    if "TARİH" in val_upper: date_col = col_idx
                    if "TÜR" in val_upper: type_col = col_idx
                    if "GÜN" in val_upper: day_col = col_idx
                break
        
        # Eğer otomatik bulamazsa senin verdiğin standart koordinatları kullan (E, J, L, N)
        if name_col is None: name_col = 4
        if date_col is None: date_col = 9
        if type_col is None: type_col = 11
        if day_col is None: day_col = 13

        # Veriyi temizle ve sütunları al
        try:
            df = df_raw.iloc[header_idx + 1:].copy()
            df = df.iloc[:, [name_col, date_col, type_col, day_col]]
            df.columns = ["Adı Soyadı", "Tarihi", "Türü", "Gün Sayısı"]
            
            # Boşlukları ve geçersiz satırları temizle
            df = df.dropna(subset=["Adı Soyadı"])
            df["Tarihi"] = pd.to_datetime(df["Tarihi"], errors='coerce', dayfirst=True)
            df = df.dropna(subset=["Tarihi"])
            
            # Ay Seçimi
            aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                     "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            secilen_ay_adi = st.selectbox("Hangi Ayın Raporunu İstiyorsunuz?", aylar)
            secilen_ay_no = aylar.index(secilen_ay_adi) + 1
            
            # Filtreleme (N ve F'yi ele, Ayı seç)
            df["Türü"] = df["Türü"].astype(str).str.strip().str.upper()
            mask = (df["Türü"] != "N") & (df["Türü"] != "F") & (df["Tarihi"].dt.month == secilen_ay_no)
            final_df = df[mask].copy()

            # Raporu Göster
            if not final_df.empty:
                ozet = final_df.groupby("Adı Soyadı")["Gün Sayısı"].sum().reset_index()
                ozet = ozet.sort_values("Adı Soyadı")
                
                st.success(f"✅ {secilen_ay_adi} ayı için sonuçlar hazır!")
                st.dataframe(ozet, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    ozet.to_excel(writer, index=False)
                st.download_button("📥 Excel Raporunu İndir", output.getvalue(), f"Rapor_{secilen_ay_adi}.xlsx")
            else:
                st.warning(f"Seçilen ayda ({secilen_ay_adi}) kriterlere uygun kayıt bulunamadı.")
                
                # Hata Ayıklama Yardımcısı (Sadece veri yoksa görünür)
                with st.expander("Uygulama ne görüyor? (Burayı kontrol edin)"):
                    st.write("Sizin dosyanızdaki sütunlar şunlar:")
                    st.write(df.head(10))
                    
        except Exception as e:
            st.error(f"Veri işleme hatası: {e}")
