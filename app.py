import streamlit as st
import pandas as pd

# --- 1. 配置页面 ---
st.set_page_config(page_title="酒店入住管理系统", layout="centered")

# --- 2. 初始化 Session State (核心修复点) ---
def init_connection():
    if 'page' not in st.session_state:
        st.session_state.page = 'input_info'
    if 'customer_data' not in st.session_state:
        st.session_state.customer_data = []
    if 'rooms' not in st.session_state:
        # 初始库存
        st.session_state.rooms = {"大床房": 5, "双床房": 3}
    if 'temp_user' not in st.session_state:
        st.session_state.temp_user = {}
    if 'error_msg' not in st.session_state:
        st.session_state.error_msg = ""

init_connection()

# 房价配置
ROOM_PRICES = {"大床房": 200, "双床房": 250}

# 跳转函数
def navigate_to(page_name):
    st.session_state.page =…
