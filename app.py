import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 初始化与样式 ---
st.set_page_config(page_title="Executive PMS v4.2", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f1f5f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.2em; font-weight: 600; }
    .room-card {
        padding: 20px; border-radius: 15px; background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 8px solid #ddd;
        margin-bottom: 15px; min-height: 130px;
    }
    .bill-header { background-color: #1e293b; color: white; padding: 15px; border-radius: 10px 10px 0 0; }
    .bill-body { background-color: white; padding: 20px; border: 1px solid #e2e8f0; border-radius: 0 0 10px 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO", "guest": None},
    }
    st.session_state.update({'page': 'home', 'history': [], 'audit_logs': [], 'temp': {}, 'paid': False})

def navigate_to(target):
    st.session_state.page = target
    st.rerun()

def add_audit(action, detail):
    """原子级审计记录"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.audit_logs.append({"时间": now, "操作": action, "详情": detail})

# --- 2. 页面逻辑 ---

# 【主页：房态中心】
if st.session_state.page == 'home':
    st.session_state.paid = False
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    rooms = st.session_state.rooms_db
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("入住率", f"{(sum(1 for r in rooms.values() if r['guest'])/len(rooms))*100:.1f}%")
    c3.metric("营收总计", f"RM {sum(h.get('total',0) for h in st.session_state.history):.2f}")
    
    st.divider()
    room_cols = st.columns(5)
    for idx, (no, info) in enumerate(rooms.items()):
        with room_cols[idx % 5]:
            is_occ = info['guest'] is not None
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316" if info['status']=="Dirty" else "#64748b")
            st.markdown(f"""<div class="room-card" style="border-top-color: {color};">
                <div style="font-size:1.3em;font-weight:800;">{no} <small style="font-weight:400;font-size:0.6em;">{info['type']}</small></div>
                <div style="color:{color};font-weight:700;margin-top:10px;">{f"👤 {info['guest']}" if is_occ else info['status']}</div>
                </div>""", unsafe_allow_html=True)

    st.write("")
    nav_btns = st.columns(5)
    if nav_btns[0].button("📝 入住登记", type="primary"): navigate_to('in')
    if nav_btns[1].button("🔑 批量退房"): navigate_to('out')
    if nav_btns[2].button("🧹 批量维护"): navigate_to('batch')
    if nav_btns[3].button("📊 财务与审计"): navigate_to('report')

# 【入住登记】
elif st.session_state.page == 'in':
    st.title("旅客登记")
    can_use = {k: f"{k} ({v['type']})" for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    with st.form("in_f"):
        c1, c2 = st.columns(2)
        name, ic = c1.text_input("姓名"), c2.text_input("证件号")
        rs = st.multiselect("选择房号", options=list(can_use.keys()), format_func=lambda x: can_use[x])
        ds = st.date_input("入住与离店日期", [date.today(), date.today() + timedelta(1)])
        if st.form_submit_button("核算账单"):
            if name and rs and len(ds) == 2 and (ds[1]-ds[0]).days > 0:
                st.session_state.temp = {"name": name, "ic": ic, "rs": rs, "days": (ds[1]-ds[0]).days, "checkin": ds[0], "checkout": ds[1]}
                navigate_to('pay')
            else: st.error("请完整填写，且日期有效")
    if st.button("返回首页"): navigate_to('home')

# 【账单确认：表格累加明细】
elif st.session_state.page == 'pay':
    st.title("结算确认")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("✅ 支付成功!")
        if st.button("回到主页"): st.session_state.temp = {}; navigate_to('home')
    else:
        # 构造发票明细表格
        bill_items = []
        total_base = 0
        for r in t['rs']:
            info = st.session_state.rooms_db[r]
            sub = info['price'] * t['days']
            bill_items.append({"房号": f"{r} ({info['type']})", "单价": f"RM {info['price']}", "天数": t['days'], "小计金额": f"RM {sub:.2f}"})
            total_base += sub
        
        sst, ttax = total_base * 0.06, 10.0 * len(t['rs']) * t['days']
        grand_total = total_base + sst + ttax + 100.0

        st.markdown(f"""<div class="bill-header"><b>住宿预订详情清单</b></div>""", unsafe_allow_html=True)
        with st.container():
            st.markdown(f"""<div class="bill-body">
                <p><b>住客姓名:</b> {t['name']} &nbsp;&nbsp; | &nbsp;&nbsp; <b>证件号:</b> {t['ic']}</p>
                <p><b>入住日期:</b> {t['checkin']} &nbsp;&nbsp; | &nbsp;&nbsp; <b>退房日期:</b> {t['checkout']} &nbsp;&nbsp; | &nbsp;&nbsp; <b>共计:</b> {t['days']} 晚</p>
                </div>""", unsafe_allow_html=True)
            
            st.table(pd.DataFrame(bill_items)) # 费用表格
            
            c1, c2 = st.columns([2,1])
            with c2:
                st.write(f"房费总额: RM {total_base:.2f}")
                st.write(f"政府税 (SST 6%): RM {sst:.2f}")
                st.write(f"旅游税: RM {ttax:.2f}")
                st.write(f"押金 (Deposit): RM 100.00")
                st.markdown(f"### 应收总额: RM {grand_total:.2f}")

        col_p1, col_p2, col_p3 = st.columns(3)
        if col_p1.button("✅ 确认支付成功", type="primary"):
            for r in t['rs']: st.session_state.rooms_db[r].update({"guest": t['name'], "status": "Dirty"})
            st.session_state.history.append({**t, "total": grand_total, "rooms_str": ", ".join(t['rs'])})
            add_audit("登记入住", f"住客: {t['name']} | 房间: {', '.join(t['rs'])} | 金额: RM {grand_total:.2f}")
            st.session_state.paid = True
            st.rerun()
        if col_p2.button("❌ 取消"): navigate_to('home')
        if col_p3.button("⬅️ 返回修改"): navigate_to('in')

# 【批量退房：审计集成】
elif st.session_state.page == 'out':
    st.title("🔑 批量退房管理")
    g_map = {info['guest']: [] for info in st.session_state.rooms_db.values() if info['guest']}
    for r, info in st.session_state.rooms_db.items():
        if info['guest']: g_map[info['guest']].append(f"{r}({info['type']})")
    
    if g_map:
        target = st.selectbox("选择住客", list(g_map.keys()))
        if st.button("确认结账", type="primary"):
            rooms_to_free = []
            for r_str in g_map[target]:
                r_no = r_str.split("(")[0]
                st.session_state.rooms_db[r_no].update({"guest": None, "status": "Dirty"})
                rooms_to_free.append(r_no)
            add_audit("办理退房", f"住客: {target} | 释放房间: {', '.join(rooms_to_free)}")
            st.success("退房完成"); st.button("完成", on_click=lambda: navigate_to('home'))
    else: st.info("无在住旅客"); st.button("返回", on_click=lambda: navigate_to('home'))

# 【批量维护：审计集成】
elif st.session_state.page == 'batch':
    st.title("🧹 批量房态维护")
    rooms_list = list(st.session_state.rooms_db.keys())
    with st.container(border=True):
        targets = st.multiselect("选择房号", rooms_list, default=rooms_list if st.checkbox("全选") else [])
        new_stat = st.select_slider("目标状态", ["Clean", "Dirty", "OOO"])
        if st.button("执行更新", type="primary"):
            actual_updated = []
            for r in targets:
                if not st.session_state.rooms_db[r]['guest']:
                    st.session_state.rooms_db[r]['status'] = new_stat
                    actual_updated.append(r)
            add_audit("批量维护", f"房间: {', '.join(actual_updated)} -> 状态: {new_stat}")
            st.success(f"已更新 {len(actual_updated)} 间房状态"); st.button("完成", on_click=lambda: navigate_to('home'))
    if st.button("返回"): navigate_to('home')

# 【报表与审计日志】
elif st.session_state.page == 'report':
    st.title("📊 报表与审计中心")
    tab1, tab2 = st.tabs(["💰 营收记录", "📑 审计日志"])
    with tab1:
        if st.session_state.history: st.dataframe(pd.DataFrame(st.session_state.history)[['name', 'rooms_str', 'checkin', 'checkout', 'total']], use_container_width=True)
        else: st.info("暂无记录")
    with tab2:
        if st.session_state.audit_logs: st.table(pd.DataFrame(st.session_state.audit_logs).iloc[::-1])
        else: st.info("暂无操作审计")
    if st.button("返回主页"): navigate_to('home')
