"""Ayarlar sayfası"""
import streamlit as st
from src.integrations.google_search_console import get_credentials
from src.config import (
    GOOGLE_ADS_DEVELOPER_TOKEN,
    GOOGLE_ADS_CUSTOMER_ID,
    META_APP_ID,
    META_APP_SECRET
)


def render_settings():
    """Ayarlar sayfası"""
    st.title("⚙️ Ayarlar")
    st.markdown("---")
    
    st.subheader("🔑 API Anahtarları ve Bağlantı Durumu")
    
    # Google Search Console durumu
    st.markdown("### 🔍 Google Search Console")
    credentials = get_credentials()
    if credentials:
        st.success("✅ Bağlı")
        if st.button("🔌 Bağlantıyı Kes (Search Console)", type="secondary"):
            if 'credentials' in st.session_state:
                del st.session_state['credentials']
            st.rerun()
    else:
        st.warning("❌ Bağlı Değil")
    
    st.markdown("---")
    
    # Google Ads durumu
    st.markdown("### 💰 Google Ads")
    if GOOGLE_ADS_DEVELOPER_TOKEN and GOOGLE_ADS_CUSTOMER_ID:
        st.success("✅ API Bilgileri Yapılandırılmış")
        st.info("Developer Token ve Customer ID .env dosyasından okunuyor.")
    else:
        st.error("❌ API Bilgileri Eksik")
        st.info("Lütfen .env dosyasına GOOGLE_ADS_DEVELOPER_TOKEN ve GOOGLE_ADS_CUSTOMER_ID ekleyin.")
    
    st.markdown("---")
    
    # Meta Ads durumu
    st.markdown("### 📱 Meta Ads")
    if META_APP_ID and META_APP_SECRET:
        st.success("✅ API Bilgileri Yapılandırılmış")
        st.info("Meta App ID ve App Secret .env dosyasından okunuyor.")
    else:
        st.warning("⚠️ API Bilgileri Eksik")
        st.info("Lütfen .env dosyasına META_APP_ID ve META_APP_SECRET ekleyin.")
    
    st.markdown("---")
    
    st.subheader("📝 Notlar")
    st.info("""
    - Tüm API anahtarları .env dosyasında saklanmaktadır.
    - Güvenlik için .env dosyasını asla git'e commit etmeyin.
    - API anahtarlarınızı düzenli olarak kontrol edin.
    """)
