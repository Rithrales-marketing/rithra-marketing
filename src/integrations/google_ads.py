"""Google Ads entegrasyonu"""
import streamlit as st
from src.config import (
    GOOGLE_ADS_DEVELOPER_TOKEN,
    GOOGLE_ADS_CUSTOMER_ID,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET
)


def get_google_ads_client():
    """Google Ads API client'ı oluştur (iskelet)"""
    # TODO: Google Ads API entegrasyonu
    # from google.ads.googleads.client import GoogleAdsClient
    # client = GoogleAdsClient.load_from_dict({
    #     "developer_token": GOOGLE_ADS_DEVELOPER_TOKEN,
    #     "client_id": GOOGLE_CLIENT_ID,
    #     "client_secret": GOOGLE_CLIENT_SECRET,
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
