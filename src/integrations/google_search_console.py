"""Google Search Console entegrasyonu"""
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from src.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    REDIRECT_URI,
    SCOPES
)


def get_flow():
    """OAuth flow nesnesini oluştur"""
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


def get_credentials():
    """Session state'ten credentials al"""
    if 'credentials' in st.session_state:
        creds_dict = st.session_state['credentials']
        return Credentials.from_authorized_user_info(creds_dict)
    return None


def save_credentials(credentials):
    """Credentials'ı session state'e kaydet"""
    st.session_state['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }


def get_search_console_service(credentials):
    """Search Console API servisini oluştur"""
    return build('searchconsole', 'v1', credentials=credentials)


def list_sites(service):
    """Kullanıcının Search Console'daki sitelerini listele"""
    try:
        sites = service.sites().list().execute()
        return sites.get('siteEntry', [])
    except HttpError as error:
        st.error(f"Bir hata oluştu: {error}")
        return []


def get_search_analytics(service, site_url, start_date, end_date, row_limit=25000):
    """Search Console'dan analitik verileri çek - Tüm sayfaları çeker"""
    all_rows = []
    start_row = 0
    max_rows_per_page = 25000  # Google API maksimum limiti
    
    try:
        while True:
            # Her sayfada maksimum 25,000 satır çek
            if row_limit:
                current_limit = min(max_rows_per_page, row_limit - len(all_rows))
            else:
                current_limit = max_rows_per_page
            
            request = {
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'dimensions': ['query', 'page'],
                'rowLimit': current_limit,
                'startRow': start_row
            }
            
            response = service.searchanalytics().query(
                siteUrl=site_url,
                body=request
            ).execute()
            
            rows = response.get('rows', [])
            
            if not rows:
                break
            
            all_rows.extend(rows)
            
            if len(rows) < request['rowLimit']:
                break
            
            if row_limit and len(all_rows) >= row_limit:
                break
            
            start_row += len(rows)
            
            if start_row >= 2500000:
                break
        
        return all_rows
    except HttpError as error:
        st.error(f"Veri çekilirken hata oluştu: {error}")
        return all_rows
    except Exception as error:
        st.error(f"Beklenmeyen hata: {error}")
        return all_rows
