import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time

# --- 1. 全局增强样式 (UI 进一步优化) ---
st.set_page_config(page_title="Harmony PMS Pro v10.0", layout="wide")

st.markdown("""
    <style>
    /* 全局背景与字体 */
    .main { background-color: #f8fafc; }
    .stApp { background-image: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); }
    
    /* 统计卡片美化 */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    
    /* 房态卡片深度美化 */
    .room-container {
        padding: 20px;
        border-radius: 15px;
        background: white;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .room-container:hover { transform: translateY(-5px); box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }
    
    /* 按钮样式强化 */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
        height: 3.5rem;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心数据库初始化 (绝对保留 v8.0/9.0 数据结构) ---
if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO",   "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
    }
    st.session_state.update({
        'page': 'home', 
        'history': [], 
        'refunds': [], 
        'temp': {}, 
        'paid': False,
        'is_logged_in': False,
        'checkout_history': []  # 增加批量退房的记忆功能
    })

# --- 3. 解决 st.rerun() no-op 问题 (状态机控制) ---
# 不再在 callback 中调用 rerun，而是修改状态后让脚本自然重跑
def nav_to(target):
    st.session_state.page = target

def get_room_label(room_no):
    """带房型的房号标注"""
    if room_no in st.session_state.rooms_db:
        return f"{room_no} ({st.session_state.rooms_db[room_no]['type']})"
    return room_no

# --- 4. 员工登录系统 (abcd / 12345) ---
if not st.session_state.is_logged_in:
    st.markdown("<div style='max-width:400px; margin: 100px auto;'>", unsafe_allow_html=True)
    st.title("🔐 后台登录")
    with st.form("login_gate"):
        u = st.text_input("工号 (User)")
        p = st.text_input("密码 (Pass)", type="password")
        if st.form_submit_button("验证登录", use_container_width=True):
            if u == "abcd" and p == "12345":
                st.session_state.is_logged_in = True
                st.rerun()
            else:
                st.error("验证失败，页面已重置")
                time.sleep(1)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop() # 强制停止后续代码执行

# --- 5. 核心业务逻辑 ---

# 【页面 1: 首页房态】
if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    # 顶部数据卡片
    rev_in = sum(h['total'] for h in st.session_state.history)
    rev_out = sum(r['amount'] for r in st.session_state.refunds)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("当前出租率", f"{(sum(1 for r in st.session_state.rooms_db.values() if r['guest'])/5)*100:.0f}%")
    with c2: st.metric("净营收 (Net)", f"RM {rev_in - rev_out:.2f}")
    with c3: st.metric("已处理退款", f"RM {rev_out:.2f}")
    with c4: st.metric("待清洁/维修", f"{sum(1 for r in st.session_state.rooms_db.values() if r['status'] in ['Dirty', 'OOO'])} 间")

    st.divider()
    # 房态渲染 (不带备注，保持原始清爽)
    room_cols = st.columns(5)
    for i, (no, info) in enumerate(st.session_state.rooms_db.items()):
        with room_cols[i]:
            is_occ = info['guest'] is not None
            c = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316" if info['status']=="Dirty" else "#64748b")
            st.markdown(f"""
                <div class='room-container' style='border-top: 6px solid {c};'>
                    <span style='font-size: 1.3em; font-weight: 800;'>{no}</span> 
                    <small style='color: #64748b;'>{info['type']}</small><br>
                    <span style='color: #94a3b8; font-size: 0.85em;'>实时价: RM {info['price']}</span><br>
                    <div style='color: {c}; font-weight: 700; margin-top: 15px;'>
                        {'👤 ' + info['guest'] if is_occ else '✨ ' + info['status']}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.write("")
    st.subheader("⚙️ 业务处理中心")
    b1, b2, b3, b4, b5, b6, b7 = st.columns(7)
    if b1.button("📝 登记入住", type="primary"): nav_to('in'); st.rerun()
    if b2.button("🔑 批量退房"): nav_to('out'); st.rerun()
    if b3.button("⚙️ 房价管理"): nav_to('price'); st.rerun()
    if b4.button("🧹 房态维护"): nav_to('batch'); st.rerun()
    if b5.button("📊 报表中心"): nav_to('report'); st.rerun()
    if b6.button("💸 退款处理"): nav_to('refund'); st.rerun()
    if b7.button("🚪 登出", help="安全退出系统"): 
        st.session_state.is_logged_in = False
        st.rerun()

# 【页面 2: 入住登记】
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    st.subheader("1. 基础信息 (*号为必填)")
    c1, c2 = st.columns(2)
    name = c1.text_input("主负责人姓名 *", placeholder="输入真实姓名")
    ic = c2.text_input("证件号 (IC/Passport) *", placeholder="输入证件号码")
    tel = c1.text_input("联系电话 *", placeholder="01x-xxxxxxx")
    mail = c2.text_input("电子邮箱 *", placeholder="guest@example.com")
    
    st.write("---")
    st.subheader("2. 随行人员 (实时动态)")
    n_others = st.number_input("随行人数", 0, 10, 0)
    others_data = []
    for i in range(int(n_others)):
        o1, o2 = st.columns(2)
        on = o1.text_input(f"随行人 {i+1} 姓名", key=f"on_{i}")
        oi = o2.text_input(f"随行人 {i+1} 证件", key=f"oi_{i}")
        others_data.append({"name": on, "ic": oi})

    st.write("---")
    st.subheader("3. 房源分配")
    # 备注房型
    avail = {k: get_room_label(k) for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    
    with st.form("checkin_v10"):
        rs_sel = st.multiselect("选择房间 (仅显示洁净房) *", options=list(avail.keys()), format_func=lambda x: avail[x])
        d_range = st.date_input("预计入住周期 *", value=[date.today(), date.today() + timedelta(1)])
        
        if st.form_submit_button("核算并跳转账单"):
            if len(d_range) < 2 or d_range[0] >= d_range[1]:
                st.error("❌ 日期错误：离店日期必须晚于入住日期")
            elif not (name and ic and tel and mail and rs_sel):
                st.error("❌ 请完整填写所有必填字段")
            else:
                snap = {r: st.session_state.rooms_db[r]['price'] for r in rs_sel}
                # 创建唯一订单 ID 解决同房不同客退款冲突
                order_uid = f"REC-{datetime.now().strftime('%m%d%H%M%S')}"
                st.session_state.temp = {
                    "uid": order_uid, "name": name, "ic": ic, "phone": tel, "email": mail,
                    "others": others_data, "rs": snap, "days": (d_range[1]-d_range[0]).days,
                    "checkin": d_range[0], "checkout": d_range[1]
                }
                nav_to('pay'); st.rerun()
    if st.button("⬅️ 取消并返回"): nav_to('home'); st.rerun()

# 【页面 3: 账单与支付】
elif st.session_state.page == 'pay':
    st.title("💳 账单明细确认")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success(f"入住成功！订单号: {t['uid']}"); st.button("返回首页", on_click=lambda: nav_to('home'))
    else:
        st.markdown(f"*负责人:* {t['name']} | *单号:* {t['uid']}")
        bill_list, subtotal = [], 0
        for r_no, price in t['rs'].items():
            amt = price * t['days']; subtotal += amt
            # 备注房型
            bill_list.append({"项目": f"房费 - {get_room_label(r_no)}", "金额": f"{amt:.2f}"})
        
        tax = subtotal * 0.06
        total = subtotal + tax + 100.0
        st.table(pd.DataFrame(bill_list + [{"项目": "SST (6%)", "金额": f"{tax:.2f}"}, {"项目": "押金", "金额": "100.00"}]))
        st.metric("总支付额", f"RM {total:.2f}")

        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 确认支付", type="primary"):
            for r in t['rs'].keys():
                st.session_state.rooms_db[r].update({
                    "guest": t['name'], "guest_ic": t['ic'], "phone": t['phone'], 
                    "email": t['email'], "others": t['others'], "status": "Occupied",
                    "current_order_id": t['uid'] # 房态绑定当前订单号
                })
            st.session_state.history.append({**t, "total": total, "room_list": ", ".join([get_room_label(r) for r in t['rs'].keys()]), "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "Paid"})
            st.session_state.paid = True; st.rerun()
        if c2.button("❌ 放弃订单"): nav_to('home'); st.rerun()
        if c3.button("⬅️ 修改信息"): nav_to('in'); st.rerun()

# 【页面 4: 批量退房 & 记忆功能修复】
elif st.session_state.page == 'out':
    st.title("🔑 离店结算中心")
    # 构建精准的 住客-IC-订单 映射，解决同名冲突
    active_map = {}
    for r_no, v in st.session_state.rooms_db.items():
        if v['guest']:
            k = f"{v['guest']} (IC: {v['guest_ic']})"
            active_map[k] = {"name": v['guest'], "ic": v['guest_ic'], "uid": v.get('current_order_id')}

    left_q, right_q = st.columns(2)
    with left_q:
        st.subheader("办理退房")
        if active_map:
            sel_k = st.selectbox("选择办理人 (姓名+IC)", list(active_map.keys()))
            target = active_map[sel_k]
            if st.button("确认退房结算", type="primary"):
                released_rooms = []
                for r, info in st.session_state.rooms_db.items():
                    if info['guest'] == target['name'] and info['guest_ic'] == target['ic']:
                        released_rooms.append(r)
                        # 记忆功能增强：存储到 checkout_history 供撤销
                        st.session_state.checkout_history.append({
                            "room": r, "info": info.copy(), "time": time.time()
                        })
                        st.session_state.rooms_db[r].update({"status": "Dirty", "guest": None, "guest_ic": None, "current_order_id": None})
                st.success(f"已释放房间: {', '.join(released_rooms)}"); time.sleep(0.5); st.rerun()
        else: st.info("目前无住客。")

    with right_q:
        st.subheader("🔄 记忆与撤销")
        if st.session_state.checkout_history:
            # 只显示最近 5 条退房记录防止撑爆页面
            recent = st.session_state.checkout_history[-5:][::-1]
            for i, record in enumerate(recent):
                # 备注房型
                label = get_room_label(record['room'])
                st.write(f"房: {label} | 客人: {record['info']['guest']}")
                if st.button(f"撤销退房 ({label})", key=f"undo_{i}"):
                    st.session_state.rooms_db[record['room']] = record['info']
                    st.session_state.checkout_history.remove(record)
                    st.success("已恢复状态"); st.rerun()
        else: st.write("暂无退房记忆。")
    if st.button("⬅️ 返回"): nav_to('home'); st.rerun()

# 【页面 5: 房价管理】
elif st.session_state.page == 'price':
    st.title("⚙️ 房价策略中心")
    p_cols = st.columns(5)
    updates = {}
    for i, (no, info) in enumerate(st.session_state.rooms_db.items()):
        # 备注房型
        updates[no] = p_cols[i].number_input(f"{get_room_label(no)}", value=float(info['price']), key=f"pr_{no}")
    if st.button("🔥 保存全部修改", type="primary"):
        for no, p in updates.items(): st.session_state.rooms_db[no]['price'] = p
        st.success("价格库已更新"); nav_to('home'); st.rerun()
    if st.button("⬅️ 返回"): nav_to('home'); st.rerun()

# 【页面 6: 报表中心 (含随行人搜索)】
elif st.session_state.page == 'report':
    st.title("📊 数据统计分析")
    t1, t2, t3 = st.tabs(["入账明细", "退款日志", "旅客检索"])
    with t1:
        if st.session_state.history:
            h_df = pd.DataFrame(st.session_state.history)
            h_df['随行人'] = h_df['others'].apply(lambda x: "|".join([p['name'] for p in x]) if x else "-")
            # 显示备注房型的订单
            st.table(h_df[['time', 'uid', 'name', 'room_list', 'total', 'status', '随行人']])
        else: st.write("暂无记录")
    with t3:
        query = st.text_input("输入姓名 (主客/随行人)")
        if query:
            match = []
            for h in st.session_state.history:
                o_names = [p['name'].lower() for p in h['others']]
                if query.lower() in h['name'].lower() or any(query.lower() in n for n in o_names):
                    match.append({"订单号": h['uid'], "主客": h['name'], "周期": f"{h['checkin']}~{h['checkout']}"})
            if match: st.table(pd.DataFrame(match))
            else: st.warning("未找到匹配旅客")
    if st.button("⬅️ 返回"): nav_to('home'); st.rerun()

# 【页面 7: 退款处理 - 解决同房不同客 Bug】
elif st.session_state.page == 'refund':
    st.title("💸 订单退款中心")
    if st.session_state.history:
        # 核心逻辑：以订单号(UID)为准，而不是房号
        ref_options = {f"{h['uid']} - {h['name']} (房: {h['room_list']})": i for i, h in enumerate(st.session_state.history)}
        sel_idx = st.selectbox("请选择要处理的订单 (支持历史订单)", list(ref_options.keys()))
        target_order = st.session_state.history[ref_options[sel_idx]]
        
        st.warning(f"该订单总计入账: RM {target_order['total']}")
        ref_amt = st.number_input("拟退金额", 0.0, float(target_order['total']), 0.0)
        ref_why = st.text_area("退款原因")
        
        if st.button("确认执行退款", type="primary"):
            if ref_amt > 0:
                st.session_state.refunds.append({
                    "uid": target_order['uid'], "name": target_order['name'], 
                    "amount": ref_amt, "reason": ref_why, "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                # 更新历史订单状态
                st.session_state.history[ref_options[sel_idx]]['status'] = "Refunded"
                st.success(f"已为单号 {target_order['uid']} 成功办理退款"); time.sleep(1); nav_to('home'); st.rerun()
    else: st.info("暂无历史订单，无法执行退款操作。")
    if st.button("⬅️ 返回"): nav_to('home'); st.rerun()

# 【页面 8: 房态维护】
elif st.session_state.page == 'batch':
    st.title("🧹 房态与清洁管理")
    # 备注房型
    all_r = {k: get_room_label(k) for k in st.session_state.rooms_db.keys()}
    sel_rooms = st.multiselect("选择房间", list(all_r.keys()), format_func=lambda x: all_r[x])
    new_s = st.selectbox("更新状态为", ["Clean", "Dirty", "OOO"])
    if st.button("批量应用更新"):
        for r in sel_rooms:
            if not st.session_state.rooms_db[r]['guest']: st.session_state.rooms_db[r]['status'] = new_s
        st.success("更新成功"); nav_to('home'); st.rerun()
    if st.button("⬅️ 返回"): nav_to('home'); st.rerun()
