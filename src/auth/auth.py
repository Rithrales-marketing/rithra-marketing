"""Authentication ve kullanıcı yönetimi"""
import streamlit as st
from src.config import USERS


def check_authentication():
    """Kullanıcının giriş yapıp yapmadığını kontrol et"""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
        st.session_state['username'] = None
    return st.session_state.get('authenticated', False)


def authenticate_user(username, password):
    """Kullanıcı adı ve şifreyi doğrula"""
    if username in USERS and USERS[username]['password'] == password:
        st.session_state['authenticated'] = True
        st.session_state['username'] = username
        return True
    return False


def logout():
    """Kullanıcıyı çıkış yaptır"""
    st.session_state['authenticated'] = False
    st.session_state['username'] = None
    # Tüm session state'i temizle (opsiyonel)
    for key in list(st.session_state.keys()):
        if key not in ['authenticated', 'username']:
            del st.session_state[key]


def render_login_page():
    """Login sayfasını render et"""
    # Login sayfası için özel CSS - Yeşil buton için güçlü override
    st.markdown("""
    <style>
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 2rem;
    }
    .login-box {
        max-width: 400px;
        width: 100%;
        padding: 2rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    /* Giriş butonu için yeşil stil - Çok güçlü override */
    div[data-testid="stForm"] button[type="submit"],
    div[data-testid="stForm"] button.kind-primary,
    div[data-testid="stForm"] .stButton > button,
    div[data-testid="stForm"] .stButton > button[kind="primary"],
    form button[type="submit"],
    button[type="submit"],
    button.kind-primary {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        background-color: #10b981 !important;
        background-image: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3) !important;
    }
    div[data-testid="stForm"] button[type="submit"]:hover,
    div[data-testid="stForm"] button.kind-primary:hover,
    div[data-testid="stForm"] .stButton > button:hover,
    div[data-testid="stForm"] .stButton > button[kind="primary"]:hover,
    form button[type="submit"]:hover,
    button[type="submit"]:hover,
    button.kind-primary:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        background-color: #059669 !important;
        background-image: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(16, 185, 129, 0.4) !important;
    }
    /* Tüm primary butonları yeşil yap - Login sayfasında */
    .stButton > button[kind="primary"],
    .stButton > button[type="submit"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        background-color: #10b981 !important;
        background-image: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[type="submit"]:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        background-color: #059669 !important;
        background-image: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Ana container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">📊 Marketing SaaS</h1>
            <p style="font-size: 1.2rem; color: #6b7280; margin-top: 0;">Spend Smarter</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Login formu
        with st.form("login_form"):
            st.subheader("Giriş Yap")
            
            username = st.text_input("Kullanıcı Adı", key="login_username", placeholder="Kullanıcı adınızı girin")
            password = st.text_input("Şifre", type="password", key="login_password", placeholder="Şifrenizi girin")
            
            login_button = st.form_submit_button("Giriş Yap", type="primary", use_container_width=True)
            
            # JavaScript ile butonu yeşil yap (inline style override)
            try:
                import streamlit.components.v1 as components
                components.html("""
                <script>
                setTimeout(function() {
                    var buttons = document.querySelectorAll('div[data-testid="stForm"] button[type="submit"], button[type="submit"], button.kind-primary');
                    buttons.forEach(function(button) {
                        button.style.setProperty('background', 'linear-gradient(135deg, #10b981 0%, #059669 100%)', 'important');
                        button.style.setProperty('background-color', '#10b981', 'important');
                        button.style.setProperty('color', 'white', 'important');
                        button.style.setProperty('border', 'none', 'important');
                        button.onmouseover = function() {
                            this.style.setProperty('background', 'linear-gradient(135deg, #059669 0%, #047857 100%)', 'important');
                            this.style.setProperty('background-color', '#059669', 'important');
                        };
                        button.onmouseout = function() {
                            this.style.setProperty('background', 'linear-gradient(135deg, #10b981 0%, #059669 100%)', 'important');
                            this.style.setProperty('background-color', '#10b981', 'important');
                        };
                    });
                }, 200);
                </script>
                """, height=0)
            except:
                pass
            
            if login_button:
                if username and password:
                    if authenticate_user(username, password):
                        st.success("✅ Giriş başarılı! Yönlendiriliyorsunuz...")
                        st.rerun()
                    else:
                        st.error("❌ Kullanıcı adı veya şifre hatalı!")
                else:
                    st.warning("⚠️ Lütfen kullanıcı adı ve şifrenizi girin.")
        
        # Test bilgileri (geliştirme için)
        with st.expander("ℹ️ Test Kullanıcı Bilgileri"):
            st.code("""
Kullanıcı Adı: admin
Şifre: admin
            """)
