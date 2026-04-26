import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 初始化与样式配置 ---
st.set_page_config(page_title="Ultra PMS Luxury v3.0", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { border-radius: 8px; transition: all 0.3s; }
    .status-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)

def safety_init():
    if 'page' not in st.session_state: st.session_state.page = 'dashboard'
    if 'rooms_db' not in st.session_state:
        st.session_state.rooms_db = {
            "101": {"type": "大床房", "base_price": 200.0, "status": "Clean", "guest": None},
            "102": {"type": "大床房", "base_price": 200.0, "status": "Clean", "guest": None},
            "103": {"type": "大床房", "base_price": 200.0, "status": "Dirty", "guest": None},
            "201": {"type": "双床房", "base_price": 250.0, "status": "Clean", "guest": None},
            "202": {"type": "双床房", "base_price": 250.0, "status": "OOO", "guest": None},
        }
    if 'bookings_history' not in st.session_state: st.session_state.bookings_history = []
    if 'audit_logs' not in st.session_state: st.session_state.audit_logs = []
    if 'temp_booking' not in st.session_state: st.session_state.temp_booking = {}

safety_init()

def navigate(target):
    st.session_state.page = target
    st.rerun()

def log_event(msg):
    now = datetime.now().strftime("%H:%M:%S")
    st.session_state.audit_logs.append({"时间": now, "描述": msg})

# --- 2. 页面渲染逻辑 ---

# 【控制台】
if st.session_state.page == 'dashboard':
    st.title("🏨 智慧酒店云端管理平台")
    rooms = st.session_state.rooms_db
    occ_count = sum(1 for r in rooms.values() if r['guest'] is not None)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("今日入住率", f"{(occ_count/len(rooms))*100:.1f}%")
    c2.metric("当前住客", f"{occ_count} 人")
    c3.metric("总营收", f"RM {sum(b.get('final_total',0) for b in st.session_state.bookings_history):.2f}")
    c4.metric("待清扫", f"{sum(1 for r in rooms.values() if r['status']=='Dirty')} 间")

    st.divider()
    st.subheader("实时房态矩阵")
    rows = st.columns(5)
    for idx, (r_no, r_info) in enumerate(rooms.items()):
        with rows[idx % 5]:
            is_occ = r_info['guest'] is not None
            theme = {"bg": "#fee2e2", "border": "#ef4444", "text": "#b91c1c"} if is_occ else \
                    ({"bg": "#dcfce7", "border": "#22c55e", "text": "#15803d"} if r_info['status']=="Clean" else \
                     {"bg": "#ffedd5", "border": "#f97316", "text": "#c2410c"} if r_info['status']=="Dirty" else \
                     {"bg": "#f1f5f9", "border": "#64748b", "text": "#334155"})
            st.markdown(f"""<div style="background:{theme['bg']}; padding:15px; border-radius:12px; border-left:6px solid {theme['border']}; margin-bottom:10px;">
                <span style="font-weight:bold;">{r_no}</span> <small>({r_info['type']})</small><br>
                <span style="color:{theme['text']}; font-size:0.9em; font-weight:600;">{f"👤 {r_info['guest']}" if is_occ else r_info['status']}</span>
                </div>""", unsafe_allow_html=True)

    st.write("")
    nav = st.columns(5)
    if nav[0].button("📝 登记入住", use_container_width=True, type="primary"): navigate('check_in')
    if nav[1].button("🔑 批量退房", use_container_width=True): navigate('check_out')
    if nav[2].button("🧹 房态维护", use_container_width=True): navigate('manage')
    if nav[3].button("📒 财务报表", use_container_width=True): navigate('history')
    if nav[4].button("📑 审计日志", use_container_width=True): navigate('audit')

# 【旅客登记 - 修复：自动重置信息】
elif st.session_state.page == 'check_in':
    st.title("📝 旅客登记入住")
    tb = st.session_state.temp_booking
    can_use = [k for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and v['guest'] is None]
    
    with st.form("in_form"):
        col1, col2 = st.columns(2)
        # 如果是支付成功后重回此页，tb已清空，这些值将自动变为初始状态
        name = col1.text_input("姓名", value=tb.get('name', ""))
        ic = col2.text_input("IC/护照", value=tb.get('ic', ""))
        
        rs = st.multiselect("分配房号", can_use, default=[r for r in tb.get('rooms', []) if r in can_use])
        ds = st.date_input("入住日期", tb.get('dates', [date.today(), date.today() + timedelta(days=1)]))
        
        if st.form_submit_button("生成账单确认"):
            if name and ic and rs and len(ds) == 2:
                st.session_state.temp_booking = {"name": name, "ic": ic, "rooms": rs, "days": (ds[1]-ds[0]).days, "dates": ds}
                navigate('payment')
            else: st.error("请完整填资料")
    if st.button("返回控制台"): navigate('dashboard')

# 【账单支付 - 修复：成功后清空数据】
elif st.session_state.page == 'payment':
    st.title("💳 结算支付")
    tb = st.session_state.get('temp_booking', {})
    
    if not tb:
        st.warning("数据已过期")
        if st.button("回到主页"): navigate('dashboard')
    else:
        with st.container(border=True):
            subtotal = sum(st.session_state.rooms_db[r]['base_price'] for r in tb['rooms']) * tb['days']
            tax = subtotal * 0.06
            ttax = 10.0 * tb['days'] * len(tb['rooms'])
            total = subtotal + tax + ttax + 100.0
            st.markdown(f"### 待支付总额: RM {total:.2f}")
            st.write(f"客人: {tb['name']} | 房间: {tb['rooms']}")
        
        st.write("")
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 支付成功", type="primary", use_container_width=True):
            for r in tb['rooms']:
                st.session_state.rooms_db[r]['guest'] = tb['name']
                st.session_state.rooms_db[r]['status'] = 'Dirty'
            tb['final_total'] = total
            st.session_state.bookings_history.append(tb.copy())
            log_event(f"入住: {tb['name']} (房号: {tb['rooms']})")
            
            # --- 核心改进：彻底重置 temp_booking 确保下次登记无残留 ---
            st.session_state.temp_booking = {} 
            st.success("办理成功！系统已自动重置登记表单。")
            if st.button("点此返回首页"): navigate('dashboard')
            
        if c2.button("❌ 支付失败 (取消订单)", use_container_width=True):
            st.session_state.temp_booking = {} 
            navigate('dashboard')
        if c3.button("⬅️ 返回修改", use_container_width=True): navigate('check_in')

# 【批量退房 - 修复：按住客选择所有关联房间】
elif st.session_state.page == 'check_out':
    st.title("🔑 批量退房结算")
    # 提取当前所有在住客人的名单及其房间
    guest_map = {}
    for r_no, r_info in st.session_state.rooms_db.items():
        if r_info['guest']:
            g_name = r_info['guest']
            if g_name not in guest_map: guest_map[g_name] = []
            guest_map[g_name].append(r_no)
    
    if not guest_map:
        st.info("当前没有任何旅客在住。")
        if st.button("返回"): navigate('dashboard')
    else:
        with st.container(border=True):
            target_guest = st.selectbox("选择要办理退房的住客", list(guest_map.keys()))
            associated_rooms = guest_map[target_guest]
            st.warning(f"该住客名下共有房间: {', '.join(associated_rooms)}")
            st.write("点击下方按钮将一键结算所有房间并将状态设为待清扫。")
            
            if st.button("确认结账并退回所有房间", type="primary", use_container_width=True):
                for r in associated_rooms:
                    st.session_state.rooms_db[r]['guest'] = None
                    st.session_state.rooms_db[r]['status'] = 'Dirty'
                log_event(f"批量退房: 客人 {target_guest} 释放房间 {associated_rooms}")
                st.success(f"退房成功！房间 {associated_rooms} 已转为待清扫状态。")
                if st.button("完成"): navigate('dashboard')
    if st.button("返回首页"): navigate('dashboard')

# 【批量房态维护 - 保持全选功能】
elif st.session_state.page == 'manage':
    st.title("🧹 批量房态管理")
    all_rooms = list(st.session_state.rooms_db.keys())
    with st.container(border=True):
        if st.checkbox("选择全部房间"):
            targets = st.multiselect("房号", all_rooms, default=all_rooms)
        else:
            targets = st.multiselect("手动选择房号", all_rooms)
        new_s = st.select_slider("目标状态", options=["Clean", "Dirty", "OOO"])
        if st.button("立即应用"):
            for r in targets:
                if st.session_state.rooms_db[r]['guest'] and new_s == "OOO": continue
                st.session_state.rooms_db[r]['status'] = new_s
            log_event(f"批量维护: {targets} -> {new_s}")
            st.success("更新成功")
    if st.button("返回"): navigate('dashboard')

# 【其他页面】
elif st.session_state.page == 'history':
    st.title("财务报表")
    if st.session_state.bookings_history: st.dataframe(pd.DataFrame(st.session_state.bookings_history), use_container_width=True)
    if st.button("返回"): navigate('dashboard')

elif st.session_state.page == 'audit':
    st.title("审计日志")
    st.table(pd.DataFrame(st.session_state.audit_logs).iloc[::-1])
    if st.button("返回"): navigate('dashboard')
