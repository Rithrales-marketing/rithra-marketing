"""Google Ads sayfası"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from src.config import (
    GOOGLE_ADS_DEVELOPER_TOKEN,
    GOOGLE_ADS_CUSTOMER_ID,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    REDIRECT_URI,
    SCOPES
)
from src.integrations.google_ads import (
    get_google_ads_client,
    get_google_ads_credentials,
    save_google_ads_credentials,
    get_campaigns_data
)


def get_google_ads_flow():
    """Google Ads için OAuth flow nesnesini oluştur"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow


def render_google_ads():
    """Google Ads sayfası"""
    st.title("💰 Google Ads")
    st.markdown("---")
    
    # Google Ads sayfası için özel turuncu buton stili
    st.markdown("""
    <style>
    /* Google Ads sayfası butonları için turuncu renk */
    h1:contains("Google Ads") ~ * button[kind="primary"],
    button[key*="google_ads"] {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        color: white !important;
    }
    button[key*="google_ads"]:hover {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.info("Google Ads hesabınıza bağlanın ve kampanya performansınızı analiz edin.")
    
    # Credentials kontrolü
    credentials = get_google_ads_credentials()
    
    # URL parametrelerinden authorization code'u kontrol et
    query_params = st.query_params
    if 'code' in query_params and credentials is None:
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [REDIRECT_URI]
                    }
                },
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            
            authorization_code = query_params['code']
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            save_google_ads_credentials(credentials)
            st.session_state['google_ads_connected'] = True
            st.rerun()
        except Exception as e:
            st.error(f"Yetkilendirme hatası: {e}")
            error_msg = str(e)
            if "redirect_uri_mismatch" in error_msg.lower():
                st.error("❌ Redirect URI uyumsuzluğu!")
                st.warning(f"Kullanılan Redirect URI: {REDIRECT_URI}")
                st.info("""
                **Çözüm:**
                1. Google Cloud Console'da OAuth 2.0 Client ID'nizi kontrol edin
                2. "Authorized redirect URIs" bölümüne şu URL'yi ekleyin:
                   https://rithra-marketing-46gzjurpv5ql9uappjajb6x.streamlit.app/
                3. Değişikliklerin kaydedildiğinden emin olun
                4. Birkaç dakika bekleyin (değişikliklerin yayılması için)
                """)
            else:
                st.error(f"Detay: {error_msg}")
    
    if credentials is None:
        st.warning("Google Ads hesabınıza henüz bağlanmadınız.")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("**Gerekli Bilgiler:**")
            st.write("- GOOGLE_ADS_DEVELOPER_TOKEN")
            st.write("- GOOGLE_ADS_CUSTOMER_ID")
            st.write("- Google OAuth Credentials")
            st.write("")
            st.info("""
            **Not:** Google Ads API'yi kullanmak için:
            1. Google Ads hesabınızda Developer Token alın
            2. Customer ID'nizi belirleyin
            3. OAuth 2.0 ile yetkilendirme yapın
            """)
        
        with col2:
            if GOOGLE_ADS_DEVELOPER_TOKEN and GOOGLE_ADS_CUSTOMER_ID:
                st.success("✅ API Bilgileri Mevcut")
                st.info(f"**Customer ID:** {GOOGLE_ADS_CUSTOMER_ID}")
            else:
                st.error("❌ API Bilgileri Eksik")
                st.info("Lütfen .env dosyasını kontrol edin.")
        
        if st.button("🔗 Google Ads'e Bağlan", type="primary", use_container_width=True, key="google_ads_connect_btn"):
            if GOOGLE_ADS_DEVELOPER_TOKEN and GOOGLE_ADS_CUSTOMER_ID:
                try:
                    flow = get_google_ads_flow()
                    authorization_url, _ = flow.authorization_url(
                        access_type='offline',
                        include_granted_scopes='true',
                        prompt='consent'
                    )
                    st.markdown(f"[Google Ads'e yönlendirmek için tıklayın]({authorization_url})")
                    st.info("Yukarıdaki bağlantıya tıklayarak Google hesabınızla giriş yapın.")
                except Exception as e:
                    st.error(f"OAuth akışı başlatılamadı: {e}")
                    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
                        st.warning("⚠️ Lütfen .env dosyasında GOOGLE_CLIENT_ID ve GOOGLE_CLIENT_SECRET değerlerini kontrol edin.")
            else:
                st.error("Lütfen önce .env dosyasında gerekli bilgileri ekleyin.")
    else:
        st.success("✅ Google Ads hesabınıza başarıyla bağlandınız!")
        
        if st.button("🔌 Bağlantıyı Kes", type="secondary"):
            if 'google_ads_credentials' in st.session_state:
                del st.session_state['google_ads_credentials']
            if 'google_ads_connected' in st.session_state:
                del st.session_state['google_ads_connected']
            st.rerun()
        
        st.markdown("---")
        
        try:
            # Token'ı yenile
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                save_google_ads_credentials(credentials)
            
            # Google Ads client'ı oluştur
            client = get_google_ads_client()
            
            if client and GOOGLE_ADS_CUSTOMER_ID:
                st.subheader("📊 Kampanya Performansı")
                
                # Tarih aralığı seçimi
                col1, col2 = st.columns(2)
                with col1:
                    default_end = datetime.now().date()
                    default_start = default_end - timedelta(days=30)
                    start_date = st.date_input(
                        "Başlangıç Tarihi",
                        value=default_start,
                        max_value=datetime.now().date(),
                        key='google_ads_start_date'
                    )
                
                with col2:
                    end_date = st.date_input(
                        "Bitiş Tarihi",
                        value=default_end,
                        max_value=datetime.now().date(),
                        key='google_ads_end_date'
                    )
                
                if start_date > end_date:
                    st.error("⚠️ Başlangıç tarihi bitiş tarihinden sonra olamaz!")
                else:
                    if st.button("📊 Verileri Getir", type="primary", use_container_width=True, key="google_ads_fetch_btn"):
                        with st.spinner("Kampanya verileri çekiliyor, lütfen bekleyin..."):
                            campaigns_data = get_campaigns_data(
                                client,
                                GOOGLE_ADS_CUSTOMER_ID,
                                start_date,
                                end_date
                            )
                            
                            if campaigns_data:
                                df = pd.DataFrame(campaigns_data)
                                
                                # Toplamları hesapla
                                total_spend = df['Maliyet ($)'].sum()
                                total_impressions = df['Gösterim'].sum()
                                total_clicks = df['Tıklama'].sum()
                                total_conversions = df['Dönüşüm'].sum()
                                # CTR zaten yüzde olarak hesaplanmış
                                avg_ctr = df['CTR'].mean() if len(df) > 0 else 0
                                avg_cpc = df['Ortalama CPC ($)'].mean() if len(df) > 0 else 0
                                
                                # Tabloyu göster
                                st.markdown("### 📋 Kampanya Performansı")
                                st.dataframe(
                                    df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        'Kampanya ID': st.column_config.NumberColumn('Kampanya ID', format='%d'),
                                        'Kampanya Adı': st.column_config.TextColumn('Kampanya Adı', width='large'),
                                        'Durum': st.column_config.TextColumn('Durum', width='small'),
                                        'Gösterim': st.column_config.NumberColumn('Gösterim', format='%d'),
                                        'Tıklama': st.column_config.NumberColumn('Tıklama', format='%d'),
                                        'Maliyet ($)': st.column_config.NumberColumn('Maliyet ($)', format='$%.2f'),
                                        'Dönüşüm': st.column_config.NumberColumn('Dönüşüm', format='%d'),
                                        'CTR': st.column_config.NumberColumn('CTR', format='%.2f%%'),
                                        'Ortalama CPC ($)': st.column_config.NumberColumn('Ortalama CPC ($)', format='$%.2f'),
                                        'Dönüşüm Başına Maliyet ($)': st.column_config.NumberColumn('Dönüşüm Başına Maliyet ($)', format='$%.2f')
                                    }
                                )
                                
                                # Genel özet metrikleri
                                st.markdown("### 📈 Genel Özet İstatistikler")
                                col1, col2, col3, col4, col5, col6 = st.columns(6)
                                
                                with col1:
                                    st.metric("Toplam Harcama", f"${total_spend:,.2f}")
                                
                                with col2:
                                    st.metric("Toplam Gösterim", f"{total_impressions:,}")
                                
                                with col3:
                                    st.metric("Toplam Tıklama", f"{total_clicks:,}")
                                
                                with col4:
                                    st.metric("Toplam Dönüşüm", f"{total_conversions:,}")
                                
                                with col5:
                                    # CTR zaten yüzde olarak hesaplanmış
                                    st.metric("Ortalama CTR", f"{avg_ctr:.2f}%")
                                
                                with col6:
                                    st.metric("Ortalama CPC", f"${avg_cpc:.2f}")
                                
                                # Session state'e kaydet (dashboard için)
                                st.session_state['google_ads_total_spend'] = total_spend
                                st.session_state['google_ads_data'] = df
                                
                                st.success(f"✅ {len(df)} kampanya verisi başarıyla yüklendi!")
                            else:
                                st.warning("⚠️ Seçilen tarih aralığında kampanya verisi bulunamadı.")
            else:
                st.error("❌ Google Ads client oluşturulamadı. Lütfen API bilgilerini kontrol edin.")
                
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
            if "invalid_grant" in str(e).lower() or "token" in str(e).lower():
                st.info("Token süresi dolmuş olabilir. Lütfen tekrar bağlanın.")
                if 'google_ads_credentials' in st.session_state:
                    del st.session_state['google_ads_credentials']
                st.rerun()
