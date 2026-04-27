import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time

# --- 1. 全局史诗级视觉样式引擎 (规范化重构) ---
st.set_page_config(page_title="Harmony Hotel system v12.0", layout="wide")

st.markdown("""
    <style>
    /* 全局背景与字体规范 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; color: #1e293b; }
    
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }

    /* 统一卡片规范 (Room Cards & Metrics) */
    .pms-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 20px;
    }
    .pms-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        border: 1px solid #3b82f6;
    }

    /* 按钮规范统一 */
    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        font-size: 0.85rem;
        height: 3.2rem !important;
        transition: all 0.2s !important;
        border: none !important;
        background: #ffffff !important;
        color: #1e293b !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1) !important;
    }
    .stButton>button:hover {
        background: #3b82f6 !important;
        color: white !important;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4) !important;
    }

    /* 顶部导航与标题美化 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1e293b, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }

    /* 状态标签规范 */
    .badge {
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-clean { background: #dcfce7; color: #15803d; }
    .badge-dirty { background: #fee2e2; color: #b91c1c; }
    .badge-occ { background: #dbeafe; color: #1d4ed8; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心状态初始化 (继承 v11.0 逻辑) ---
if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO",   "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
    }
    st.session_state.update({
        'page': 'home', 'history': [], 'refunds': [], 'temp': {}, 'paid': False,
        'is_logged_in': False, 'checkout_history': [], 'refund_ledger': {}
    })

# --- 3. 业务工具库 ---
def nav_to(target):
    st.session_state.page = target

def get_room_label(room_no):
    if room_no in st.session_state.rooms_db:
        return f"{room_no} ({st.session_state.rooms_db[room_no]['type']})"
    return room_no

# --- 4. 统一登录网关 (abcd / 12345) ---
if not st.session_state.is_logged_in:
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.markdown("<div style='height:120px;'></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;'>Executive Portal</h1>", unsafe_allow_html=True)
        with st.container():
            with st.form("luxury_login"):
                u = st.text_input("STAFF ID", placeholder="ABCD")
                p = st.text_input("ACCESS KEY", type="password", placeholder="***")
                if st.form_submit_button("UNLOCK SYSTEM", use_container_width=True):
                    if u == "abcd" and p == "12345":
                        st.session_state.is_logged_in = True
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Invalid Credentials. Access Denied.")
                        time.sleep(1); st.rerun()
    st.stop()

# --- 5. 核心业务页面模块 ---

# 【主页看板：房态全局监控】
if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.markdown("<h1 class='main-title'> 鸿蒙智慧酒店管理系统</h1>", unsafe_allow_html=True)
    
    # 顶部统计区 (规范化 metric 显示)
    g_in = sum(h['total'] for h in st.session_state.history)
    g_out = sum(r['amount'] for r in st.session_state.refunds)
    
    m_cols = st.columns(4)
    with m_cols[0]: st.metric("入住率", f"{(sum(1 for r in st.session_state.rooms_db.values() if r['guest'])/5)*100:.0f}%")
    with m_cols[1]: st.metric("当日净营收", f"RM {g_in - g_out:.2f}")
    with m_cols[2]: st.metric("退款", f"{len(st.session_state.refunds)} 笔")
    with m_cols[3]: st.metric("可用洁净房", f"{sum(1 for r in st.session_state.rooms_db.values() if r['status']=='Clean' and not r['guest'])} 间")

    st.markdown("### 🛏️ 实时房态监控")
    # 房态栅格化
    room_grid = st.columns(5)
    for idx, (r_id, r_info) in enumerate(st.session_state.rooms_db.items()):
        with room_grid[idx]:
            is_occ = r_info['guest'] is not None
            badge_class = "badge-occ" if is_occ else ("badge-clean" if r_info['status']=="Clean" else "badge-dirty")
            st.markdown(f"""
                <div class='pms-card'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <span style='font-size:1.5rem; font-weight:800;'>{r_id}</span>
                        <span class='badge {badge_class}'>{r_info['status']}</span>
                    </div>
                    <div style='color:#64748b; font-size:0.85rem; margin-top:4px;'>{r_info['type']}</div>
                    <div style='margin-top:20px; font-weight:600;'>
                        {('👤 ' + r_info['guest']) if is_occ else '✨ Available'}
                    </div>
                    <div style='font-size:0.75rem; color:#94a3b8; margin-top:8px;'>
                        Base Price: RM {r_info['price']}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("### ⚡ 快捷指令中心")
    # 统一化操作按钮
    nav_cols = st.columns(7)
    if nav_cols[0].button("📝 登记入住", use_container_width=True): nav_to('in'); st.rerun()
    if nav_cols[1].button("🔑 批量退房", use_container_width=True): nav_to('out'); st.rerun()
    if nav_cols[2].button("⚙️ 房价管理", use_container_width=True): nav_to('price'); st.rerun()
    if nav_cols[3].button("🧹 房态维护", use_container_width=True): nav_to('batch'); st.rerun()
    if nav_cols[4].button("📊 报表中心", use_container_width=True): nav_to('report'); st.rerun()
    if nav_cols[5].button("💸 退款处理", use_container_width=True): nav_to('refund'); st.rerun()
    if nav_cols[6].button("🚪 安全退出", use_container_width=True): 
        st.session_state.is_logged_in = False; st.rerun()

# 【功能：登记入住 - 规范化输入】
elif st.session_state.page == 'in':
    st.markdown("<h2 class='main-title'>新旅客入住登记</h2>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        st.subheader("1. 核心联系人信息")
        c1, c2 = st.columns(2)
        n = c1.text_input("全名 (Name) *")
        i = c2.text_input("证件号 (ID/Passport) *")
        p = c1.text_input("手机号 (Mobile) *")
        e = c2.text_input("电子邮箱 (Email) *")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        st.subheader("2. 随行人员 (如有)")
        s_count = st.number_input("随行人数", 0, 10, 0)
        others_cache = []
        for idx in range(int(s_count)):
            sc1, sc2 = st.columns(2)
            others_cache.append({
                "name": sc1.text_input(f"随行人 {idx+1} 姓名", key=f"s_n_{idx}"),
                "ic": sc2.text_input(f"随行人 {idx+1} 证件", key=f"s_i_{idx}")
            })
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        st.subheader("3. 房源与周期")
        avail = {k: get_room_label(k) for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
        with st.form("in_form_v12"):
            sel_rooms = st.multiselect("分配客房 *", options=list(avail.keys()), format_func=lambda x: avail[x])
            date_pick = st.date_input("入住/退房日期 *", value=[date.today(), date.today() + timedelta(1)])
            
            if st.form_submit_button("核算账单预览", use_container_width=True):
                if len(date_pick) < 2 or date_pick[0] >= date_pick[1]:
                    st.error("❌ 无效日期：退房必须晚于入住")
                elif not (n and i and p and e and sel_rooms):
                    st.error("❌ 必填项缺失，请检查 * 标记字段")
                else:
                    u_code = f"UID-{datetime.now().strftime('%m%d%H%M%S')}"
                    st.session_state.temp = {
                        "uid": u_code, "name": n, "ic": i, "phone": p, "email": e,
                        "others": others_cache, "rs": {r: st.session_state.rooms_db[r]['price'] for r in sel_rooms},
                        "days": (date_pick[1]-date_pick[0]).days, "checkin": date_pick[0], "checkout": date_pick[1]
                    }
                    nav_to('pay'); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    if st.button("⬅️ 取消并返回看板"): nav_to('home'); st.rerun()

# 【功能：账单支付 - 规范化展示】
elif st.session_state.page == 'pay':
    st.markdown("<h2 class='main-title'>账单支付确认</h2>", unsafe_allow_html=True)
    t_data = st.session_state.temp
    if st.session_state.paid:
        st.success(f"入住成功！订单号: {t_data['uid']}"); st.button("返回首页", on_click=lambda: nav_to('home'))
    else:
        with st.container():
            st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
            st.write(f"*负责人:* {t_data['name']} | *单号:* {t_data['uid']}")
            st.divider()
            
            items, sub = [], 0
            for r, pr in t_data['rs'].items():
                cost = pr * t_data['days']
                sub += cost
                items.append({"描述": f"房费 - {get_room_label(r)}", "明细": f"RM {pr} x {t_data['days']}晚", "小计": f"RM {cost:.2f}"})
            
            tax = sub * 0.06
            total = sub + tax + 100.0
            st.table(pd.DataFrame(items + [{"描述": "SST (6%)", "明细": "-", "小计": f"RM {tax:.2f}"}, {"描述": "履约押金 (可退)", "明细": "-", "小计": "RM 100.00"}]))
            st.markdown(f"<h2 style='text-align:right;'>应付总额: RM {total:.2f}</h2>", unsafe_allow_html=True)

            pc1, pc2, pc3 = st.columns(3)
            if pc1.button("✅ 确认支付", type="primary", use_container_width=True):
                with st.spinner("处理中..."):
                    for r in t_data['rs'].keys():
                        st.session_state.rooms_db[r].update({
                            "guest": t_data['name'], "guest_ic": t_data['ic'], "phone": t_data['phone'],
                            "email": t_data['email'], "others": t_data['others'], "status": "Occupied", "current_uid": t_data['uid']
                        })
                    st.session_state.history.append({**t_data, "total": total, "room_list": ", ".join([get_room_label(r) for r in t_data['rs'].keys()]), "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "Paid"})
                    st.session_state.paid = True; st.rerun()
            if pc2.button("❌ 放弃登记", use_container_width=True): nav_to('home'); st.rerun()
            if pc3.button("⬅️ 返回修改", use_container_width=True): nav_to('in'); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 【功能：批量退房 & 撤销记忆】
elif st.session_state.page == 'out':
    st.markdown("<h2 class='main-title'>离店退房管理</h2>", unsafe_allow_html=True)
    active_pool = {}
    for r_no, v_info in st.session_state.rooms_db.items():
        if v_info['guest']:
            tag = f"{v_info['guest']} (ID: {v_info['guest_ic']}) | UID: {v_info.get('current_uid', 'N/A')}"
            active_pool[tag] = {"name": v_info['guest'], "ic": v_info['guest_ic'], "uid": v_info.get('current_uid')}

    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        st.subheader("快捷退房结算")
        if active_pool:
            target = st.selectbox("选择在店住客", list(active_pool.keys()))
            info = active_pool[target]
            if st.button("办理离店", type="primary", use_container_width=True):
                rel = []
                for r_no, r_val in st.session_state.rooms_db.items():
                    if r_val['guest'] == info['name'] and r_val['guest_ic'] == info['ic']:
                        rel.append(r_no)
                        st.session_state.checkout_history.append({"room": r_no, "snapshot": r_val.copy()})
                        st.session_state.rooms_db[r_no].update({"status": "Dirty", "guest": None, "guest_ic": None, "current_uid": None})
                st.success(f"结算完成！房号 {', '.join(rel)} 已释放。"); time.sleep(0.5); st.rerun()
        else: st.info("目前无住客记录。")
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        st.subheader("🔄 操作撤销记忆")
        if st.session_state.checkout_history:
            for idx, item in enumerate(st.session_state.checkout_history[-3:][::-1]):
                st.write(f"房: {get_room_label(item['room'])} | 客: {item['snapshot']['guest']}")
                if st.button(f"恢复入住状态 ({idx})", key=f"undo_v12_{idx}", use_container_width=True):
                    st.session_state.rooms_db[item['room']] = item['snapshot']
                    st.session_state.checkout_history.remove(item); st.rerun()
        else: st.write("暂无最近操作。")
        st.markdown("</div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回主页"): nav_to('home'); st.rerun()

# 【功能：风控退款系统 - UI 规范化】
elif st.session_state.page == 'refund':
    st.markdown("<h2 class='main-title'>财务退款中心</h2>", unsafe_allow_html=True)
    if st.session_state.history:
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        ref_options = {f"{h['uid']} | {h['name']} | Rooms: {h['room_list']}": i for i, h in enumerate(st.session_state.history)}
        sel_key = st.selectbox("选择需办理退款的订单", list(ref_options.keys()))
        t_order = st.session_state.history[ref_options[sel_key]]
        
        # 风控计算
        refunded = st.session_state.refund_ledger.get(t_order['uid'], 0.0)
        bal = t_order['total'] - refunded
        
        c1, c2, c3 = st.columns(3)
        c1.metric("订单总额", f"RM {t_order['total']:.2f}")
        c2.metric("累计已退", f"RM {refunded:.2f}", delta=f"-{refunded:.2f}")
        c3.metric("剩余可退", f"RM {bal:.2f}")
        
        if bal <= 0:
            st.error("🚫 该订单已完成全额退款。")
        else:
            amt = st.number_input("退款额 (Refund Amount)", 0.0, float(bal), 0.0)
            why = st.text_area("退款原因及审计备注 *")
            if st.button("批准退款并生成凭证", type="primary", use_container_width=True):
                if amt > 0 and why:
                    st.session_state.refund_ledger[t_order['uid']] = refunded + amt
                    st.session_state.refunds.append({"uid": t_order['uid'], "name": t_order['name'], "amount": amt, "reason": why, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    st.session_state.history[ref_options[sel_key]]['status'] = "Fully Refunded" if (refunded + amt) >= t_order['total'] else "Partial Refund"
                    st.success("退款成功！"); time.sleep(1); nav_to('home'); st.rerun()
                else: st.warning("请填写完整的退款理由。")
        st.markdown("</div>", unsafe_allow_html=True)
    else: st.info("尚无成交订单。")
    if st.button("⬅️ 返回"): nav_to('home'); st.rerun()

# 【功能：报表与实时日志】
elif st.session_state.page == 'report':
    st.markdown("<h2 class='main-title'>综合审计报表</h2>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["💰 入账明细", "📄 退款原因日志", "🔍 旅客查询"])
    
    with tab1:
        if st.session_state.history: st.table(pd.DataFrame(st.session_state.history)[['time', 'uid', 'name', 'room_list', 'total', 'status']])
        else: st.info("暂无数据")
    with tab2:
        if st.session_state.refunds: st.table(pd.DataFrame(st.session_state.refunds)[['time', 'uid', 'name', 'amount', 'reason']])
        else: st.info("暂无记录")
    with tab3:
        q = st.text_input("请输入姓名查找")
        if q:
            matches = [h for h in st.session_state.history if q.lower() in h['name'].lower()]
            if matches: st.table(pd.DataFrame(matches)[['time', 'uid', 'name', 'room_list']])
            else: st.warning("未找到匹配旅客")
    if st.button("⬅️ 返回主页"): nav_to('home'); st.rerun()

# 【功能：房价配置】
elif st.session_state.page == 'price':
    st.markdown("<h2 class='main-title'>客房定价中心</h2>", unsafe_allow_html=True)
    st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
    cols = st.columns(5)
    upd = {}
    for i, (no, d) in enumerate(st.session_state.rooms_db.items()):
        upd[no] = cols[i].number_input(f"{get_room_label(no)}", value=float(d['price']), key=f"lux_p_{no}")
    if st.button("保存全局变动", type="primary", use_container_width=True):
        for no, p in upd.items(): st.session_state.rooms_db[no]['price'] = p
        st.success("调价已同步。"); nav_to('home'); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"): nav_to('home'); st.rerun()

# 【功能：房态控制】
elif st.session_state.page == 'batch':
    st.markdown("<h2 class='main-title'>房态自动化调度</h2>", unsafe_allow_html=True)
    st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
    rooms = {k: get_room_label(k) for k in st.session_state.rooms_db.keys()}
    targets = st.multiselect("目标房间", options=list(rooms.keys()), format_func=lambda x: rooms[x])
    stat = st.selectbox("设定状态", ["Clean", "Dirty", "OOO (维修)"])
    if st.button("执行状态同步", type="primary", use_container_width=True):
        for r in targets:
            if not st.session_state.rooms_db[r]['guest']:
                st.session_state.rooms_db[r]['status'] = "OOO" if "维修" in stat else stat
        st.success("同步完成。"); nav_to('home'); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"): nav_to('home'); st.rerun()
