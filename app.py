import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 配置与样式 ---
st.set_page_config(page_title="Hotel system", layout="wide")

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

# 数据初始化
if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO", "guest": None},
    }
    st.session_state.update({'page': 'home', 'history': [], 'audit_logs': [], 'temp': {}, 'paid': False})

def nav(target):
    """标准的导航跳转函数"""
    st.session_state.page = target
    st.rerun()

def add_log(action, detail):
    """审计日志记录"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.audit_logs.append({"时间": now, "操作": action, "详情": detail})

# --- 2. 页面逻辑控制 ---

# 【主页：房态中心】
if st.session_state.page == 'home':
    st.session_state.paid = False
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    rooms = st.session_state.rooms_db
    # 动态财务统计
    paid_total = sum(h['total'] for h in st.session_state.history if h.get('status') == "已支付")
    refunded_total = sum(h['total'] for h in st.session_state.history if h.get('status') == "已退款")
    net_revenue = paid_total - refunded_total

    c1, c2, c3 = st.columns(3)
    c1.metric("入住率", f"{(sum(1 for r in rooms.values() if r['guest'])/len(rooms))*100:.1f}%")
    c2.metric("净营收 (扣除退款)", f"RM {max(0.0, net_revenue):.2f}")
    c3.metric("待清扫房间", f"{sum(1 for r in rooms.values() if r['status']=='Dirty')} 间")

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

# 【1. 入住登记页】
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    can_use = {k: f"{k} ({v['type']})" for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    
    with st.form("checkin_form_final"):
        c1, c2 = st.columns(2)
        name, ic = c1.text_input("住客姓名"), c2.text_input("证件号")
        rs = st.multiselect("分配房间", options=list(can_use.keys()), format_func=lambda x: can_use[x])
        ds = st.date_input("预订日期", [date.today(), date.today() + timedelta(1)])
        if st.form_submit_button("核算并支付"):
            if name and rs and len(ds) == 2 and (ds[1]-ds[0]).days > 0:
                st.session_state.temp = {"name": name, "ic": ic, "rs": rs, "days": (ds[1]-ds[0]).days, "checkin": ds[0], "checkout": ds[1], "id": datetime.now().strftime("%Y%m%d%H%M%S")}
                nav('pay')
            else: st.error("请完整填写，且入住天数需 > 0")
            
    st.write("---")
    if st.button("⬅️ 取消并返回首页"): nav('home')

# 【2. 结算支付确认页】
elif st.session_state.page == 'pay':
    st.title("结算确认")
    t = st.session_state.temp
    
    if st.session_state.paid:
        st.success("✅ 支付成功！")
        if st.button("完成办理并回到主页", type="primary"): 
            st.session_state.temp = {}
            nav('home')
    elif not t:
        st.warning("会话已过期，请重新操作")
        if st.button("⬅️ 返回首页"): nav('home')
    else:
        # 表格生成
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
            st.subheader(f"住客: {t['name']} | 入住: {t['checkin']} ➔ 退房: {t['checkout']}")
            st.table(pd.DataFrame(items))
            c1, c2 = st.columns([2,1])
            with c2:
                st.write(f"房费小计: RM {base:.2f} | SST (6%): RM {sst:.2f}")
                st.write(f"旅游税: RM {ttax:.2f} | 预收押金: RM 100.00")
                st.markdown(f"### 总额: RM {total:.2f}")

        col_p = st.columns(3)
        if col_p[0].button("✅ 确认支付成功", type="primary"):
            for r in t['rs']: st.session_state.rooms_db[r].update({"guest": t['name'], "status": "Dirty"})
            st.session_state.history.append({**t, "total": total, "rooms_str": ", ".join(t['rs']), "status": "已支付"})
            add_log("办理入住", f"住客 {t['name']}，房号 {', '.join(t['rs'])}，总计 RM {total:.2f}")
            st.session_state.paid = True
            st.rerun()
        if col_p[1].button("❌ 取消办理"): nav('home')
        if col_p[2].button("⬅️ 修改预订信息"): nav('in')

# 【3. 批量退房页】
elif st.session_state.page == 'out':
    st.title("🔑 离店退房管理")
    g_map = {}
    for r, info in st.session_state.rooms_db.items():
        if info['guest']: g_map.setdefault(info['guest'], []).append(f"{r}({info['type']})")
    
    if g_map:
        target = st.selectbox("选择办理离店的住客", list(g_map.keys()))
        if st.button("确认一键离店并结账", type="primary"):
            freed = []
            for r_str in g_map[target]:
                r_no = r_str.split("(")[0]
                st.session_state.rooms_db[r_no].update({"guest": None, "status": "Dirty"})
                freed.append(r_no)
            add_log("办理退房", f"住客 {target} 已结账，释放房间: {', '.join(freed)}")
            st.success(f"退房成功！房间 {', '.join(freed)} 已设为待清扫。")
            if st.button("点击回到主页"): nav('home')
    else:
        st.info("当前暂无在住旅客。")
    
    st.write("---")
    if st.button("⬅️ 返回主页"): nav('home')

# 【4. 批量房态维护页】
elif st.session_state.page == 'batch':
    st.title("🛠️ 房态维护中心")
    all_rs = list(st.session_state.rooms_db.keys())
    with st.container(border=True):
        targets = st.multiselect("勾选需更改的房间", all_rs, default=all_rs if st.checkbox("全选") else [])
        new_stat = st.select_slider("目标房态", ["Clean", "Dirty", "OOO"])
        if st.button("提交更改", type="primary"):
            updated = []
            for r in targets:
                if not st.session_state.rooms_db[r]['guest']:
                    st.session_state.rooms_db[r]['status'] = new_stat
                    updated.append(r)
            add_log("批量维护", f"房号 {', '.join(updated)} 状态更新为 {new_stat}")
            st.success(f"成功更新 {len(updated)} 间房态状态。")
            if st.button("点此刷新主页"): nav('home')
    
    st.write("---")
    if st.button("⬅️ 返回主页"): nav('home')

# 【5. 报表与退款办理页】
elif st.session_state.page == 'report':
    st.title("📊 报表与财务审计")
    tab1, tab2 = st.tabs(["💰 营收与退款", "📑 审计日志"])
    
    with tab1:
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            for idx, row in df.iterrows():
                # 使用 Expander 包裹订单，保持页面整洁
                with st.expander(f"订单: {row['id']} | 住客: {row['name']} | 金额: RM {row['total']:.2f} | 状态: {row['status']}"):
                    st.write(f"*房号:* {row['rooms_str']} | *周期:* {row['checkin']} 至 {row['checkout']}")
                    if row['status'] == "已支付":
                        if st.button(f"执行退款 (ID:{row['id']})", key=f"r_{row['id']}"):
                            st.session_state.history[idx]['status'] = "已退款"
                            add_log("财务退款", f"办理订单 {row['id']} 全额退款，RM {row['total']:.2f}")
                            st.success("退款成功，财务数据已同步更新。")
                            st.rerun()
                    else:
                        st.warning("该订单已结算退款或无法操作。")
        else:
            st.info("暂无历史交易数据记录。")
    
    with tab2:
        if st.session_state.audit_logs:
            st.table(pd.DataFrame(st.session_state.audit_logs).iloc[::-1])
        else:
            st.info("审计日志暂为空。")
    
    st.write("---")
    if st.button("⬅️ 返回主页"): nav('home')
