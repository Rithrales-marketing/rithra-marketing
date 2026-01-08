"""SEO - Search Console sayfası"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from src.integrations.google_search_console import (
    get_flow,
    get_credentials,
    save_credentials,
    get_search_console_service,
    list_sites,
    get_search_analytics
)
from src.utils.formatting import format_position, format_ctr
from src.utils.date_utils import get_date_range
from src.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, REDIRECT_URI, SCOPES


def render_seo_search_console():
    """SEO - Search Console sayfası"""
    # SEO sayfası için özel yeşil buton stili
    st.markdown("""
    <style>
    /* SEO sayfası butonları için yeşil renk */
    h1:contains("SEO") ~ * button[kind="primary"],
    button[key*="seo"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
    }
    button[key*="seo"]:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🔍 SEO - Search Console")
    st.markdown("---")

    # Credentials kontrolü
    credentials = get_credentials()

    # URL parametrelerinden authorization code'u kontrol et
    query_params = st.query_params
    if 'code' in query_params and credentials is None:
        try:
            # OAuth callback geldiğinde, redirect URI'yi tekrar belirle
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
            save_credentials(credentials)
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
        st.info("Google Search Console'a bağlanmak için aşağıdaki butona tıklayın.")
        
        if st.button("🔗 Google ile Bağlan", type="primary", use_container_width=True, key="seo_connect_btn"):
            try:
                flow = get_flow()
                authorization_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='consent'
                )
                st.markdown(f"[Google'a yönlendirmek için tıklayın]({authorization_url})")
                st.info("Yukarıdaki bağlantıya tıklayarak Google hesabınızla giriş yapın.")
            except Exception as e:
                st.error(f"OAuth akışı başlatılamadı: {e}")
                if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
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
