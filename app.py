import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. 初始化系统配置 ---
st.set_page_config(page_title="酒店管理系统", layout="wide")

def init_pro_system():
    # 页面控制
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    
    # 房号管理 (缺陷修复 3, 4)
    if 'rooms_db' not in st.session_state:
        st.session_state.rooms_db = {
            "101": {"type": "大床房", "status": "Clean", "guest": None},
            "102": {"type": "大床房", "status": "Clean", "guest": None},
            "103": {"type": "大床房", "status": "Dirty", "guest": None},
            "201": {"type": "双床房", "status": "Clean", "guest": None},
            "202": {"type": "双床房", "status": "OOO", "guest": None},
        }
    
    # 审计与记录 (缺陷修复 6, 11, 12)
    if 'audit_logs' not in st.session_state:
        st.session_state.audit_logs = []
    if 'bookings' not in st.session_state:
        st.session_state.bookings = []
    if 'temp_booking' not in st.session_state:
        st.session_state.temp_booking = {}

init_pro_system()

# 常量定义 (缺陷修复 8)
ROOM_PRICES = {"大床房": 200, "双床房": 250}
SST_RATE = 0.06
TOUR_TAX = 10.0

def log_action(action):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.audit_logs.append(f"[{now}] {action}")

def navigate(page_name):
    st.session_state.page = page_name
    st.rerun()

# --- 2. 页面逻辑 ---

# 【控制台 - 修复缺陷 24】
if st.session_state.page == 'dashboard':
    st.title("🏨 酒店管理综合看板")
    
    st.subheader("实时房态")
    cols = st.columns(5)
    for i, (room, info) in enumerate(st.session_state.rooms_db.items()):
        status = info['status']
        icon = "✅" if status == "Clean" else "🧹" if status == "Dirty" else "🛠️"
        color = "green" if status == "Clean" else "red" if status == "Dirty" else "orange"
        with cols[i%5]:
            st.markdown(f"### {room}")
            st.markdown(f"{icon} :{color}[{status}]")
            if info['guest']: st.caption(f"👤 {info['guest']}")

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("新入住登记", use_container_width=True): navigate('check_in')
    if c2.button("办理退房", use_container_width=True): navigate('check_out')
    if c3.button("房态/维修维护", use_container_width=True, type="primary"): navigate('manage_rooms')
    if c4.button("审计日志", use_container_width=True): navigate('audit')

# 【入住登记 - 修复缺陷 3, 11, 12】
elif st.session_state.page == 'check_in':
    st.title("Check-in 登记")
    clean_rooms = [r for r, v in st.session_state.rooms_db.items() if v['status'] == "Clean"]
    
    if not clean_rooms:
        st.error("没有可用的清洁房间，请先维护房态。")
        if st.button("返回"): navigate('dashboard')
    else:
        name = st.text_input("客人姓名")
        ic = st.text_input("IC 编号")
        selected_room = st.selectbox("分配房号", clean_rooms)
        duration = st.number_input("入住天数", min_value=1, step=1, value=1)
        
        col_btn = st.columns(2)
        if col_btn[0].button("返回"): navigate('dashboard')
        if col_btn[1].button("下一步: 结算"):
            if name and ic:
                st.session_state.temp_booking = {
                    "name": name, "ic": ic, "room": selected_room, 
                    "days": duration, "type": st.session_state.rooms_db[selected_room]['type']
                }
                navigate('payment')
            else:
                st.warning("请完整填写资料")

# 【支付界面 - 修复缺陷 8, 16, 25】
elif st.session_state.page == 'payment':
    st.title("费用结算与支付")
    tb = st.session_state.temp_booking
    price = ROOM_PRICES[tb['type']]
    
    room_charge = price * tb['days']
    sst = room_charge * SST_RATE
    ttax = TOUR_TAX * tb['days']
    deposit = 100.0
    
    st.write(f"*房费总计:* RM {room_charge}")
    st.write(f"*SST (6%):* RM {sst:.2f}")
    st.write(f"*旅游税:* RM {ttax}")
    st.write(f"*押金 (可退):* RM {deposit}")
    total = room_charge + sst + ttax + deposit
    st.subheader(f"应付总额: RM {total:.2f}")
    
    c = st.columns(3)
    if c[0].button("返回修改"): navigate('check_in')
    if c[1].button("✅ 确认支付成功", type="primary"):
        st.session_state.rooms_db[tb['room']]['status'] = "Dirty"
        st.session_state.rooms_db[tb['room']]['guest'] = tb['name']
        tb['final_total'] = total
        st.session_state.bookings.append(tb)
        log_action(f"入住完成: {tb['name']} 房号 {tb['room']}")
        st.success("办理成功！")
        if st.button("返回主页"): navigate('dashboard')
    if c[2].button("❌ 支付失败"):
        log_action(f"支付失败记录: {tb['name']}")
        navigate('dashboard')

# 【退房流程 - 修复缺陷 13, 14, 16】
elif st.session_state.page == 'check_out':
    st.title("退房办理")
    occupied = [r for r, v in st.session_state.rooms_db.items() if v['guest']]
    if not occupied:
        st.info("当前无入住客人")
        if st.button("返回"): navigate('dashboard')
    else:
        target = st.selectbox("选择退房房间", occupied)
        late = st.checkbox("是否存在延迟退房费? (RM 100)")
        if st.button("确认退房并释放房间"):
            guest = st.session_state.rooms_db[target]['guest']
            st.session_state.rooms_db[target]['status'] = "Dirty"
            st.session_state.rooms_db[target]['guest'] = None
            log_action(f"退房成功: {target} (客人: {guest}, 延迟费: {late})")
            navigate('dashboard')

# 【房态维护 - 满足额外需求】
elif st.session_state.page == 'manage_rooms':
    st.title("房态维护")
    rm = st.selectbox("选择房号", list(st.session_state.rooms_db.keys()))
    new_stat = st.selectbox("新状态", ["Clean", "Dirty", "OOO"])
    if st.button("保存修改"):
        st.session_state.rooms_db[rm]['status'] = new_stat
        log_action(f"手动修改房态: {rm} -> {new_stat}")
        navigate('dashboard')
    if st.button("取消"): navigate('dashboard')

# 【审计日志 - 修复缺陷 6】
elif st.session_state.page == 'audit':
    st.title("系统审计日志")
    st.table(pd.DataFrame(st.session_state.audit_logs, columns=["操作记录"]).iloc[::-1])
    if st.button("返回控制台"): navigate('dashboard')
