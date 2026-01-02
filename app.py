import streamlit as st
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import pandas as pd
from streamlit_option_menu import option_menu
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.exceptions import FacebookRequestError

# .env dosyasından değişkenleri yükle
load_dotenv()

# Google OAuth yapılandırması
CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# Redirect URI'yi dinamik olarak belirle (Streamlit Cloud veya localhost)
# Streamlit Cloud URL'si (production için - hardcoded)
STREAMLIT_CLOUD_URL = 'https://rithra-marketing-46gzjurpv5ql9uappjajb6x.streamlit.app/'

def get_redirect_uri():
    """Mevcut sayfa URL'sine göre redirect URI belirle"""
    # Development modu kontrolü (sadece localhost için)
    # Eğer USE_LOCALHOST environment variable set edilmişse, localhost kullan
    use_localhost = os.getenv('USE_LOCALHOST', '').lower() == 'true'
    if use_localhost:
        return 'http://localhost:8501/'
    
    # Environment variable'dan Streamlit Cloud URL'sini al (Streamlit Cloud Secrets'da set edilebilir)
    streamlit_url = os.getenv('STREAMLIT_CLOUD_URL')
    if streamlit_url:
        return streamlit_url.rstrip('/') + '/'
    
    # Varsayılan: Her zaman Streamlit Cloud URL'si kullan (production)
    # Streamlit Cloud'da çalışıyorsa bu kullanılacak
    # NOT: Localhost'ta test etmek için USE_LOCALHOST=true set edin
    return STREAMLIT_CLOUD_URL

# Google Ads yapılandırması
GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')
GOOGLE_ADS_CUSTOMER_ID = os.getenv('GOOGLE_ADS_CUSTOMER_ID')

# Meta Ads yapılandırması
META_APP_ID = os.getenv('META_APP_ID')
META_APP_SECRET = os.getenv('META_APP_SECRET')

# OAuth 2.0 kapsamları
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

# Sayfa yapılandırması
st.set_page_config(
    page_title="Marketing SaaS Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== GOOGLE SEARCH CONSOLE FONKSİYONLARI ====================

def get_flow():
    """OAuth flow nesnesini oluştur"""
    # Runtime'da redirect URI'yi belirle (Streamlit Cloud için)
    redirect_uri = get_redirect_uri()
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri
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

def format_position(position):
    """Pozisyon değerine göre emoji ekle"""
    if position is None or pd.isna(position):
        return "N/A"
    
    pos = float(position)
    if 1 <= pos <= 3:
        return f"🟢 {pos:.1f}"
    elif 4 <= pos <= 10:
        return f"🟡 {pos:.1f}"
    else:
        return f"🔴 {pos:.1f}"

def format_ctr(ctr):
    """CTR değerini yüzde olarak formatla"""
    if ctr is None or pd.isna(ctr):
        return "0.00%"
    return f"{ctr * 100:.2f}%"

def get_date_range(period):
    """Seçilen periyoda göre tarih aralığını hesapla"""
    today = datetime.now().date()
    
    if period == "Son 7 Gün":
        start = today - timedelta(days=7)
        end = today
    elif period == "Son 14 Gün":
        start = today - timedelta(days=14)
        end = today
    elif period == "Son 30 Gün":
        start = today - timedelta(days=30)
        end = today
    elif period == "Bu Ay":
        start = today.replace(day=1)
        end = today
    elif period == "Geçen Ay":
        if today.month == 1:
            start = today.replace(year=today.year - 1, month=12, day=1)
        else:
            start = today.replace(month=today.month - 1, day=1)
        if today.month == 1:
            end = today.replace(year=today.year - 1, month=12, day=31)
        else:
            if today.month - 1 in [1, 3, 5, 7, 8, 10, 12]:
                end = today.replace(month=today.month - 1, day=31)
            elif today.month - 1 in [4, 6, 9, 11]:
                end = today.replace(month=today.month - 1, day=30)
            else:
                year = today.year
                if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                    end = today.replace(month=2, day=29)
                else:
                    end = today.replace(month=2, day=28)
    else:
        return None, None
    
    return start, end

# ==================== GOOGLE ADS FONKSİYONLARI ====================

def get_google_ads_client():
    """Google Ads API client'ı oluştur (iskelet)"""
    # TODO: Google Ads API entegrasyonu
    # from google.ads.googleads.client import GoogleAdsClient
    # client = GoogleAdsClient.load_from_dict({
    #     "developer_token": GOOGLE_ADS_DEVELOPER_TOKEN,
    #     "client_id": CLIENT_ID,
    #     "client_secret": CLIENT_SECRET,
    #     "refresh_token": "...",
    #     "use_proto_plus": True
    # })
    # return client
    return None

def get_google_ads_total_spend():
    """Google Ads toplam harcamasını getir"""
    # TODO: Google Ads API'den harcama verisi çek
    if 'google_ads_total_spend' in st.session_state:
        return st.session_state['google_ads_total_spend']
    return 0.0

# ==================== META ADS FONKSİYONLARI ====================

# Sabit hesap ID'leri
META_ACCOUNT_IDS = ['act_1301566494721561', 'act_924782866177345']

def get_meta_ads_insights_for_account(account_id, access_token, days=7):
    """Meta Ads hesabının son N günlük verilerini çek"""
    try:
        # FacebookAdsApi'yi başlat
        FacebookAdsApi.init(access_token=access_token)
        
        # Tarih aralığı hesapla
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # AdAccount nesnesini oluştur ve verileri çek
        account = AdAccount(account_id)
        insights = account.get_insights(
            fields=[
                AdsInsights.Field.spend,
                AdsInsights.Field.impressions,
                AdsInsights.Field.clicks,
                AdsInsights.Field.cpm,
                AdsInsights.Field.date_start,
                AdsInsights.Field.date_stop
            ],
            params={
                'time_range': {
                    'since': start_date.strftime('%Y-%m-%d'),
                    'until': end_date.strftime('%Y-%m-%d')
                },
                'level': 'account'
            }
        )
        
        return list(insights)
    except FacebookRequestError as e:
        # Hata mesajını çıkar
        error_msg = str(e)
        if hasattr(e, 'error_message'):
            error_msg = e.error_message
        elif hasattr(e, 'api_error_message'):
            error_msg = e.api_error_message
        elif hasattr(e, 'api_error'):
            if isinstance(e.api_error, dict) and 'message' in e.api_error:
                error_msg = e.api_error['message']
        return {'error': error_msg, 'account_id': account_id}
    except Exception as e:
        return {'error': str(e), 'account_id': account_id}

def get_all_meta_ads_data(access_token, days=7):
    """Tüm Meta Ads hesaplarının verilerini çek ve birleştir"""
    all_data = []
    errors = []
    
    for account_id in META_ACCOUNT_IDS:
        result = get_meta_ads_insights_for_account(account_id, access_token, days)
        
        if isinstance(result, dict) and 'error' in result:
            errors.append({
                'account_id': account_id,
                'error': result['error']
            })
        elif result:
            # Hesap ID'sini temizle (act_ prefix'i kaldır)
            clean_account_id = account_id.replace('act_', '')
            
            for insight in result:
                all_data.append({
                    'Hesap ID': clean_account_id,
                    'Hesap': account_id,
                    'Harcama ($)': float(insight.get('spend', 0)),
                    'Gösterim': int(insight.get('impressions', 0)),
                    'Tıklama': int(insight.get('clicks', 0)),
                    'CPM ($)': float(insight.get('cpm', 0)),
                    'Tarih Başlangıç': insight.get('date_start', 'N/A'),
                    'Tarih Bitiş': insight.get('date_stop', 'N/A')
                })
    
    return all_data, errors

def get_meta_ads_total_spend():
    """Meta Ads toplam harcamasını getir"""
    if 'meta_ads_total_spend' in st.session_state:
        return st.session_state['meta_ads_total_spend']
    return 0.0

def get_search_console_total_clicks():
    """Search Console toplam tıklamasını getir"""
    if 'analytics_data' in st.session_state and st.session_state.get('data_loaded', False):
        df = st.session_state['analytics_data']
        return int(df['Tıklama'].sum())
    return 0

# ==================== SAYFA FONKSİYONLARI ====================

def render_dashboard():
    """Genel Bakış sayfası"""
    st.title("🏠 Genel Bakış")
    st.markdown("---")
    
    st.info("📊 Tüm kanalların özeti burada görüntülenecek.")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Toplam Tıklama", "0", delta="0")
    
    with col2:
        st.metric("Toplam Gösterim", "0", delta="0")
    
    with col3:
        st.metric("Ortalama CTR", "0%", delta="0%")
    
    with col4:
        st.metric("Toplam Harcama", "$0", delta="$0")
    
    st.markdown("---")
    st.subheader("📈 Kanal Performansı")
    st.info("Kanal performans grafikleri burada görüntülenecek.")

def render_seo_search_console():
    """SEO - Search Console sayfası"""
    st.title("🔍 SEO - Search Console")
    st.markdown("---")

    # Credentials kontrolü
    credentials = get_credentials()

    # URL parametrelerinden authorization code'u kontrol et
    query_params = st.query_params
    if 'code' in query_params and credentials is None:
        try:
            # OAuth callback geldiğinde, redirect URI'yi tekrar belirle
            # Callback Streamlit Cloud'dan geliyorsa, Streamlit Cloud URL'si kullanılmalı
            redirect_uri = get_redirect_uri()
            
            # Flow'u callback için yeniden oluştur (doğru redirect URI ile)
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            
            authorization_code = query_params['code']
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            save_credentials(credentials)
            st.rerun()
        except Exception as e:
            st.error(f"Yetkilendirme hatası: {e}")
            st.error(f"Detay: {str(e)}")
            # Debug bilgisi
            st.info(f"🔍 Kullanılan Redirect URI: {get_redirect_uri()}")
            st.info(f"🔍 Query params: {dict(query_params)}")

    if credentials is None:
        st.info("Google Search Console'a bağlanmak için aşağıdaki butona tıklayın.")
        
        if st.button("🔗 Google ile Bağlan", type="primary", use_container_width=True):
            try:
                flow = get_flow()
                redirect_uri = get_redirect_uri()
                # Debug: Redirect URI'yi göster (geliştirme için)
                st.info(f"🔗 Redirect URI: {redirect_uri}")
                
                authorization_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='consent'
                )
                st.markdown(f"[Google'a yönlendirmek için tıklayın]({authorization_url})")
                st.info("Yukarıdaki bağlantıya tıklayarak Google hesabınızla giriş yapın.")
            except Exception as e:
                st.error(f"OAuth akışı başlatılamadı: {e}")
                if not CLIENT_ID or not CLIENT_SECRET:
                    st.warning("⚠️ Lütfen .env dosyasında GOOGLE_CLIENT_ID ve GOOGLE_CLIENT_SECRET değerlerini kontrol edin.")
    else:
        st.success("✅ Google hesabınıza başarıyla bağlandınız!")
        
        if st.button("🔌 Bağlantıyı Kes", type="secondary"):
            if 'credentials' in st.session_state:
                del st.session_state['credentials']
            st.rerun()

        st.markdown("---")
        
        try:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                save_credentials(credentials)

            service = get_search_console_service(credentials)
            sites = list_sites(service)

            if sites:
                st.subheader("📊 Search Console Analitikleri")
                
                # Siteleri session state'te sakla ve sıralamayı sabitle
                if 'sites_list' not in st.session_state:
                    site_urls = sorted([site.get('siteUrl', '') for site in sites])
                    st.session_state['sites_list'] = site_urls
                else:
                    site_urls = st.session_state['sites_list']
                
                current_sites = [site.get('siteUrl', '') for site in sites]
                for site_url in current_sites:
                    if site_url not in site_urls:
                        site_urls.append(site_url)
                        site_urls.sort()
                        st.session_state['sites_list'] = site_urls
                
                if 'selected_site' not in st.session_state:
                    st.session_state['selected_site'] = site_urls[0] if site_urls else None
                elif st.session_state.get('selected_site') not in site_urls:
                    st.session_state['selected_site'] = site_urls[0] if site_urls else None
                
                current_index = 0
                if st.session_state.get('selected_site') in site_urls:
                    current_index = site_urls.index(st.session_state['selected_site'])
                
                selected_site = st.radio(
                    "🌐 Analiz edilecek siteyi seçin:",
                    site_urls,
                    index=current_index,
                    key='site_radio_selector'
                )
                
                st.session_state['selected_site'] = selected_site
                
                if 'previous_site' in st.session_state:
                    if selected_site != st.session_state['previous_site']:
                        if 'analytics_data' in st.session_state:
                            del st.session_state['analytics_data']
                        if 'data_loaded' in st.session_state:
                            st.session_state['data_loaded'] = False
                
                st.session_state['previous_site'] = selected_site
                
                if selected_site:
                    st.markdown("---")
                    st.subheader("📅 Tarih Aralığı")
                    
                    date_options = [
                        "Son 7 Gün",
                        "Son 14 Gün",
                        "Son 30 Gün",
                        "Bu Ay",
                        "Geçen Ay",
                        "Özel Tarih"
                    ]
                    
                    if 'date_period' not in st.session_state:
                        st.session_state['date_period'] = "Son 30 Gün"
                    
                    period_index = date_options.index(st.session_state.get('date_period', "Son 30 Gün"))
                    
                    selected_period = st.radio(
                        "Hızlı Seçenekler:",
                        date_options,
                        horizontal=True,
                        key='date_period_radio',
                        index=period_index
                    )
                    
                    if selected_period != st.session_state.get('date_period'):
                        st.session_state['date_period'] = selected_period
                    
                    if selected_period != "Özel Tarih":
                        start_date, end_date = get_date_range(selected_period)
                        st.session_state['start_date'] = start_date
                        st.session_state['end_date'] = end_date
                    else:
                        col1, col2 = st.columns(2)
                        default_end = datetime.now().date()
                        default_start = default_end - timedelta(days=30)
                        
                        with col1:
                            start_date = st.date_input(
                                "Başlangıç Tarihi",
                                value=st.session_state.get('start_date', default_start),
                                max_value=datetime.now().date(),
                                key='start_date_input'
                            )
                            st.session_state['start_date'] = start_date
                        
                        with col2:
                            end_date = st.date_input(
                                "Bitiş Tarihi",
                                value=st.session_state.get('end_date', default_end),
                                max_value=datetime.now().date(),
                                key='end_date_input'
                            )
                            st.session_state['end_date'] = end_date
                    
                    if selected_period != "Özel Tarih":
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"📅 **Başlangıç:** {st.session_state['start_date'].strftime('%d.%m.%Y')}")
                        with col2:
                            st.info(f"📅 **Bitiş:** {st.session_state['end_date'].strftime('%d.%m.%Y')}")
                        start_date = st.session_state['start_date']
                        end_date = st.session_state['end_date']
                    
                    if start_date > end_date:
                        st.error("⚠️ Başlangıç tarihi bitiş tarihinden sonra olamaz!")
                    else:
                        st.markdown("---")
                        
                        if st.button("📊 Verileri Getir", type="primary", use_container_width=True):
                            with st.spinner("Veriler çekiliyor, lütfen bekleyin..."):
                                rows = get_search_analytics(
                                    service, 
                                    selected_site, 
                                    start_date, 
                                    end_date,
                                    row_limit=None
                                )
                                
                                if rows:
                                    data = []
                                    for row in rows:
                                        keys = row.get('keys', [])
                                        if len(keys) >= 2:
                                            data.append({
                                                'Anahtar Kelime': keys[0] if keys[0] else 'N/A',
                                                'İlgili Sayfa': keys[1] if keys[1] else 'N/A',
                                                'Tıklama': row.get('clicks', 0),
                                                'Gösterim': row.get('impressions', 0),
                                                'CTR': row.get('ctr', 0),
                                                'Ortalama Pozisyon': row.get('position', None)
                                            })
                                    
                                    if data:
                                        df = pd.DataFrame(data)
                                        df = df.sort_values('Tıklama', ascending=False)
                                        st.session_state['analytics_data'] = df
                                        st.session_state['data_loaded'] = True
                                        st.success(f"✅ {len(df)} kayıt başarıyla yüklendi!")
                                    else:
                                        st.warning("Veri bulunamadı.")
                                        st.session_state['data_loaded'] = False
                                else:
                                    st.warning("Seçilen tarih aralığında veri bulunamadı.")
                                    st.session_state['data_loaded'] = False
                        
                        if st.session_state.get('data_loaded', False) and 'analytics_data' in st.session_state:
                            df = st.session_state['analytics_data'].copy()
                            
                            st.markdown("---")
                            st.subheader("📈 Detaylı Analitik Veriler")
                            
                            search_term = st.text_input(
                                "🔍 Arama (Anahtar Kelime veya Sayfa):",
                                key='search_input',
                                placeholder="Anahtar kelime veya sayfa URL'si ile arayın..."
                            )
                            
                            if search_term:
                                mask = (
                                    df['Anahtar Kelime'].str.contains(search_term, case=False, na=False) |
                                    df['İlgili Sayfa'].str.contains(search_term, case=False, na=False)
                                )
                                df_filtered = df[mask]
                            else:
                                df_filtered = df
                            
                            if not df_filtered.empty:
                                df_display = df_filtered.copy()
                                df_display['Ortalama Pozisyon'] = df_display['Ortalama Pozisyon'].apply(format_position)
                                df_display['CTR'] = df_display['CTR'].apply(format_ctr)
                                df_display['Tıklama'] = df_display['Tıklama'].astype(int)
                                df_display['Gösterim'] = df_display['Gösterim'].astype(int)
                                
                                st.dataframe(
                                    df_display,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        'Anahtar Kelime': st.column_config.TextColumn('Anahtar Kelime', width='medium'),
                                        'İlgili Sayfa': st.column_config.TextColumn('İlgili Sayfa', width='large'),
                                        'Tıklama': st.column_config.NumberColumn('Tıklama', format='%d'),
                                        'Gösterim': st.column_config.NumberColumn('Gösterim', format='%d'),
                                        'CTR': st.column_config.TextColumn('CTR'),
                                        'Ortalama Pozisyon': st.column_config.TextColumn('Ortalama Pozisyon')
                                    }
                                )
                                
                                st.markdown("### 📊 Özet İstatistikler")
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric("Toplam Tıklama", f"{df_filtered['Tıklama'].sum():,}")
                                with col2:
                                    st.metric("Toplam Gösterim", f"{df_filtered['Gösterim'].sum():,}")
                                with col3:
                                    total_ctr = (df_filtered['Tıklama'].sum() / df_filtered['Gösterim'].sum() * 100) if df_filtered['Gösterim'].sum() > 0 else 0
                                    st.metric("Ortalama CTR", f"{total_ctr:.2f}%")
                                with col4:
                                    avg_pos = df_filtered['Ortalama Pozisyon'].mean()
                                    st.metric("Ortalama Pozisyon", f"{avg_pos:.1f}" if not pd.isna(avg_pos) else "N/A")
                            else:
                                st.info("Arama kriterinize uygun sonuç bulunamadı.")
            else:
                st.warning("Search Console'da henüz mülk bulunmuyor.")
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
            if "invalid_grant" in str(e).lower() or "token" in str(e).lower():
                st.info("Token süresi dolmuş olabilir. Lütfen tekrar bağlanın.")
                if 'credentials' in st.session_state:
                    del st.session_state['credentials']
                st.rerun()

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
        
        if st.button("🔗 Google Ads'e Bağlan", type="primary", use_container_width=True):
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

def render_meta_ads():
    """Meta Ads sayfası"""
    st.title("📱 Meta Ads")
    st.markdown("---")
    
    # Access Token input
    st.subheader("🔑 Access Token")
    st.info("Meta Ads hesabınıza erişmek için Access Token gerekir.")
    
    # Session state'te token'ı sakla
    if 'meta_access_token' not in st.session_state:
        st.session_state['meta_access_token'] = ""
    
    access_token = st.text_input(
        "Access Token (Erişim Belgesi):",
        value=st.session_state.get('meta_access_token', ''),
        type="password",
        key='meta_token_input',
        help="Meta Ads API Access Token'ınızı buraya girin."
    )
    
    if access_token:
        st.session_state['meta_access_token'] = access_token
        
        st.markdown("---")
        st.subheader("📊 Reklam Hesapları")
        st.info(f"**İzlenen Hesaplar:** {', '.join([acc.replace('act_', '') for acc in META_ACCOUNT_IDS])}")
        
        st.markdown("---")
        st.subheader("📈 Hesap Performansı (Son 7 Gün)")
        
        if st.button("📊 Verileri Getir", type="primary", use_container_width=True):
            with st.spinner("Veriler çekiliyor, lütfen bekleyin..."):
                all_data, errors = get_all_meta_ads_data(access_token, days=7)
                
                # Hataları göster
                if errors:
                    for error in errors:
                        st.error(f"❌ **Hesap {error['account_id']} Hatası:** {error['error']}")
                
                if all_data:
                    df = pd.DataFrame(all_data)
                    
                    # Toplamları hesapla
                    total_spend = df['Harcama ($)'].sum()
                    total_impressions = df['Gösterim'].sum()
                    total_clicks = df['Tıklama'].sum()
                    avg_cpm = df['CPM ($)'].mean()
                    
                    # Tabloyu göster
                    st.markdown("### 📋 Detaylı Veriler")
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'Hesap ID': st.column_config.TextColumn('Hesap ID', width='small'),
                            'Harcama ($)': st.column_config.NumberColumn(
                                'Harcama ($)',
                                format='$%.2f'
                            ),
                            'Gösterim': st.column_config.NumberColumn(
                                'Gösterim',
                                format='%d'
                            ),
                            'Tıklama': st.column_config.NumberColumn(
                                'Tıklama',
                                format='%d'
                            ),
                            'CPM ($)': st.column_config.NumberColumn(
                                'CPM ($)',
                                format='$%.2f'
                            ),
                            'Tarih Başlangıç': st.column_config.TextColumn('Tarih Başlangıç'),
                            'Tarih Bitiş': st.column_config.TextColumn('Tarih Bitiş')
                        }
                    )
                    
                    # Hesap bazında özet
                    st.markdown("### 📊 Hesap Bazında Özet")
                    account_summary = df.groupby('Hesap ID').agg({
                        'Harcama ($)': 'sum',
                        'Gösterim': 'sum',
                        'Tıklama': 'sum',
                        'CPM ($)': 'mean'
                    }).reset_index()
                    
                    account_summary.columns = ['Hesap ID', 'Toplam Harcama ($)', 'Toplam Gösterim', 'Toplam Tıklama', 'Ortalama CPM ($)']
                    st.dataframe(
                        account_summary,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'Toplam Harcama ($)': st.column_config.NumberColumn(
                                'Toplam Harcama ($)',
                                format='$%.2f'
                            ),
                            'Toplam Gösterim': st.column_config.NumberColumn(
                                'Toplam Gösterim',
                                format='%d'
                            ),
                            'Toplam Tıklama': st.column_config.NumberColumn(
                                'Toplam Tıklama',
                                format='%d'
                            ),
                            'Ortalama CPM ($)': st.column_config.NumberColumn(
                                'Ortalama CPM ($)',
                                format='$%.2f'
                            )
                        }
                    )
                    
                    # Genel özet metrikleri
                    st.markdown("### 📈 Genel Özet İstatistikler")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Toplam Harcama", f"${total_spend:,.2f}")
                    
                    with col2:
                        st.metric("Toplam Gösterim", f"{total_impressions:,}")
                    
                    with col3:
                        st.metric("Toplam Tıklama", f"{total_clicks:,}")
                    
                    with col4:
                        st.metric("Ortalama CPM", f"${avg_cpm:,.2f}")
                    
                    # Session state'e kaydet (dashboard için)
                    st.session_state['meta_ads_total_spend'] = total_spend
                    st.session_state['meta_ads_data'] = df
                    
                    st.success(f"✅ {len(df)} kayıt başarıyla yüklendi!")
                elif not errors:
                    st.warning("⚠️ Veri bulunamadı. Seçilen tarih aralığında veri olmayabilir.")
    else:
        st.warning("⚠️ Lütfen Access Token girin.")
        st.info("""
        **Access Token Nasıl Alınır?**
        1. Facebook Developers (developers.facebook.com) hesabınıza giriş yapın
        2. Graph API Explorer'ı kullanın
        3. İhtiyacınız olan izinleri seçin (ads_read)
        4. Access Token'ı kopyalayın
        """)

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

# ==================== ANA UYGULAMA ====================

def main():
    # Sidebar menü
    with st.sidebar:
        st.title("📊 Marketing SaaS")
        st.markdown("---")
        
        selected = option_menu(
            menu_title=None,
            options=["Genel Bakış", "SEO", "Google Ads", "Meta Ads", "Ayarlar"],
            icons=["house", "search", "currency-dollar", "facebook", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "5!important", "background-color": "#fafafa"},
                "icon": {"color": "#1f77b4", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0px",
                    "padding": "10px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "#1f77b4"},
            }
        )
    
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
