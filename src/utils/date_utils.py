"""Tarih yardımcı fonksiyonları"""
from datetime import datetime, timedelta


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
