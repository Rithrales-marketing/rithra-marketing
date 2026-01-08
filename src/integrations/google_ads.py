"""Google Ads entegrasyonu"""
import streamlit as st
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
from src.config import (
    GOOGLE_ADS_DEVELOPER_TOKEN,
    GOOGLE_ADS_CUSTOMER_ID,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET
)


def get_google_ads_credentials():
    """Session state'ten Google Ads credentials al"""
    if 'google_ads_credentials' in st.session_state:
        creds_dict = st.session_state['google_ads_credentials']
        return Credentials.from_authorized_user_info(creds_dict)
    return None


def save_google_ads_credentials(credentials):
    """Google Ads credentials'ı session state'e kaydet"""
    st.session_state['google_ads_credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }


def get_google_ads_client():
    """Google Ads API client'ı oluştur"""
    if not GOOGLE_ADS_DEVELOPER_TOKEN or not GOOGLE_ADS_CUSTOMER_ID:
        return None
    
    credentials = get_google_ads_credentials()
    if not credentials:
        return None
    
    # Token'ı yenile
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            save_google_ads_credentials(credentials)
        except Exception as e:
            st.error(f"Token yenileme hatası: {e}")
            return None
    
    try:
        # Google Ads API client'ı oluştur
        client = GoogleAdsClient.load_from_dict({
            "developer_token": GOOGLE_ADS_DEVELOPER_TOKEN,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": credentials.refresh_token,
            "use_proto_plus": True
        })
        return client
    except Exception as e:
        st.error(f"Google Ads client oluşturma hatası: {e}")
        return None


def get_campaigns_data(client, customer_id, start_date=None, end_date=None):
    """Kampanya performans verilerini çek"""
    if not client or not customer_id:
        return []
    
    # Customer ID formatını düzelt (tire varsa kaldır, 10 haneli olmalı)
    customer_id = str(customer_id).replace('-', '')
    if len(customer_id) != 10:
        st.error(f"Geçersiz Customer ID formatı: {customer_id}. 10 haneli olmalı.")
        return []
    
    # Varsayılan tarih aralığı: Son 30 gün
    if not end_date:
        end_date = datetime.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    try:
        ga_service = client.get_service("GoogleAdsService")
        
        # Sorgu oluştur - segments.date ile günlük veri çek
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_per_conversion
            FROM campaign
            WHERE campaign.status != 'REMOVED'
            AND segments.date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY campaign.id, segments.date
        """
        
        # İstek gönder
        response = ga_service.search(customer_id=customer_id, query=query)
        
        campaigns_data = []
        campaign_dict = {}
        
        for row in response:
            campaign_id = row.campaign.id
            campaign_name = row.campaign.name
            
            if campaign_id not in campaign_dict:
                campaign_dict[campaign_id] = {
                    'Kampanya ID': campaign_id,
                    'Kampanya Adı': campaign_name,
                    'Durum': row.campaign.status.name,
                    'Gösterim': 0,
                    'Tıklama': 0,
                    'Maliyet (₺)': 0.0,
                    'Dönüşüm': 0.0,
                    'CTR': 0.0,
                    'Ortalama CPC (₺)': 0.0,
                    'Dönüşüm Başına Maliyet (₺)': 0.0,
                    'Günlük Kayıt Sayısı': 0
                }
            
            # Metrikleri topla
            if row.metrics.impressions:
                campaign_dict[campaign_id]['Gösterim'] += row.metrics.impressions
            if row.metrics.clicks:
                campaign_dict[campaign_id]['Tıklama'] += row.metrics.clicks
            if row.metrics.cost_micros:
                campaign_dict[campaign_id]['Maliyet (₺)'] += row.metrics.cost_micros / 1_000_000
            if row.metrics.conversions:
                campaign_dict[campaign_id]['Dönüşüm'] += row.metrics.conversions
            
            # Ortalama değerler (son değerleri kullan)
            if row.metrics.ctr is not None:
                campaign_dict[campaign_id]['CTR'] = row.metrics.ctr
            if row.metrics.average_cpc is not None:
                campaign_dict[campaign_id]['Ortalama CPC (₺)'] = row.metrics.average_cpc / 1_000_000
            if row.metrics.cost_per_conversion is not None and row.metrics.cost_per_conversion > 0:
                campaign_dict[campaign_id]['Dönüşüm Başına Maliyet (₺)'] = row.metrics.cost_per_conversion / 1_000_000
            
            campaign_dict[campaign_id]['Günlük Kayıt Sayısı'] += 1
        
        # CTR'yi hesapla (toplam tıklama / toplam gösterim * 100)
        for campaign_id in campaign_dict:
            if campaign_dict[campaign_id]['Gösterim'] > 0:
                campaign_dict[campaign_id]['CTR'] = (
                    campaign_dict[campaign_id]['Tıklama'] / 
                    campaign_dict[campaign_id]['Gösterim'] * 100
                )
            # Ortalama CPC'yi hesapla
            if campaign_dict[campaign_id]['Tıklama'] > 0:
                campaign_dict[campaign_id]['Ortalama CPC (₺)'] = (
                    campaign_dict[campaign_id]['Maliyet (₺)'] / 
                    campaign_dict[campaign_id]['Tıklama']
                )
            # Dönüşüm başına maliyeti hesapla
            if campaign_dict[campaign_id]['Dönüşüm'] > 0:
                campaign_dict[campaign_id]['Dönüşüm Başına Maliyet (₺)'] = (
                    campaign_dict[campaign_id]['Maliyet (₺)'] / 
                    campaign_dict[campaign_id]['Dönüşüm']
                )
            
            # Günlük kayıt sayısını kaldır (gösterim için değil)
            del campaign_dict[campaign_id]['Günlük Kayıt Sayısı']
        
        campaigns_data = list(campaign_dict.values())
        # Maliyete göre sırala
        campaigns_data.sort(key=lambda x: x['Maliyet (₺)'], reverse=True)
        return campaigns_data
        
    except GoogleAdsException as ex:
        error_message = ""
        for error in ex.failure.errors:
            # error_code hatasını düzelt
            error_code_str = ""
            try:
                if hasattr(error, 'error_code') and hasattr(error.error_code, 'error_code'):
                    error_code_str = f"{error.error_code.error_code}: "
            except:
                pass
            error_message += f"Error {error_code_str}{error.message}\n"
            if hasattr(error, 'location') and error.location:
                for field_path_element in error.location.field_path_elements:
                    error_message += f"  Field: {field_path_element.field_name}\n"
        st.error(f"Google Ads API hatası:\n{error_message}")
        return []
    except Exception as e:
        st.error(f"Beklenmeyen hata: {e}")
        import traceback
        st.error(f"Detay: {traceback.format_exc()}")
        return []


def list_customer_accounts(client, manager_customer_id=None):
    """MCC hesabının altındaki müşteri hesaplarını listele"""
    if not client:
        return []
    
    try:
        # Eğer manager_customer_id verilmediyse, config'den al
        if not manager_customer_id:
            manager_customer_id = GOOGLE_ADS_CUSTOMER_ID
        
        # Customer ID formatını düzelt
        manager_customer_id = str(manager_customer_id).replace('-', '')
        
        ga_service = client.get_service("GoogleAdsService")
        
        # MCC hesabının altındaki tüm müşteri hesaplarını çek
        # customer_client tablosu MCC hesabının altındaki tüm hesapları gösterir
        query = """
            SELECT
                customer_client.id,
                customer_client.descriptive_name,
                customer_client.currency_code,
                customer_client.time_zone,
                customer_client.manager,
                customer_client.test_account,
                customer_client.status
            FROM customer_client
            WHERE customer_client.status = 'ENABLED'
            ORDER BY customer_client.descriptive_name
        """
        
        # İstek gönder - Manager hesabından müşteri hesaplarını çek
        response = ga_service.search(customer_id=manager_customer_id, query=query)
        
        customer_accounts = []
        for row in response:
            customer_id = row.customer_client.id
            customer_name = row.customer_client.descriptive_name
            currency = row.customer_client.currency_code
            timezone = row.customer_client.time_zone
            is_manager = row.customer_client.manager
            is_test = row.customer_client.test_account
            status = row.customer_client.status.name if hasattr(row.customer_client.status, 'name') else str(row.customer_client.status)
            
            # Manager hesaplarını atla - sadece müşteri hesaplarını göster
            # Manager hesaplarından metrik çekilemez
            if is_manager:
                continue
            
            # Sadece aktif hesapları göster
            if status != 'ENABLED':
                continue
            
            customer_accounts.append({
                'Customer ID': str(customer_id),
                'Hesap Adı': customer_name if customer_name else f"Customer {customer_id}",
                'Para Birimi': currency if currency else 'N/A',
                'Zaman Dilimi': timezone if timezone else 'N/A',
                'Manager': 'Evet' if is_manager else 'Hayır',
                'Test Hesabı': 'Evet' if is_test else 'Hayır'
            })
        
        return customer_accounts
        
    except GoogleAdsException as ex:
        error_message = ""
        for error in ex.failure.errors:
            error_code_str = ""
            try:
                if hasattr(error, 'error_code') and hasattr(error.error_code, 'error_code'):
                    error_code_str = f"{error.error_code.error_code}: "
            except:
                pass
            error_message += f"Error {error_code_str}{error.message}\n"
        st.error(f"Müşteri hesapları listelenirken hata:\n{error_message}")
        return []
    except Exception as e:
        st.error(f"Beklenmeyen hata: {e}")
        import traceback
        st.error(f"Detay: {traceback.format_exc()}")
        return []


def get_conversion_details(client, customer_id, start_date=None, end_date=None):
    """Dönüşüm detaylarını çek - keyword, arama terimi, reklam URL'si ve dönüşüm türü"""
    if not client or not customer_id:
        return []
    
    # Customer ID formatını düzelt
    customer_id = str(customer_id).replace('-', '')
    if len(customer_id) != 10:
        st.error(f"Geçersiz Customer ID formatı: {customer_id}. 10 haneli olmalı.")
        return []
    
    # Varsayılan tarih aralığı: Son 30 gün
    if not end_date:
        end_date = datetime.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    try:
        ga_service = client.get_service("GoogleAdsService")
        
        # Dönüşüm detaylarını çek - search_term_view kullanarak
        query = f"""
            SELECT
                search_term_view.search_term,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_ad.ad.final_urls,
                ad_group_ad.ad.id,
                ad_group.name,
                campaign.name,
                segments.conversion_action_name,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_micros,
                segments.date
            FROM search_term_view
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
            AND metrics.conversions > 0
            ORDER BY metrics.conversions DESC, segments.date DESC
            LIMIT 10000
        """
        
        # İstek gönder
        response = ga_service.search(customer_id=customer_id, query=query)
        
        conversion_details = []
        for row in response:
            try:
                search_term = row.search_term_view.search_term if hasattr(row, 'search_term_view') and row.search_term_view else 'N/A'
            except:
                search_term = 'N/A'
            
            try:
                keyword_text = row.ad_group_criterion.keyword.text if hasattr(row, 'ad_group_criterion') and row.ad_group_criterion else 'N/A'
                match_type = row.ad_group_criterion.keyword.match_type.name if hasattr(row, 'ad_group_criterion') and row.ad_group_criterion and hasattr(row.ad_group_criterion.keyword, 'match_type') else 'N/A'
            except:
                keyword_text = 'N/A'
                match_type = 'N/A'
            
            # Final URLs
            try:
                if hasattr(row, 'ad_group_ad') and row.ad_group_ad and hasattr(row.ad_group_ad, 'ad') and hasattr(row.ad_group_ad.ad, 'final_urls'):
                    final_urls = list(row.ad_group_ad.ad.final_urls)
                    ad_url = final_urls[0] if final_urls else 'N/A'
                else:
                    ad_url = 'N/A'
            except:
                ad_url = 'N/A'
            
            try:
                ad_id = row.ad_group_ad.ad.id if hasattr(row, 'ad_group_ad') and row.ad_group_ad and hasattr(row.ad_group_ad, 'ad') else 'N/A'
            except:
                ad_id = 'N/A'
            
            try:
                ad_group_name = row.ad_group.name if hasattr(row, 'ad_group') and row.ad_group else 'N/A'
            except:
                ad_group_name = 'N/A'
            
            try:
                campaign_name = row.campaign.name if hasattr(row, 'campaign') and row.campaign else 'N/A'
            except:
                campaign_name = 'N/A'
            
            try:
                conversion_action_name = row.segments.conversion_action_name if hasattr(row.segments, 'conversion_action_name') else 'N/A'
            except:
                conversion_action_name = 'N/A'
            
            try:
                conversions = row.metrics.conversions if hasattr(row.metrics, 'conversions') and row.metrics.conversions else 0
            except:
                conversions = 0
            
            try:
                conversions_value = row.metrics.conversions_value if hasattr(row.metrics, 'conversions_value') and row.metrics.conversions_value else 0.0
            except:
                conversions_value = 0.0
            
            try:
                cost = row.metrics.cost_micros / 1_000_000 if hasattr(row.metrics, 'cost_micros') and row.metrics.cost_micros else 0.0
            except:
                cost = 0.0
            
            try:
                date = str(row.segments.date) if hasattr(row.segments, 'date') else 'N/A'
            except:
                date = 'N/A'
            
            conversion_details.append({
                'Tarih': str(date),
                'Arama Terimi': search_term,
                'Keyword': keyword_text,
                'Eşleşme Türü': match_type,
                'Reklam URL': ad_url,
                'Reklam ID': ad_id,
                'Reklam Grubu': ad_group_name,
                'Kampanya': campaign_name,
                'Dönüşüm Türü': conversion_action_name,
                'Dönüşüm Sayısı': conversions,
                'Dönüşüm Değeri (₺)': conversions_value,
                'Maliyet (₺)': cost
            })
        
        return conversion_details
        
    except GoogleAdsException as ex:
        error_message = ""
        for error in ex.failure.errors:
            error_code_str = ""
            try:
                if hasattr(error, 'error_code'):
                    error_code_str = f"{error.error_code}: "
            except:
                pass
            error_message += f"Error {error_code_str}{error.message}\n"
        st.error(f"Dönüşüm detayları çekilirken hata:\n{error_message}")
        return []
    except Exception as e:
        st.error(f"Beklenmeyen hata: {e}")
        import traceback
        st.error(f"Detay: {traceback.format_exc()}")
        return []


def get_google_ads_total_spend():
    """Google Ads toplam harcamasını getir"""
    if 'google_ads_total_spend' in st.session_state:
        return st.session_state['google_ads_total_spend']
    return 0.0
