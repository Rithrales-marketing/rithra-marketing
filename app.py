"""Marketing SaaS Dashboard - Ana Uygulama"""
import streamlit as st
from streamlit_option_menu import option_menu

# Modüllerden import
from src.auth import check_authentication, logout, render_login_page
from src.pages import (
    render_dashboard,
    render_seo_search_console,
    render_google_ads,
    render_meta_ads,
    render_settings
)

# Sayfa yapılandırması
st.set_page_config(
    page_title="Marketing SaaS Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Modern tema ve mobil uyumluluk
st.markdown("""
<style>
    /* Genel Stil */
    .main {
        padding: 1rem 2rem;
    }
    
    /* Sidebar Stil - Modern Mavi Tasarım */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 0 !important;
    }
    
    /* Sidebar içindeki tüm metinleri beyaz yap */
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Sidebar container padding */
    [data-testid="stSidebar"] > div:first-child {
        padding: 1.5rem 1rem !important;
    }
    
    /* Modern menü öğeleri - Yuvarlatılmış, temiz tasarım */
    .sidebar-menu-item {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        color: white !important;
        background-color: transparent;
        font-size: 0.95rem;
        font-weight: 500;
    }
    
    .sidebar-menu-item:hover {
        background-color: rgba(255, 255, 255, 0.15);
    }
    
    .sidebar-menu-item.active {
        background-color: rgba(255, 255, 255, 0.25);
        font-weight: 600;
    }
    
    .sidebar-menu-item-icon {
        margin-right: 0.75rem;
        font-size: 1.1rem;
        width: 20px;
        text-align: center;
    }
    
    /* Collection öğeleri - Renkli noktalarla */
    .collection-item {
        display: flex;
        align-items: center;
        padding: 0.6rem 1rem;
        margin: 0.2rem 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 0.9rem;
    }
    
    .collection-item:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    .collection-dot {
        width: 8px;
        height: 8px;
        border-radius: 2px;
        margin-right: 0.75rem;
    }
    
    /* Bölüm başlıkları */
    .sidebar-section-title {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: rgba(255, 255, 255, 0.6) !important;
        margin: 1.5rem 0 0.5rem 0;
        padding: 0 1rem;
    }
    
    /* Divider */
    .sidebar-divider {
        height: 1px;
        background: rgba(255, 255, 255, 0.15);
        margin: 1rem 0;
        border: none;
    }
    
    /* Sidebar başlıkları */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6 {
        color: white !important;
    }
    
    /* Sidebar paragrafları ve span'ler */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {
        color: white !important;
    }
    
    /* Sidebar divider (hr) çizgisi */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.3) !important;
        margin: 1rem 0 !important;
    }
    
    /* Sidebar butonları - Modern tasarım */
    [data-testid="stSidebar"] .stButton > button {
        color: white !important;
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        text-align: left !important;
        font-weight: 500 !important;
        margin: 0.25rem 0 !important;
        transition: all 0.2s ease !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.15) !important;
    }
    
    /* Aktif buton stili */
    [data-testid="stSidebar"] .stButton > button[kind=""]:focus {
        background: rgba(255, 255, 255, 0.25) !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar input alanları */
    [data-testid="stSidebar"] .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    
    [data-testid="stSidebar"] .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.6) !important;
    }
    
    /* Sidebar selectbox */
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }
    
    /* Sidebar checkbox ve radio */
    [data-testid="stSidebar"] .stCheckbox > label,
    [data-testid="stSidebar"] .stRadio > label {
        color: white !important;
    }
    
    /* Sidebar markdown içeriği */
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    
    /* Option Menu - Menü öğeleri için özel stiller */
    [data-testid="stSidebar"] .css-1lcbmhc,
    [data-testid="stSidebar"] .css-1lcbmhc a,
    [data-testid="stSidebar"] .css-1lcbmhc span {
        color: white !important;
    }
    
    /* Option Menu linkleri - Mavi arka plan ve çerçeve */
    [data-testid="stSidebar"] .css-1lcbmhc .nav-link,
    [data-testid="stSidebar"] .css-1lcbmhc a {
        background-color: rgba(30, 58, 138, 0.6) !important;
        color: white !important;
        border: 2px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 10px !important;
        margin: 8px 0 !important;
        padding: 12px 15px !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stSidebar"] .css-1lcbmhc .nav-link:hover,
    [data-testid="stSidebar"] .css-1lcbmhc a:hover {
        background-color: rgba(59, 130, 246, 0.8) !important;
        color: white !important;
        border-color: rgba(255, 255, 255, 0.6) !important;
        transform: translateX(5px) !important;
    }
    
    [data-testid="stSidebar"] .css-1lcbmhc .nav-link-selected,
    [data-testid="stSidebar"] .css-1lcbmhc a[aria-selected="true"],
    [data-testid="stSidebar"] [aria-selected="true"] {
        color: white !important;
        border: 2px solid rgba(255, 255, 255, 0.8) !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Option Menu ikonları */
    [data-testid="stSidebar"] .css-1lcbmhc i,
    [data-testid="stSidebar"] .css-1lcbmhc svg {
        color: white !important;
        fill: white !important;
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        padding-top: 2rem;
    }
    
    /* Buton Stilleri - Mobil Uyumlu ve Renkli */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        cursor: pointer;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    
    /* SEO Sayfası Butonları - Yeşil */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
    }
    
    /* Secondary Butonlar */
    .stButton > button[kind="secondary"] {
        background: #6b7280;
        color: white;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #4b5563;
    }
    
    /* Metric Kartları */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #6b7280;
    }
    
    /* Metric Kartları - Renkli Border */
    [data-testid="stMetricContainer"] {
        padding: 1rem;
        border-radius: 12px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
    }
    
    /* Tablo Stilleri */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Input Alanları */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Radio Button Stilleri */
    .stRadio > div {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .stRadio > div > label {
        padding: 0.5rem 1rem;
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .stRadio > div > label:hover {
        border-color: #3b82f6;
        background-color: #eff6ff;
    }
    
    /* Selectbox Stilleri */
    .stSelectbox > div > div {
        border-radius: 8px;
    }
    
    /* Date Input Stilleri */
    .stDateInput > div > div > input {
        border-radius: 8px;
    }
    
    /* Mobil Uyumluluk */
    @media (max-width: 768px) {
        .main {
            padding: 0.5rem 1rem;
        }
        
        [data-testid="stSidebar"] {
            min-width: 200px;
            max-width: 250px;
        }
        
        .stButton > button {
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
        
        h1 {
            font-size: 1.5rem;
        }
        
        h2 {
            font-size: 1.3rem;
        }
        
        h3 {
            font-size: 1.1rem;
        }
    }
    
    /* Başlık Stilleri */
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    h2 {
        color: #3b82f6;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    
    h3 {
        color: #60a5fa;
        font-weight: 600;
    }
    
    /* Success/Error/Info Mesajları */
    .stSuccess {
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stError {
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stInfo {
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Scrollbar Stil */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Ana uygulama fonksiyonu"""
    # Authentication kontrolü
    if not check_authentication():
        render_login_page()
        return
    
    # Giriş yapılmışsa ana uygulamayı göster
    # Sidebar menü - Modern tasarım (görseldeki gibi)
    with st.sidebar:
        # Üst bölüm - Kullanıcı adı ve logo
        username = st.session_state.get('username', 'User')
        st.markdown(f"""
        <div style="padding: 1rem 1rem 0.5rem 1rem; display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 1.2rem; font-weight: 600; color: white;">{username}'s</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # New Chat butonu (opsiyonel - gelecekte eklenebilir)
        # st.markdown("""
        # <div style="padding: 0.5rem 1rem; display: flex; align-items: center; cursor: pointer; border-radius: 8px; margin: 0.5rem 0;">
        #     <span style="margin-right: 0.5rem;">➕</span>
        #     <span style="color: white;">New chat</span>
        # </div>
        # """, unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # Ana navigasyon menüsü
        menu_items = [
            ("Genel Bakış", "🏠"),
            ("SEO", "🔍"),
            ("Google Ads", "💰"),
            ("Meta Ads", "📱"),
        ]
        
        # Session state'te seçili menüyü sakla
        if 'selected_menu' not in st.session_state:
            st.session_state['selected_menu'] = "Genel Bakış"
        
        # Aktif menü için CSS ekle
        active_menu = st.session_state.get('selected_menu', 'Genel Bakış')
        menu_key_map = {
            'Genel Bakış': 'menu_Genel Bakış',
            'SEO': 'menu_SEO',
            'Google Ads': 'menu_Google Ads',
            'Meta Ads': 'menu_Meta Ads',
            'Ayarlar': 'menu_Ayarlar'
        }
        active_key = menu_key_map.get(active_menu, 'menu_Genel Bakış')
        st.markdown(f"""
        <style>
        button[data-testid*="baseButton-{active_key}"] {{
            background-color: rgba(255, 255, 255, 0.25) !important;
            font-weight: 600 !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # Menü öğelerini göster - Butonlar ile
        for item_name, icon in menu_items:
            if st.button(f"{icon} {item_name}", key=f"menu_{item_name}", use_container_width=True):
                st.session_state['selected_menu'] = item_name
                st.rerun()
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # Alt kısım - Settings
        is_settings_active = st.session_state['selected_menu'] == "Ayarlar"
        if st.button("⚙️ Ayarlar", key="menu_Ayarlar", use_container_width=True):
            st.session_state['selected_menu'] = "Ayarlar"
            st.rerun()
        
        # Seçili menüyü kontrol et ve sayfayı render et
        selected = st.session_state.get('selected_menu', 'Genel Bakış')
    
    # Sayfa yönlendirme
    if selected == "Genel Bakış":
        render_dashboard()
    elif selected == "SEO":
        render_seo_search_console()
    elif selected == "Google Ads":
        render_google_ads()
    elif selected == "Meta Ads":
        render_meta_ads()
    elif selected == "Ayarlar":
        render_settings()


if __name__ == "__main__":
    main()
