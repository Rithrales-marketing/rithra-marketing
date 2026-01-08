"""Integrations modülü"""
from .google_search_console import (
    get_flow,
    get_credentials,
    save_credentials,
    get_search_console_service,
    list_sites,
    get_search_analytics
)

from .google_ads import (
    get_google_ads_client,
    get_google_ads_total_spend,
    get_google_ads_credentials,
    save_google_ads_credentials,
    get_campaigns_data,
    list_customer_accounts
)

from .meta_ads import (
    get_meta_ads_insights_for_account,
    get_all_meta_ads_data,
    get_meta_ads_total_spend
)

__all__ = [
    # Google Search Console
    'get_flow',
    'get_credentials',
    'save_credentials',
    'get_search_console_service',
    'list_sites',
    'get_search_analytics',
    # Google Ads
    'get_google_ads_client',
    'get_google_ads_total_spend',
    'get_google_ads_credentials',
    'save_google_ads_credentials',
    'get_campaigns_data',
    'list_customer_accounts',
    # Meta Ads
    'get_meta_ads_insights_for_account',
    'get_all_meta_ads_data',
    'get_meta_ads_total_spend'
]
