"""Formatting yardımcı fonksiyonları"""
import pandas as pd


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
