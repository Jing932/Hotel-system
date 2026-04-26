import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 初始化与样式配置 ---
st.set_page_config(page_title="Ultra PMS Luxury v3.0", layout="wide")

# 注入自定义 CSS
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { border-radius: 8px; transition: all 0.3s; font-weight: 500; }
    .status-card {
        background: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #3b82f6;
    }
    /* 隐藏 Streamlit 默认的列表样式 */
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

# 【控制台 - Dashboard】
if st.session_state.page == 'dashboard':
    st.title("🏨 智慧酒店云端管理平台")
    rooms = st.session_state.rooms_db
    
    # 修复：准确计算入住率
    occ_count = sum(1 for r in rooms.values() if r.get('guest') is not None)
    rev_total = sum(float(b.get('final_total', 0)) for b in st.session_state.bookings_history)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("今日入住率", f"{(occ_count/len(rooms))*100:.1f}%")
    c2.metric("当前住客", f"{occ_count} 人")
    c3.metric("累计总营收", f"RM {rev_total:.2f}")
    c4.metric("待清扫房间", f"{sum(1 for r in rooms.values() if r['status']=='Dirty')} 间")

    st.divider()
    
    # 房态矩阵
    rows = st.columns(5)
    for idx, (r_no, r_info) in enumerate(rooms.items()):
        with rows[idx % 5]:
            is_occ = r_info['guest'] is not None
            theme = {"bg": "#fee2e2", "border": "#ef4444", "text": "#b91c1c"} if is_occ else \
                    ({"bg": "#dcfce7", "border": "#22c55e", "text": "#15803d"} if r_info['status']=="Clean" else \
                     {"bg": "#ffedd5", "border": "#f97316", "text": "#c2410c"} if r_info['status']=="Dirty" else \
                     {"bg": "#f1f5f9", "border": "#64748b", "text": "#334155"})
            
            status_text = f"👤 {r_info['guest']}" if is_occ else r_info['status']
            st.markdown(f"""
                <div style="background:{theme['bg']}; padding:15px; border-radius:12px; border-left:6px solid {theme['border']}; margin-bottom:10px; min-height:85px;">
                    <span style="font-weight:bold; color:#1e293b;">房号: {r_no}</span><br>
                    <span style="color:{theme['text']}; font-size:0.9em; font-weight:600;">{status_text}</span>
                </div>
            """, unsafe_allow_html=True)

    st.write("")
    nav = st.columns(5)
    if nav[0].button("📝 登记入住", use_container_width=True, type="primary"): navigate('check_in')
    if nav[1].button("🔑 批量退房", use_container_width=True): navigate('check_out')
    if nav[2].button("🧹 房态维护", use_container_width=True): navigate('manage')
    if nav[3].button("📒 财务报表", use_container_width=True): navigate('history')
    if nav[4].button("📑 审计日志", use_container_width=True): navigate('audit')

# 【旅客登记】
elif st.session_state.page == 'check_in':
    st.title("📝 旅客登记入住")
    tb = st.session_state.temp_booking
    # 只筛选可用的干净房间
    can_use = [k for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and v['guest'] is None]
    
    with st.form("in_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("姓名", value=tb.get('name', ""))
        ic = col2.text_input("证件号码 (IC/护照)", value=tb.get('ic', ""))
        
        # 转换房号显示，去掉代码痕迹
        selected_rooms = st.multiselect("分配房间", can_use, default=[r for r in tb.get('rooms', []) if r in can_use])
        dates = st.date_input("预计入住周期", tb.get('dates', [date.today(), date.today() + timedelta(days=1)]))
        
        if st.form_submit_button("确认并生成账单"):
            if name and ic and selected_rooms and len(dates) == 2:
                st.session_state.temp_booking = {
                    "name": name, "ic": ic, 
                    "rooms": selected_rooms, 
                    "days": (dates[1]-dates[0]).days, 
                    "dates": dates
                }
                navigate('payment')
            else: st.error("⚠️ 请完整填写所有必填信息。")
    if st.button("取消并返回首页"): navigate('dashboard')

# 【结算支付 - 重点美化页】
elif st.session_state.page == 'payment':
    st.title("💳 结算支付确认")
    tb = st.session_state.get('temp_booking', {})
    
    if not tb or "rooms" not in tb:
        st.warning("⚠️ 暂无待处理订单，请重新登记。")
        if st.button("返回主页"): navigate('dashboard')
    else:
        # 去代码化处理：将列表 ['101', '102'] 转换为 "101, 102"
        rooms_display = ", ".join(tb['rooms'])
        
        with st.container(border=True):
            st.subheader(f"住客姓名: {tb['name']}")
            st.markdown(f"*分配房号:* {rooms_display}")
            st.markdown(f"*入住时长:* {tb['days']} 晚 ({tb['dates'][0]} 至 {tb['dates'][1]})")
            
            # 计算费用
            subtotal = sum(st.session_state.rooms_db[r]['base_price'] for r in tb['rooms']) * tb['days']
            tax = subtotal * 0.06
            ttax = 10.0 * tb['days'] * len(tb['rooms'])
            total = subtotal + tax + ttax + 100.0 # 100 押金
            
            st.markdown(f"<h2 style='color:#2563eb;'>待支付总额: RM {total:.2f}</h2>", unsafe_allow_html=True)
        
        st.write("")
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 支付成功", type="primary", use_container_width=True):
            # 执行更新逻辑
            for r in tb['rooms']:
                st.session_state.rooms_db[r]['guest'] = tb['name']
                st.session_state.rooms_db[r]['status'] = 'Dirty'
            
            tb['final_total'] = total
            st.session_state.bookings_history.append(tb.copy())
            log_event(f"入住办理成功: {tb['name']} (房号: {rooms_display})")
            
            # 重置登记信息，防止下一次登记时残留
            st.session_state.temp_booking = {} 
            st.success(f"入住办理成功！房间 {rooms_display} 已分配给 {tb['name']}。")
            if st.button("确认并返回主页"): navigate('dashboard')
            
        if c2.button("❌ 支付失败 (取消订单)", use_container_width=True):
            st.session_state.temp_booking = {} 
            navigate('dashboard')
        if c3.button("⬅️ 修改信息", use_container_width=True): navigate('check_in')

# 【批量退房】
elif st.session_state.page == 'check_out':
    st.title("🔑 批量退房办理")
    # 按客人分组房间
    guest_groups = {}
    for r_no, r_info in st.session_state.rooms_db.items():
        if r_info['guest']:
            name = r_info['guest']
            if name not in guest_groups: guest_groups[name] = []
            guest_groups[name].append(r_no)
    
    if not guest_groups:
        st.info("当前没有已登记的住客。")
        if st.button("返回首页"): navigate('dashboard')
    else:
        with st.form("checkout_form"):
            target = st.selectbox("选择办理退房的住客", list(guest_groups.keys()))
            rooms_to_free = guest_groups[target]
            # 友好显示房号
            rooms_str = ", ".join(rooms_to_free)
            
            st.warning(f"注意：该住客名下包含房间 {rooms_str}。")
            st.info("退房后，上述房间将自动转为“待清扫”状态。")
            
            if st.form_submit_button("确认结账并一键退房"):
                for r in rooms_to_free:
                    st.session_state.rooms_db[r]['guest'] = None
                    st.session_state.rooms_db[r]['status'] = 'Dirty'
                log_event(f"退房成功: {target} (释放房号: {rooms_str})")
                st.success(f"已成功为 {target} 办理退房。")
        if st.button("返回首页"): navigate('dashboard')

# 【房态维护】
elif st.session_state.page == 'manage':
    st.title("🧹 批量房态维护")
    all_rooms = list(st.session_state.rooms_db.keys())
    
    with st.form("m_form"):
        select_all = st.checkbox("全选所有房间")
        targets = st.multiselect("选择房号", all_rooms, default=all_rooms if select_all else [])
        new_status = st.select_slider("目标状态", options=["Clean", "Dirty", "OOO"])
        
        if st.form_submit_button("立即同步状态"):
            if targets:
                for r in targets:
                    # 安全锁：不能将有人住的房设为维修中
                    if st.session_state.rooms_db[r]['guest'] and new_status == "OOO": continue
                    st.session_state.rooms_db[r]['status'] = new_status
                log_event(f"房态更新: {targets} -> {new_status}")
                st.success("状态已批量更新。")
            else: st.warning("请至少选择一个房间。")
    if st.button("返回首页"): navigate('dashboard')

# --- 财务与审计页 ---
elif st.session_state.page == 'history':
    st.title("📒 历史财务报表")
    if st.session_state.bookings_history:
        df = pd.DataFrame(st.session_state.bookings_history)
        # 格式化日期和房号列，方便阅读
        df['rooms'] = df['rooms'].apply(lambda x: ", ".join(x))
        st.dataframe(df, use_container_width=True)
    else: st.info("暂无历史记录。")
    if st.button("返回"): navigate('dashboard')

elif st.session_state.page == 'audit':
    st.title("📑 系统审计日志")
    st.table(pd.DataFrame(st.session_state.audit_logs).iloc[::-1])
    if st.button("返回"): navigate('dashboard')
