import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Devamsızlık Takip Sistemi", layout="wide")

st.title("📊 Devamsızlık Takip Uygulaması")
st.info("MEB'den aldığınız dosyayı yükleyin. Uygulama otomatik olarak uygun sütunları bulmaya çalışacaktır.")

uploaded_file = st.file_uploader("Excel dosyasını buraya sürükleyin (.xlsx veya .xls)", type=["xlsx", "xls"])

if uploaded_file:
    df = None
    
    # 1. ADIM: DOSYAYI OKUMA (HER TÜRLÜ FORMATI DENER)
    try:
        # Önce standart modern excel dene
        df = pd.read_excel(uploaded_file)
    except:
        try:
            # Olmazsa eski tip excel dene
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, engine='xlrd')
        except:
            try:
                # O da olmazsa (MEB dosyaları bazen aslında HTML'dir)
                uploaded_file.seek(0)
                df = pd.read_html(uploaded_file)[0]
            except Exception as e:
                st.error(f"Dosya okunamadı. Lütfen dosyayı Excel'de açıp 'Farklı Kaydet' diyerek '.xlsx' formatında kaydedip tekrar yükleyin.")
                st.stop()

    if df is not None:
        # 2. ADIM: BAŞLIK SATIRINI BULMA
        # MEB dosyalarında üstte çok boşluk olabilir, "Adı Soyadı" yazan satırı arayalım
        header_row_index = 0
        found = False
        for i, row in df.head(20).iterrows():
            if row.astype(str).str.contains("Adı Soyadı", na=False).any():
                header_row_index = i
                found = True
                break
        
        # Eğer başlık bulunduysa tabloyu oradan itibaren başlat
        if found:
            df.columns = df.iloc[header_row_index]
            df = df.iloc[header_row_index + 1:].reset_index(drop=True)
        
        # 3. ADIM: SÜTUNLARI TESPİT ETME (Kullanıcının koordinatları veya isimle arama)
        try:
            # Sütun isimlerini temizle
            df.columns = [str(c).strip() for c in df.columns]
            
            # Koordinatlara göre çek (Sizin verdiğiniz E, J, L, N yapısı)
            # Eğer başlıklar bulunamadıysa iloc ile devam et
            if not found:
                 raw_df = df.iloc[:, [4, 9, 11, 13]]
                 raw_df.columns = ["Adı Soyadı", "Tarihi", "Türü", "Gün Sayısı"]
            else:
                # Başlığa göre bulmaya çalış, bulamazsa koordinat kullan
                cols = {}
                col_map = {"Adı Soyadı": "Adı Soyadı", "Tarih": "Tarihi", "Tür": "Türü", "Gün": "Gün Sayısı"}
                for target, new_name in col_map.items():
                    matches = [c for c in df.columns if target in c]
                    if matches: cols[new_name] = matches[0]
                
                if len(cols) >= 3:
                    raw_df = df[list(cols.values())].copy()
                    raw_df.columns = list(cols.keys())
                else:
                    raw_df = df.iloc[:, [4, 9, 11, 13]]
                    raw_df.columns = ["Adı Soyadı", "Tarihi", "Türü", "Gün Sayısı"]

            # 4. ADIM: TARİH VE TEMİZLİK
            # Tarihleri Türkiye formatında (gün önce) okumaya zorla
            raw_df["Tarihi"] = pd.to_datetime(raw_df["Tarihi"], dayfirst=True, errors='coerce')
            
            # Türü temizle (N ve F'yi elemek için)
            raw_df["Türü"] = raw_df["Türü"].astype(str).str.strip().str.upper()
            
            # Ay Seçimi
            aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                     "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            secilen_ay_adi = st.selectbox("Rapor İstediğiniz Ayı Seçin:", aylar)
            secilen_ay_no = aylar.index(secilen_ay_adi) + 1
            
            # FİLTRELEME
            mask = (
                (raw_df["Türü"] != "N") & 
                (raw_df["Türü"] != "F") & 
                (raw_df["Tarihi"].dt.month == secilen_ay_no)
            )
            sonuc_df = raw_df[mask].copy()
            
            # ÖZET VE SIRALAMA
            if not sonuc_df.empty:
                ozet = sonuc_df.groupby("Adı Soyadı")["Gün Sayısı"].sum().reset_index()
                ozet = ozet.sort_values("Adı Soyadı")
                
                st.success(f"{secilen_ay_adi} Ayı İçin {len(ozet)} Kayıt Bulundu.")
                st.dataframe(ozet, use_container_width=True)
                
                # İndirme Butonu
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    ozet.to_excel(writer, index=False)
                
                st.download_button("📥 Raporu Excel Olarak İndir", output.getvalue(), f"Rapor_{secilen_ay_adi}.xlsx")
            else:
                st.warning(f"{secilen_ay_adi} ayında 'N' veya 'F' harici bir devamsızlık bulunamadı.")
                # Hata ayıklama için yüklenen veriden örnek göster (Gizli)
                with st.expander("Yüklenen Veriden Örnek (Hata Ayıklama)"):
                    st.write(raw_df.head(10))

        except Exception as e:
            st.error(f"Veri işleme hatası: {e}")
