"""Dashboard sayfası"""
import streamlit as st


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
