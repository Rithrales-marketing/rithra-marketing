"""Konfigürasyon yönetimi modülü"""
import os
from dotenv import load_dotenv

# .env dosyasından değişkenleri yükle
load_dotenv()

# Google OAuth yapılandırması
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# Redirect URI - Streamlit Cloud URL'si veya Custom Domain
REDIRECT_URI = os.getenv('STREAMLIT_REDIRECT_URI', 'https://rithra-marketing-46gzjurpv5ql9uappjajb6x.streamlit.app/')

# Google Ads yapılandırması
GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')
GOOGLE_ADS_CUSTOMER_ID = os.getenv('GOOGLE_ADS_CUSTOMER_ID')

# Meta Ads yapılandırması
META_APP_ID = os.getenv('META_APP_ID')
META_APP_SECRET = os.getenv('META_APP_SECRET')

# OAuth 2.0 kapsamları
SCOPES = [
    'https://www.googleapis.com/auth/webmasters.readonly',  # Google Search Console
    'https://www.googleapis.com/auth/adwords'  # Google Ads
]

# Meta Ads hesap ID'leri
META_ACCOUNT_IDS = ['act_1301566494721561', 'act_924782866177345']

# Kullanıcı yönetimi - Test kullanıcıları
USERS = {
    'admin': {
        'password': 'admin',
        'name': 'Admin User'
    }
}
