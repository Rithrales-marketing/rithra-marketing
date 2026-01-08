"""Meta Ads sayfası"""
import streamlit as st
import pandas as pd
from src.config import META_ACCOUNT_IDS
from src.integrations.meta_ads import get_all_meta_ads_data


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
        
        if st.button("📊 Verileri Getir", type="primary", use_container_width=True, key="meta_ads_fetch_btn"):
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
