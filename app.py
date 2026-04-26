import streamlit as st
import pandas as pd
from datetime import datetime, date

# --- 1. 初始化系统配置 ---
st.set_page_config(page_title="Ultra PMS - 酒店管理系统", layout="wide")

def init_system():
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    
    # 房源数据库 (房号, 类型, 基础价)
    if 'rooms_db' not in st.session_state:
        st.session_state.rooms_db = {
            "101": {"type": "大床房", "base_price": 200, "status": "Clean", "guest": None},
            "102": {"type": "大床房", "base_price": 200, "status": "Clean", "guest": None},
            "103": {"type": "大床房", "base_price": 200, "status": "Dirty", "guest": None},
            "201": {"type": "双床房", "base_price": 250, "status": "Clean", "guest": None},
            "202": {"type": "双床房", "base_price": 250, "status": "OOO", "guest": None},
        }
    
    # 历史订单数据库 (修复缺陷 4: 订单查询)
    if 'bookings_history' not in st.session_state:
        st.session_state.bookings_history = []
    
    if 'audit_logs' not in st.session_state:
        st.session_state.audit_logs = []

init_system()

# --- 2. 核心功能函数 ---
def navigate(page):
    st.session_state.page = page
    st.rerun()

def log_action(action):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.audit_logs.append({"时间": now, "操作内容": action})

# --- 3. 页面渲染逻辑 ---

# 【控制台 - Dashboard】
if st.session_state.page == 'dashboard':
    st.title("🏨 Ultra PMS 智慧酒店管理")
    
    # 顶栏统计
    clean_count = sum(1 for r in st.session_state.rooms_db.values() if r['status'] == "Clean")
    total_revenue = sum(b['final_total'] for b in st.session_state.bookings_history)
    
    stat1, stat2, stat3 = st.columns(3)
    stat1.metric("可用空房", f"{clean_count} 间")
    stat2.metric("今日入住率", f"{(5-clean_count)/5*100:.0f}%")
    stat3.metric("累计总营收", f"RM {total_revenue:.2f}")

    st.divider()
    
    # 房态卡片展示
    st.subheader("实时房态矩阵")
    room_cols = st.columns(5)
    for i, (room_no, info) in enumerate(st.session_state.rooms_db.items()):
        with room_cols[i % 5]:
            bg_color = "#d1e7dd" if info['status'] == "Clean" else "#f8d7da" if info['status'] == "Dirty" else "#fff3cd"
            st.markdown(f"""
                <div style="background-color:{bg_color}; padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:10px">
                    <h3 style="margin:0; color:#333">{room_no}</h3>
                    <p style="margin:0; font-size:0.8em; color:#666">{info['type']}</p>
                    <p style="margin:10px 0 0 0; font-weight:bold; color:#444">{info['status']}</p>
                    <p style="margin:0; font-size:0.7em">{'👤 '+info['guest'] if info['guest'] else '空闲'}</p>
                </div>
            """, unsafe_allow_html=True)

    st.divider()
    # 导航区
    nav_cols = st.columns(5)
    if nav_cols[0].button("📝 办理入住", use_container_width=True): navigate('check_in')
    if nav_cols[1].button("🔑 办理退房", use_container_width=True): navigate('check_out')
    if nav_cols[2].button("🛠️ 房态维护", use_container_width=True): navigate('manage_rooms')
    if nav_cols[3].button("📊 历史账单", use_container_width=True): navigate('history')
    if nav_cols[4].button("📑 审计日志", use_container_width=True): navigate('audit')

# 【办理入住 - 修复缺陷 7, 8】
elif st.session_state.page == 'check_in':
    st.title("新客登记办理")
    
    with st.form("checkin_form"):
        col1, col2 = st.columns(2)
        guest_name = col1.text_input("客人姓名")
        guest_ic = col2.text_input("IC 编号")
        
        # 缺陷 7: 日期范围预订
        stay_range = st.date_input("选择入住与退房日期", [date.today(), date.today() + timedelta(days=1)])
        
        # 缺陷 8: 多房间选择
        available_list = [r for r, v in st.session_state.rooms_db.items() if v['status'] == "Clean"]
        selected_rooms = st.multiselect("分配房间 (可多选)", available_list)
        
        # 缺陷 3: 动态单价微调 (允许前台手动修改价格)
        custom_rate = st.number_input("协议单价调整 (RM/晚, 0表示按系统原价)", min_value=0.0)
        
        if st.form_submit_button("生成账单"):
            if not selected_rooms or not guest_name or len(stay_range) < 2:
                st.error("请完整填写资料并选择至少一个房间")
            else:
                days = (stay_range[1] - stay_range[0]).days
                st.session_state.temp_booking = {
                    "name": guest_name, "ic": guest_ic, "rooms": selected_rooms,
                    "days": days, "rate_override": custom_rate, "dates": stay_range
                }
                navigate('payment')
    if st.button("返回"): navigate('dashboard')

# 【付款页面 - 修复缺陷 12】
elif st.session_state.page == 'payment':
    st.title("账单结算中心")
    tb = st.session_state.temp_booking
    
    st.write(f"### 客人: {tb['name']} | 周期: {tb['days']} 晚")
    
    # 账单明细计算
    items = []
    total_room_fee = 0
    for r in tb['rooms']:
        price = tb['rate_override'] if tb['rate_override'] > 0 else st.session_state.rooms_db[r]['base_price']
        subtotal = price * tb['days']
        total_room_fee += subtotal
        items.append({"项目": f"房费 - 房间 {r}", "金额": subtotal})
    
    sst = total_room_fee * 0.06
    ttax = 10.0 * tb['days'] * len(tb['rooms'])
    deposit = 100.0
    
    items.append({"项目": "SST (6%)", "金额": sst})
    items.append({"项目": "旅游税 (TTax)", "金额": ttax})
    items.append({"项目": "可退押金", "金额": deposit})
    
    # 缺陷 12: 模拟其他杂费
    with st.expander("添加其他杂费 (Folio Items)"):
        extra_name = st.text_input("杂费项目名称")
        extra_amt = st.number_input("金额", min_value=0.0)
        if st.button("添加该项"):
            st.session_state.temp_booking.setdefault('extras', []).append({"项目": extra_name, "金额": extra_amt})
    
    # 合并杂费
    if 'extras' in tb:
        items.extend(tb['extras'])
    
    df_bill = pd.DataFrame(items)
    st.table(df_bill)
    final_total = df_bill["金额"].sum()
    st.markdown(f"## 应付总额: RM {final_total:.2f}")

    c1, c2, c3 = st.columns(3)
    if c1.button("✅ 确认支付成功"):
        # 更新房态
        for r in tb['rooms']:
            st.session_state.rooms_db[r]['status'] = "Dirty"
            st.session_state.rooms_db[r]['guest'] = tb['name']
        
        # 记录到历史
        tb['final_total'] = final_total
        st.session_state.bookings_history.append(tb)
        log_action(f"入住完成: {tb['name']} 租用房间 {tb['rooms']}")
        navigate('dashboard')
    if c2.button("❌ 支付失败"): navigate('dashboard')
    if c3.button("返回"): navigate('check_in')

# 【历史查询 - 修复缺陷 4】
elif st.session_state.page == 'history':
    st.title("历史订单查询")
    if not st.session_state.bookings_history:
        st.write("暂无历史记录")
    else:
        df_history = pd.DataFrame(st.session_state.bookings_history)
        st.dataframe(df_history[["name", "ic", "rooms", "days", "final_total"]])
    if st.button("返回"): navigate('dashboard')

# 【房态维护、审计、退房流程逻辑参考之前版本补齐...】
elif st.session_state.page == 'manage_rooms':
    st.title("房态维护")
    # 此处逻辑与之前一致...
    if st.button("返回"): navigate('dashboard')

elif st.session_state.page == 'audit':
    st.title("系统审计日志")
    st.table(pd.DataFrame(st.session_state.audit_logs).iloc[::-1])
    if st.button("返回"): navigate('dashboard')

elif st.session_state.page == 'check_out':
    st.title("办理退房")
    # ...退房逻辑...
    if st.button("返回"): navigate('dashboard')
