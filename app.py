import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 核心初始化 (防止变量引用错误) ---
st.set_page_config(page_title="Ultra PMS Pro", layout="wide")

def safety_init():
    """全量初始化，确保任何时候引用变量都有默认值"""
    defaults = {
        'page': 'dashboard',
        'rooms_db': {
            "101": {"type": "大床房", "base_price": 200.0, "status": "Clean", "guest": None},
            "102": {"type": "大床房", "base_price": 200.0, "status": "Clean", "guest": None},
            "103": {"type": "大床房", "base_price": 200.0, "status": "Dirty", "guest": None},
            "201": {"type": "双床房", "base_price": 250.0, "status": "Clean", "guest": None},
            "202": {"type": "双床房", "base_price": 250.0, "status": "OOO", "guest": None},
        },
        'bookings_history': [],
        'audit_logs': [],
        'temp_booking': {}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

safety_init()

# --- 2. 工具函数 ---
def navigate(target_page):
    st.session_state.page = target_page
    st.rerun()

def log_event(msg):
    now = datetime.now().strftime("%H:%M:%S")
    st.session_state.audit_logs.append({"时间": now, "描述": msg})

# --- 3. 页面渲染 ---

# 【Dashboard 仪表盘】
if st.session_state.page == 'dashboard':
    st.title("🏨 智慧酒店管理系统")
    
    # 修复入住率逻辑：只看真正住人的房
    all_rooms = st.session_state.rooms_db
    occupied_count = sum(1 for r in all_rooms.values() if r.get('guest') is not None)
    occ_rate = (occupied_count / len(all_rooms)) * 100
    
    # 指标栏
    c1, c2, c3 = st.columns(3)
    c1.metric("今日入住率", f"{occ_rate:.1f}%")
    c2.metric("当前住客数", f"{occupied_count} 人")
    c3.metric("累计营收", f"RM {sum(b.get('final_total', 0) for b in st.session_state.bookings_history):.2f}")

    st.divider()
    
    # 房态矩阵
    st.subheader("实时房态矩阵")
    rows = st.columns(5)
    for idx, (r_no, r_info) in enumerate(all_rooms.items()):
        with rows[idx % 5]:
            # 状态判定颜色
            is_occupied = r_info.get('guest') is not None
            status = r_info.get('status', 'Dirty')
            
            if is_occupied:
                color, label = "#fee2e2", f"👤 {r_info['guest']}"
            elif status == "Clean":
                color, label = "#dcfce7", "✅ 可入住"
            elif status == "Dirty":
                color, label = "#ffedd5", "🧹 待清扫"
            else:
                color, label = "#f1f5f9", "🛠️ 维修中"
                
            st.markdown(f"""
                <div style="background:{color}; padding:15px; border-radius:10px; border:1px solid #ddd;">
                    <b style="font-size:1.2em;">{r_no}</b> <small>({r_info['type']})</small><br>
                    <hr style="margin:8px 0">
                    <span style="font-weight:600;">{label}</span>
                </div>
            """, unsafe_allow_html=True)

    st.write("")
    # 底部导航
    nav = st.columns(5)
    if nav[0].button("📝 登记入住", use_container_width=True): navigate('check_in')
    if nav[1].button("🔑 办理退房", use_container_width=True): navigate('check_out')
    if nav[2].button("🧹 房态维护", use_container_width=True): navigate('manage')
    if nav[3].button("📒 财务报表", use_container_width=True): navigate('history')
    if nav[4].button("📑 审计日志", use_container_width=True): navigate('audit')

# 【入住登记】
elif st.session_state.page == 'check_in':
    st.title("新客入住登记")
    # 防错：只筛选真正空闲且干净的房
    can_use = [k for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and v['guest'] is None]
    
    if not can_use:
        st.warning("🚨 当前没有可入住的干净房间！请先前往“房态维护”清理房间。")
        if st.button("返回控制台"): navigate('dashboard')
    else:
        with st.form("in_form"):
            name = st.text_input("客人姓名", key="in_name")
            ic = st.text_input("IC/护照号", key="in_ic")
            selected = st.multiselect("分配房号", can_use)
            dates = st.date_input("入住周期", [date.today(), date.today() + timedelta(days=1)])
            
            if st.form_submit_button("确认并计算费用"):
                if name and ic and selected and len(dates) == 2:
                    st.session_state.temp_booking = {
                        "name": name, "ic": ic, "rooms": selected,
                        "days": (dates[1]-dates[0]).days, "dates": dates
                    }
                    navigate('payment')
                else:
                    st.error("请完整填写所有信息。")
    if st.button("取消返回"): navigate('dashboard')

# 【费用支付】
elif st.session_state.page == 'payment':
    st.title("账单确认")
    tb = st.session_state.get('temp_booking', {})
    
    # 防错检查：如果刷新导致 temp_booking 为空，导回首页
    if not tb or "rooms" not in tb:
        st.error("会话数据丢失，请重新登记。")
        if st.button("回到首页"): navigate('dashboard')
    else:
        # 计算逻辑加固
        subtotal = 0.0
        for r in tb['rooms']:
            subtotal += st.session_state.rooms_db[r]['base_price'] * tb['days']
        
        sst = subtotal * 0.06
        ttax = 10.0 * tb['days'] * len(tb['rooms'])
        total = subtotal + sst + ttax + 100.0 # 100是固定押金
        
        # 账单表格展示
        bill_df = pd.DataFrame([
            {"项目": "房费小计", "金额": f"RM {subtotal:.2f}"},
            {"项目": "SST (6%)", "金额": f"RM {sst:.2f}"},
            {"项目": "旅游税", "金额": f"RM {ttax:.2f}"},
            {"项目": "可退押金", "金额": "RM 100.00"},
            {"项目": "总计应付", "金额": f"RM {total:.2f}"}
        ])
        st.table(bill_df)
        
        if st.button("✅ 确认支付并完成入住", type="primary"):
            for r in tb['rooms']:
                st.session_state.rooms_db[r]['guest'] = tb['name']
                st.session_state.rooms_db[r]['status'] = 'Dirty'
            
            # 存入历史记录
            tb['final_total'] = total
            st.session_state.bookings_history.append(tb)
            log_event(f"入住办理: {tb['name']} 房间: {tb['rooms']}")
            st.success("办理完成！")
            st.session_state.temp_booking = {} # 清空临时变量
            if st.button("完成"): navigate('dashboard')

# 【退房/房态/历史逻辑同样加固实现...】
elif st.session_state.page == 'manage':
    st.title("房态维护")
    target = st.selectbox("选择房间", list(st.session_state.rooms_db.keys()))
    new_s = st.selectbox("设置状态", ["Clean", "Dirty", "OOO"])
    if st.button("提交更改"):
        st.session_state.rooms_db[target]['status'] = new_s
        log_event(f"手动修改房态: {target} -> {new_s}")
        navigate('dashboard')
    if st.button("返回"): navigate('dashboard')

elif st.session_state.page == 'history':
    st.title("历史订单报表")
    if st.session_state.bookings_history:
        st.write(pd.DataFrame(st.session_state.bookings_history))
    else:
        st.info("暂无成交记录")
    if st.button("返回"): navigate('dashboard')

elif st.session_state.page == 'audit':
    st.title("审计日志")
    st.table(pd.DataFrame(st.session_state.audit_logs).iloc[::-1])
    if st.button("返回"): navigate('dashboard')

elif st.session_state.page == 'check_out':
    st.title("办理退房")
    occupants = {k: v['guest'] for k, v in st.session_state.rooms_db.items() if v['guest']}
    if not occupants:
        st.info("当前无住客。")
    else:
        r_out = st.selectbox("选择退房房间", list(occupants.keys()))
        if st.button("确认退房"):
            name = occupants[r_out]
            st.session_state.rooms_db[r_out]['guest'] = None
            st.session_state.rooms_db[r_out]['status'] = 'Dirty'
            log_event(f"退房办理: {name} 房号: {r_out}")
            navigate('dashboard')
    if st.button("返回"): navigate('dashboard')
