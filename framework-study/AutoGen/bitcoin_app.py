"""
比特币价格显示应用 - 完整实现版本
功能：实时显示比特币当前价格、24小时涨跌幅和涨跌额
技术栈：Streamlit + Requests + CoinGecko API
"""

import streamlit as st
import requests
import time
from datetime import datetime
import traceback

# ==================== 配置部分 ====================
# CoinGecko API的端点
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
# 应用刷新间隔（秒）
AUTO_REFRESH_INTERVAL = 30  # 设置为30秒自动刷新

# ==================== 数据获取模块 ====================
@st.cache_data(ttl=10)  # 缓存10秒，避免频繁调用API
def fetch_bitcoin_data():
    """
    从CoinGecko API获取比特币价格数据
    
    返回:
        dict: 包含比特币价格和变化数据的字典，格式如下：
            {
                "current_price": float,
                "price_change_24h": float,
                "price_change_percentage_24h": float
            }
        如果获取失败，返回None
    """
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_24hr_vol": "false",
        "include_last_updated_at": "false"
    }
    
    try:
        response = requests.get(COINGECKO_API_URL, params=params, timeout=10)
        response.raise_for_status()  # 如果响应状态码不是200，抛出HTTPError
        
        data = response.json()
        
        if "bitcoin" not in data:
            st.error("API响应中未找到比特币数据")
            return None
        
        bitcoin_data = data["bitcoin"]
        
        return {
            "current_price": bitcoin_data.get("usd", 0),
            "price_change_24h": bitcoin_data.get("usd_24h_change", 0),
            "price_change_percentage_24h": bitcoin_data.get("usd_24h_change", 0),
            "last_updated": datetime.now().strftime("%H:%M:%S")
        }
        
    except requests.exceptions.RequestException as e:
        st.error(f"网络请求失败: {str(e)}")
        return None
    except ValueError as e:
        st.error(f"解析JSON响应失败: {str(e)}")
        return None
    except Exception as e:
        st.error(f"获取数据时发生未知错误: {str(e)}")
        return None

# ==================== 界面初始化 ====================
def setup_page():
    """设置页面布局和样式"""
    st.set_page_config(
        page_title="Bitcoin Price Tracker",
        page_icon="₿",
        layout="centered"
    )
    
    # 自定义CSS样式
    st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #F7931A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .price-card {
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: #f8f9fa;
        margin-bottom: 1.5rem;
    }
    .positive-change {
        color: #10B981;
        font-weight: bold;
    }
    .negative-change {
        color: #EF4444;
        font-weight: bold;
    }
    .last-updated {
        font-size: 0.9rem;
        color: #6B7280;
        text-align: center;
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 应用标题
    st.markdown('<h1 class="main-title">₿ Bitcoin Price Tracker</h1>', unsafe_allow_html=True)

# ==================== 数据展示模块 ====================
def display_price_data(price_data):
    """
    展示比特币价格数据
    
    参数:
        price_data: 包含比特币价格数据的字典
    """
    if not price_data:
        st.warning("暂无有效价格数据")
        return
    
    current_price = price_data.get("current_price", 0)
    price_change = price_data.get("price_change_24h", 0)
    price_change_percentage = price_data.get("price_change_percentage_24h", 0)
    last_updated = price_data.get("last_updated", "")
    
    # 格式化价格显示
    price_formatted = f"${current_price:,.2f}"
    
    # 计算涨跌额（基于百分比变化）
    change_amount = current_price * (price_change_percentage / 100)
    change_amount_formatted = f"${abs(change_amount):,.2f}"
    
    # 确定涨跌颜色和符号
    is_positive = price_change_percentage >= 0
    change_prefix = "+" if is_positive else "-"
    percentage_formatted = f"{change_prefix}{abs(price_change_percentage):.2f}%"
    
    # 创建容器显示价格卡片
    with st.container():
        st.markdown('<div class="price-card">', unsafe_allow_html=True)
        
        # 使用两列布局
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown(f"### Current Price")
            st.markdown(f"### **{price_formatted}**")
            
        with col2:
            st.markdown(f"### 24H Change")
            # 根据涨跌使用不同的CSS类
            change_class = "positive-change" if is_positive else "negative-change"
            st.markdown(f'<h3 class="{change_class}">**{percentage_formatted}**</h3>', unsafe_allow_html=True)
            st.markdown(f"*({change_prefix}{change_amount_formatted})*")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    # 显示最后更新时间
    if last_updated:
        st.markdown(f'<p class="last-updated">Last updated: {last_updated}</p>', unsafe_allow_html=True)

# ==================== 主应用逻辑 ====================
def main():
    """主应用函数"""
    # 初始化页面
    setup_page()
    
    # 侧边栏设置
    with st.sidebar:
        st.header("Settings")
        
        # 自动刷新开关
        auto_refresh = st.checkbox("Enable Auto-Refresh", value=True)
        
        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh Interval (seconds)",
                min_value=10,
                max_value=300,
                value=AUTO_REFRESH_INTERVAL,
                step=10
            )
            st.caption(f"Data will refresh every {refresh_interval} seconds")
            
            # 使用Streamlit的自动刷新机制
            st.markdown("---")
            st.markdown("**Auto-refresh status:** Active")
            
        # 显示应用信息
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This app displays real-time Bitcoin price data using the CoinGecko API.
        
        **Data Source:** CoinGecko Public API
        **Framework:** Streamlit
        """)
    
    # 主内容区域
    st.markdown("---")
    
    # 创建刷新按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        refresh_clicked = st.button("🔄 Refresh Price Data", use_container_width=True)
    
    # 获取并显示数据
    try:
        # 显示加载状态
        with st.spinner("Fetching latest Bitcoin price..."):
            # 如果点击了刷新按钮，清除缓存强制重新获取
            if refresh_clicked:
                st.cache_data.clear()
                
            # 获取价格数据
            price_data = fetch_bitcoin_data()
        
        # 显示数据
        if price_data:
            display_price_data(price_data)
        else:
            st.error("Failed to fetch Bitcoin price data. Please try again.")
            
            # 提供重试选项
            if st.button("Retry"):
                st.cache_data.clear()
                st.rerun()
    
    except Exception as e:
        # 捕获并显示所有未处理的异常
        st.error("An unexpected error occurred while fetching data.")
        st.error(f"Error details: {str(e)}")
        
        # 开发模式下显示详细错误信息
        if st.session_state.get("debug_mode", False):
            with st.expander("Error Traceback"):
                st.code(traceback.format_exc())
    
    # 检查自动刷新
    if auto_refresh and 'refresh_interval' in locals():
        time.sleep(refresh_interval)
        st.rerun()

# ==================== 应用入口 ====================
if __name__ == "__main__":
    main()
