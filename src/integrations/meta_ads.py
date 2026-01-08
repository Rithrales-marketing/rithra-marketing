"""Meta Ads entegrasyonu"""
import streamlit as st
from datetime import datetime, timedelta
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.exceptions import FacebookRequestError
from src.config import META_ACCOUNT_IDS


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
