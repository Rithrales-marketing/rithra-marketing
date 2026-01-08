"""Google Ads sayfası"""
import streamlit as st
from src.config import GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CUSTOMER_ID


def render_google_ads():
    """Google Ads sayfası"""
    st.title("💰 Google Ads")
    st.markdown("---")
    
    st.info("Google Ads hesabınıza bağlanın ve kampanya performansınızı analiz edin.")
    
    # Google Ads bağlantı durumu kontrolü
    if 'google_ads_connected' not in st.session_state:
        st.session_state['google_ads_connected'] = False
    
    if not st.session_state['google_ads_connected']:
        st.warning("Google Ads hesabınıza henüz bağlanmadınız.")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("**Gerekli Bilgiler:**")
            st.write("- GOOGLE_ADS_DEVELOPER_TOKEN")
            st.write("- GOOGLE_ADS_CUSTOMER_ID")
            st.write("- Google OAuth Credentials")
        
        with col2:
            if GOOGLE_ADS_DEVELOPER_TOKEN and GOOGLE_ADS_CUSTOMER_ID:
                st.success("✅ API Bilgileri Mevcut")
            else:
                st.error("❌ API Bilgileri Eksik")
                st.info("Lütfen .env dosyasını kontrol edin.")
        
        if st.button("🔗 Google Ads'e Bağlan", type="primary", use_container_width=True, key="google_ads_connect_btn"):
            if GOOGLE_ADS_DEVELOPER_TOKEN and GOOGLE_ADS_CUSTOMER_ID:
                try:
                    # TODO: Google Ads OAuth akışı
                    st.info("Google Ads bağlantı akışı yakında eklenecek.")
                    # st.session_state['google_ads_connected'] = True
                except Exception as e:
                    st.error(f"Bağlantı hatası: {e}")
            else:
                st.error("Lütfen önce .env dosyasında gerekli bilgileri ekleyin.")
    else:
        st.success("✅ Google Ads hesabınıza bağlısınız!")
        
        if st.button("🔌 Bağlantıyı Kes", type="secondary"):
            st.session_state['google_ads_connected'] = False
            st.rerun()
        
        st.markdown("---")
        st.subheader("📊 Kampanya Performansı")
        st.info("Kampanya analizleri burada görüntülenecek.")
