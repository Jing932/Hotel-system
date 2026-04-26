import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 配置与高级样式 ---
st.set_page_config(page_title="Executive PMS v5.2", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.2em; font-weight: 600; }
    .room-card {
        padding: 20px; border-radius: 15px; background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 8px solid #ddd;
        margin-bottom: 15px; min-height: 130px;
    }
    .bill-box { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; }
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
    # history 增加 is_refund 字段
    st.session_state.update({'page': 'home', 'history': [], 'audit_logs': [], 'temp': {}, 'paid': False})

def nav(target):
    st.session_state.page = target
    st.rerun()

def add_log(action, detail):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.audit_logs.append({"时间": now, "操作": action, "详情": detail})

# --- 2. 页面逻辑 ---

# 【主页：房态中心】
if st.session_state.page == 'home':
    st.session_state.paid = False
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    rooms = st.session_state.rooms_db
    # 动态计算营收：正常订单 - 退款订单
    total_revenue = sum(h['total'] for h in st.session_state.history if not h.get('is_refund', False))
    total_refund = sum(h['total'] for h in st.session_state.history if h.get('is_refund', False))
    net_revenue = total_revenue - total_refund

    c1, c2, c3 = st.columns(3)
    c1.metric("入住率", f"{(sum(1 for r in rooms.values() if r['guest'])/len(rooms))*100:.1f}%")
    c2.metric("净营收 (扣除退款)", f"RM {net_revenue:.2f}")
    c3.metric("待清扫", f"{sum(1 for r in rooms.values() if r['status']=='Dirty')} 间")

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
    if nav_btns[0].button("📝 入住登记", type="primary"): nav('in')
    if nav_btns[1].button("🔑 批量退房"): nav('out')
    if nav_btns[2].button("🧹 批量维护"): nav('batch')
    if nav_btns[3].button("📊 报表与退款"): nav('report')

# 【入住登记】
elif st.session_state.page == 'in':
    st.title("旅客登记")
    can_use = {k: f"{k} ({v['type']})" for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    with st.form("in_form"):
        c1, c2 = st.columns(2)
        name, ic = c1.text_input("姓名"), c2.text_input("证件号")
        rs = st.multiselect("选择房号", options=list(can_use.keys()), format_func=lambda x: can_use[x])
        ds = st.date_input("入住与离店日期", [date.today(), date.today() + timedelta(1)])
        if st.form_submit_button("去核算账单"):
            if name and rs and len(ds) == 2 and (ds[1]-ds[0]).days > 0:
                st.session_state.temp = {"name": name, "ic": ic, "rs": rs, "days": (ds[1]-ds[0]).days, "checkin": ds[0], "checkout": ds[1], "id": datetime.now().strftime("%Y%m%d%H%M%S")}
                nav('pay')
            else: st.error("请完整填写，且日期有效")
    if st.button("返回首页"): nav('home')

# 【结算确认：表格化账单】
elif st.session_state.page == 'pay':
    st.title("账单确认")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("✅ 支付成功！")
        if st.button("回到主页", type="primary"): 
            st.session_state.temp = {}
            nav('home')
    elif not t:
        st.warning("暂无数据"); st.button("返回首页", on_click=lambda: nav('home'))
    else:
        # 表格明细生成
        items = []
        base = 0
        for r in t['rs']:
            info = st.session_state.rooms_db[r]
            sub = info['price'] * t['days']
            items.append({"项目": f"房间 {r} ({info['type']})", "单价": f"RM {info['price']}", "天数": t['days'], "金额": f"RM {sub:.2f}"})
            base += sub
        
        sst, ttax = base * 0.06, 10.0 * len(t['rs']) * t['days']
        total = base + sst + ttax + 100.0

        with st.container(border=True):
            st.subheader(f"住客: {t['name']} | 入住: {t['checkin']} ➔ 退房: {t['checkout']} ({t['days']} 晚)")
            st.table(pd.DataFrame(items))
            c1, c2 = st.columns([2,1])
            with c2:
                st.write(f"房费总计: RM {base:.2f}")
                st.write(f"SST (6%): RM {sst:.2f} | 旅游税: RM {ttax:.2f}")
                st.write(f"预收押金: RM 100.00")
                st.markdown(f"### 总额: RM {total:.2f}")

        col_p = st.columns(3)
        if col_p[0].button("✅ 确认支付", type="primary"):
            for r in t['rs']: st.session_state.rooms_db[r].update({"guest": t['name'], "status": "Dirty"})
            # 保存到历史记录
            st.session_state.history.append({**t, "total": total, "rooms_str": ", ".join(t['rs']), "status": "已支付", "is_refund": False})
            add_log("登记入住", f"住客 {t['name']}，房号 {', '.join(t['rs'])}，金额 RM {total:.2f}")
            st.session_state.paid = True
            st.rerun()
        if col_p[1].button("❌ 取消"): nav('home')
        if col_p[2].button("⬅️ 修改"): nav('in')

# 【批量退房】
elif st.session_state.page == 'out':
    st.title("🔑 批量退房管理")
    g_map = {}
    for r, info in st.session_state.rooms_db.items():
        if info['guest']: g_map.setdefault(info['guest'], []).append(f"{r}({info['type']})")
    
    if g_map:
        target = st.selectbox("选择离店住客", list(g_map.keys()))
        if st.button("确认一键退房", type="primary"):
            freed = []
            for r_str in g_map[target]:
                r_no = r_str.split("(")[0]
                st.session_state.rooms_db[r_no].update({"guest": None, "status": "Dirty"})
                freed.append(r_no)
            add_log("办理退房", f"住客 {target} 已释放房间: {', '.join(freed)}")
            st.success("退房完成")
            if st.button("返回主页"): nav('home')
    else: st.info("目前无住客"); st.button("返回", on_click=lambda: nav('home'))

# 【批量房态维护】
elif st.session_state.page == 'batch':
    st.title("🧹 批量房态维护")
    all_rs = list(st.session_state.rooms_db.keys())
    with st.container(border=True):
        targets = st.multiselect("选择房号", all_rs, default=all_rs if st.checkbox("全选所有房间") else [])
        new_stat = st.select_slider("设定状态", ["Clean", "Dirty", "OOO"])
        if st.button("立即执行", type="primary"):
            updated = []
            for r in targets:
                if not st.session_state.rooms_db[r]['guest']:
                    st.session_state.rooms_db[r]['status'] = new_stat
                    updated.append(r)
            add_log("手动维护", f"房间 {', '.join(updated)} 设为 {new_stat}")
            st.success(f"已更新 {len(updated)} 间房"); st.button("完成", on_click=lambda: nav('home'))
    if st.button("返回"): nav('home')

# 【报表、退款与审计】
elif st.session_state.page == 'report':
    st.title("📊 报表与财务管理")
    tab1, tab2 = st.tabs(["💰 营收与退款办理", "📑 审计日志"])
    
    with tab1:
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            st.write("### 交易流水")
            # 显示每一笔订单及其退款状态
            for idx, row in df.iterrows():
                with st.expander(f"订单 {row['id']} - 住客: {row['name']} | 金额: RM {row['total']:.2f} | 状态: {row['status']}"):
                    st.write(f"*房间:* {row['rooms_str']} | *周期:* {row['checkin']} 至 {row['checkout']}")
                    if not row['is_refund']:
                        if st.button(f"办理退款 (ID:{row['id']})", key=f"ref_{row['id']}"):
                            # 执行退款逻辑
                            st.session_state.history[idx]['is_refund'] = True
                            st.session_state.history[idx]['status'] = "已退款"
                            add_log("财务退款", f"为订单 {row['id']} (住客: {row['name']}) 办理全额退款 RM {row['total']:.2f}")
                            st.success("退款已执行，财务数据已更新")
                            st.rerun()
                    else:
                        st.warning("此订单已办理退款")
        else: st.info("暂无交易记录")
    
    with tab2:
        if st.session_state.audit_logs: st.table(pd.DataFrame(st.session_state.audit_logs).iloc[::-1])
        else: st.info("暂无操作日志")
    
    if st.button("返回主页"): nav('home')
