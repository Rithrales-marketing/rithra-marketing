"""Sayfa render fonksiyonları modülü"""
from .dashboard import render_dashboard
from .seo import render_seo_search_console
from .google_ads_page import render_google_ads
from .meta_ads_page import render_meta_ads
from .settings import render_settings

__all__ = [
    'render_dashboard',
    'render_seo_search_console',
    'render_google_ads',
    'render_meta_ads',
    'render_settings'
]
