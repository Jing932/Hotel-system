import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 初始化与样式配置 ---
st.set_page_config(page_title="Ultra PMS Luxury Edition", layout="wide")

# 自定义 CSS：提升视觉高级感
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { border-radius: 8px; transition: all 0.3s; border: none; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .status-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-left: 5px solid #3b82f6;
    }
    div[data-testid="stExpander"] { border: none; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
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

# 【Dashboard：极致美化版】
if st.session_state.page == 'dashboard':
    st.title("🏨 智慧酒店云端管理平台")
    
    # 数据统计
    rooms = st.session_state.rooms_db
    occ_count = sum(1 for r in rooms.values() if r['guest'] is not None)
    total_rev = sum(b.get('final_total',0) for b in st.session_state.bookings_history)
    
    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("今日入住率", f"{(occ_count/len(rooms))*100:.1f}%")
        c2.metric("当前住客", f"{occ_count} 人")
        c3.metric("累计营收", f"RM {total_rev:.2f}")
        c4.metric("待清扫房间", f"{sum(1 for r in rooms.values() if r['status']=='Dirty')} 间")

    st.divider()
    
    # 房态矩阵：使用更精致的 HTML 卡片
    st.subheader("实时房态矩阵")
    rows = st.columns(5)
    for idx, (r_no, r_info) in enumerate(rooms.items()):
        with rows[idx % 5]:
            is_occ = r_info['guest'] is not None
            # 颜色主题：Occupied(红), Clean(绿), Dirty(橙), OOO(灰)
            theme = {"bg": "#fee2e2", "border": "#ef4444", "text": "#b91c1c"} if is_occ else \
                    ({"bg": "#dcfce7", "border": "#22c55e", "text": "#15803d"} if r_info['status']=="Clean" else \
                     {"bg": "#ffedd5", "border": "#f97316", "text": "#c2410c"} if r_info['status']=="Dirty" else \
                     {"bg": "#f1f5f9", "border": "#64748b", "text": "#334155"})
            
            label = f"👤 {r_info['guest']}" if is_occ else (r_info['status'])
            st.markdown(f"""
                <div style="background:{theme['bg']}; padding:15px; border-radius:12px; border-left:6px solid {theme['border']}; margin-bottom:10px;">
                    <span style="font-size:1.1em; font-weight:bold; color:#1e293b;">{r_no}</span> 
                    <span style="font-size:0.7em; color:#64748b;">({r_info['type']})</span><br>
                    <span style="font-weight:600; color:{theme['text']}; font-size:0.9em;">{label}</span>
                </div>
            """, unsafe_allow_html=True)

    st.write("")
    # 导航栏：大图标按钮
    nav = st.columns(5)
    if nav[0].button("📝 登记入住", use_container_width=True, type="primary"): navigate('check_in')
    if nav[1].button("🔑 办理退房", use_container_width=True): navigate('check_out')
    if nav[2].button("🧹 批量维护", use_container_width=True): navigate('manage')
    if nav[3].button("📒 财务报表", use_container_width=True): navigate('history')
    if nav[4].button("📑 审计日志", use_container_width=True): navigate('audit')

# 【批量房态维护：一键全选功能】
elif st.session_state.page == 'manage':
    st.title("🧹 批量房态管理中心")
    st.info("此模块用于保洁部或工程部快速批量切换房间状态。")
    
    all_room_nos = list(st.session_state.rooms_db.keys())
    
    with st.container(border=True):
        st.subheader("1. 选择目标房间")
        col_sel1, col_sel2 = st.columns([1, 4])
        
        # 功能：一键全选
        select_all = col_sel1.checkbox("选择全部房间")
        if select_all:
            targets = st.multiselect("已选择的房号", all_room_nos, default=all_room_nos)
        else:
            targets = st.multiselect("手动选择房号", all_room_nos)
            
        st.subheader("2. 设定新状态")
        new_status = st.select_slider(
            "滑动选择状态",
            options=["Clean", "Dirty", "OOO"],
            value="Clean"
        )
        
        st.write("")
        if st.button("🚀 立即应用更改", use_container_width=True, type="primary"):
            if targets:
                for r in targets:
                    # 业务保护：如果有人住，不能改为 OOO
                    if st.session_state.rooms_db[r]['guest'] and new_status == "OOO":
                        st.warning(f"房间 {r} 目前有人住，已跳过维修设置。")
                        continue
                    st.session_state.rooms_db[r]['status'] = new_status
                log_event(f"批量修改房态: {targets} -> {new_status}")
                st.success(f"成功！已将所选房间状态同步为: {new_status}")
            else:
                st.error("请先选择房间！")
                
    if st.button("完成操作并返回控制台"): navigate('dashboard')

# 【账单确认：返回修改与失败重置逻辑】
elif st.session_state.page == 'payment':
    st.title("💳 账单结算结算确认")
    tb = st.session_state.get('temp_booking', {})
    
    if not tb or "rooms" not in tb:
        st.warning("⚠️ 会话已过期或数据丢失。")
        if st.button("回到首页"): navigate('dashboard')
    else:
        # 详细账单显示
        with st.container(border=True):
            st.markdown(f"### 客户：{tb['name']}")
            st.write(f"房号：{tb['rooms']} | 周期：{tb['dates'][0]} 至 {tb['dates'][1]} ({tb['days']}晚)")
            
            subtotal = sum(st.session_state.rooms_db[r]['base_price'] for r in tb['rooms']) * tb['days']
            tax = subtotal * 0.06
            ttax = 10.0 * tb['days'] * len(tb['rooms'])
            deposit = 100.0
            total = subtotal + tax + ttax + deposit
            
            # 美化的账单表格
            bill_data = {
                "明细项目": ["房费小计", "SST (6%)", "旅游税", "预收押金"],
                "金额 (RM)": [f"{subtotal:.2f}", f"{tax:.2f}", f"{ttax:.2f}", f"{deposit:.2f}"]
            }
            st.table(pd.DataFrame(bill_data))
            st.markdown(f"<h2 style='text-align:right; color:#1e293b;'>实付总计: RM {total:.2f}</h2>", unsafe_allow_html=True)
        
        st.write("")
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 支付成功并入住", type="primary", use_container_width=True):
            for r in tb['rooms']:
                st.session_state.rooms_db[r]['guest'] = tb['name']
                st.session_state.rooms_db[r]['status'] = 'Dirty'
            tb['final_total'] = total
            st.session_state.bookings_history.append(tb.copy())
            log_event(f"入住成功: {tb['name']} -> {tb['rooms']}")
            # 支付成功后不立即清空，确保下一页渲染不报错，而在 safety_init 中由逻辑覆盖
            navigate('dashboard')
            
        if c2.button("❌ 支付失败 (取消订单)", use_container_width=True):
            log_event(f"支付中断: {tb['name']}")
            st.session_state.temp_booking = {} 
            navigate('dashboard')
            
        if c3.button("⬅️ 返回修改日期/资料", use_container_width=True):
            navigate('check_in')

# --- 其余页面代码逻辑补全 ---
elif st.session_state.page == 'check_in':
    st.title("旅客登记")
    tb = st.session_state.temp_booking
    can_use = [k for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and v['guest'] is None]
    
    with st.form("in_form"):
        col_a, col_b = st.columns(2)
        n = col_a.text_input("姓名", value=tb.get('name', ""))
        i = col_b.text_input("IC/护照", value=tb.get('ic', ""))
        
        prev_r = [r for r in tb.get('rooms', []) if r in can_use]
        rs = st.multiselect("选择房号", can_use, default=prev_r)
        
        d_val = tb.get('dates', [date.today(), date.today() + timedelta(days=1)])
        ds = st.date_input("选择日期", d_val)
        
        if st.form_submit_button("下一步：确认账单"):
            if n and i and rs and len(ds) == 2:
                st.session_state.temp_booking = {"name": n, "ic": i, "rooms": rs, "days": (ds[1]-ds[0]).days, "dates": ds}
                navigate('payment')
            else: st.error("资料不全")
    if st.button("返回"): navigate('dashboard')

elif st.session_state.page == 'check_out':
    st.title("办理退房")
    occ = {k: v['guest'] for k, v in st.session_state.rooms_db.items() if v['guest']}
    if occ:
        r = st.selectbox("选择房间", list(occ.keys()))
        if st.button("确认结账并退房"):
            st.session_state.rooms_db[r]['guest'] = None
            st.session_state.rooms_db[r]['status'] = 'Dirty'
            log_event(f"退房成功: {r}")
            navigate('dashboard')
    else: st.info("当前无住客")
    if st.button("返回"): navigate('dashboard')

elif st.session_state.page == 'audit':
    st.title("系统审计")
    st.table(pd.DataFrame(st.session_state.audit_logs).iloc[::-1])
    if st.button("返回"): navigate('dashboard')

elif st.session_state.page == 'history':
    st.title("财务统计")
    if st.session_state.bookings_history: st.dataframe(pd.DataFrame(st.session_state.bookings_history), use_container_width=True)
    if st.button("返回"): navigate('dashboard')
