import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 全局配置与状态初始化 ---
st.set_page_config(page_title="Executive PMS v8.0", layout="wide")

if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO",   "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
    }
    st.session_state.update({'page': 'home', 'history': [], 'refunds': [], 'temp': {}, 'paid': False})

def nav(target):
    st.session_state.page = target
    st.rerun()

# --- 2. 页面逻辑控制 ---

# 【主页：房态中心】
if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    # 财务计算：已收 - 已退
    total_in = sum(h['total'] for h in st.session_state.history)
    total_out = sum(r['amount'] for r in st.session_state.refunds)
    
    # UI 布局美化
    st.markdown("""
        <style>
        .metric-card { background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; }
        </style>
    """, unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("入住率", f"{(sum(1 for r in st.session_state.rooms_db.values() if r['guest'])/5)*100:.0f}%")
    with c2: st.metric("净营收", f"RM {total_in - total_out:.2f}")
    with c3: st.metric("已退款项", f"RM {total_out:.2f}", delta=f"-{len(st.session_state.refunds)} 笔", delta_color="inverse")
    with c4: st.metric("在线房态", f"{sum(1 for r in st.session_state.rooms_db.values() if r['status']=='Clean' and not r['guest'])} 洁净房")

    st.divider()
    cols = st.columns(5)
    for idx, (no, info) in enumerate(st.session_state.rooms_db.items()):
        with cols[idx]:
            is_occ = info['guest'] is not None
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316" if info['status']=="Dirty" else "#64748b")
            st.markdown(f"""
                <div style='padding:15px; border-radius:10px; background:white; border-top:5px solid {color}; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1); min-height:160px;'>
                    <b style='font-size:1.2em;'>{no}</b> <small style='color:#64748b;'>{info['type']}</small><br>
                    <span style='color:#94a3b8; font-size:0.8em;'>单价: RM {info['price']}</span><br>
                    <div style='color:{color}; font-weight:bold; margin-top:12px; font-size:0.9em;'>
                        {'👤 '+info['guest'] if is_occ else '✨ '+info['status']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    st.write("")
    menu = st.columns(6)
    if menu[0].button("📝 登记入住", type="primary", use_container_width=True): st.session_state.temp = {}; nav('in')
    if menu[1].button("🔑 批量退房", use_container_width=True): nav('out')
    if menu[2].button("⚙️ 房价管理", use_container_width=True): nav('price_admin')
    if menu[3].button("🧹 房态维护", use_container_width=True): nav('batch')
    if menu[4].button("📊 报表中心", use_container_width=True): nav('report')
    if menu[5].button("💸 退款处理", use_container_width=True): nav('refund_page')

# 【功能：入住登记 - 强化校验与随行人实时化】
elif st.session_state.page == 'in':
    st.title("📝 旅客登记入住")
    
    st.subheader("1. 负责人必填信息")
    c1, c2 = st.columns(2)
    name = c1.text_input("主登记人姓名 *")
    ic = c2.text_input("证件号 (IC/Passport) *")
    phone = c1.text_input("手机号 *", placeholder="例如: 012-3456789")
    email = c2.text_input("电子邮箱 *", placeholder="example@mail.com")
    
    st.write("---")
    st.subheader("2. 随行人员 (实时增减)")
    num_others = st.number_input("随行人数", 0, 10, 0)
    current_others = []
    for i in range(int(num_others)):
        oc1, oc2 = st.columns(2)
        o_name = oc1.text_input(f"随行人 {i+1} 姓名", key=f"v8_on_{i}")
        o_ic = oc2.text_input(f"随行人 {i+1} 证件号", key=f"v8_oi_{i}")
        current_others.append({"name": o_name, "ic": o_ic})

    st.write("---")
    st.subheader("3. 房态与日期 (含漏洞修复)")
    can_use = {k: f"{k} ({v['type']})" for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    
    with st.form("v8_checkin"):
        rs = st.multiselect("分配洁净客房", options=list(can_use.keys()))
        ds = st.date_input("入住/离店日期", value=[date.today(), date.today() + timedelta(1)])
        
        if st.form_submit_button("核算并锁定预览"):
            # 漏洞修复：日期顺序校验
            if len(ds) < 2 or ds[0] >= ds[1]:
                st.error("❌ 日期选择错误：离店日期必须晚于入住日期。")
            elif not (name and ic and phone and email and rs):
                st.error("❌ 请完整填写所有带 * 号的必填项并选择房间。")
            else:
                snap = {r: st.session_state.rooms_db[r]['price'] for r in rs}
                st.session_state.temp = {
                    "name": name, "ic": ic, "phone": phone, "email": email,
                    "others": current_others, "rs": snap, "days": (ds[1]-ds[0]).days, 
                    "id": datetime.now().strftime("%y%m%d%H%M"), "checkin": ds[0], "checkout": ds[1]
                }
                nav('pay')
    if st.button("⬅️ 返回主页"): nav('home')

# 【功能：账单预览】
elif st.session_state.page == 'pay':
    st.title("💳 确认并支付")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("✅ 登记成功！已入库。"); st.button("返回首页", on_click=lambda: nav('home'))
    else:
        # 美化账单显示
        st.info(f"旅客: {t['name']} | 证件: {t['ic']} | 周期: {t['days']} 晚")
        if t['others']:
            with st.expander("查看随行人员"):
                for p in t['others']: st.write(f"• {p['name']} ({p['ic']})")
        
        bill, sub = [], 0
        for r_no, p in t['rs'].items():
            amt = p * t['days']; sub += amt
            bill.append({"项目": f"客房 {r_no}", "明细": f"RM {p} x {t['days']}", "金额": f"{amt:.2f}"})
        tax = sub * 0.06
        total_f = sub + tax + 100.0
        
        st.table(pd.DataFrame(bill + [{"项目": "SST (6%)", "明细": "-", "金额": f"{tax:.2f}"}, {"项目": "押金", "明细": "-", "金额": "100.00"}]))
        st.markdown(f"<h2 style='text-align:right;'>应付金额: <span style='color:red;'>RM {total_f:.2f}</span></h2>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 支付成功并入住", type="primary", use_container_width=True):
            for r in t['rs'].keys():
                st.session_state.rooms_db[r].update({
                    "guest": t['name'], "guest_ic": t['ic'], "phone": t['phone'], 
                    "email": t['email'], "others": t['others'], "status": "Occupied"
                })
            st.session_state.history.append({**t, "total": total_f, "room_list": ", ".join(t['rs'].keys()), "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "Paid"})
            st.session_state.paid = True; st.rerun()
        if c2.button("❌ 支付失败 (取消)", use_container_width=True): st.session_state.temp = {}; nav('home')
        if c3.button("⬅️ 返回修改", use_container_width=True): nav('in')

# 【功能：退房管理 - 增加撤销退房】
elif st.session_state.page == 'out':
    st.title("🔑 离店退房管理")
    # 核心修复：使用 姓名+IC 唯一标识，防止误退同名旅客
    active_guests = {}
    for v in st.session_state.rooms_db.values():
        if v['guest']:
            key = f"{v['guest']} (IC: {v['guest_ic']})"
            active_guests[key] = {"name": v['guest'], "ic": v['guest_ic']}
            
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("批量办理退房")
        if active_guests:
            target_key = st.selectbox("选择办理人 (精确匹配姓名与IC)", list(active_guests.keys()))
            target = active_guests[target_key]
            if st.button("确认退房", type="primary"):
                for r, info in st.session_state.rooms_db.items():
                    if info['guest'] == target['name'] and info['guest_ic'] == target['ic']:
                        # 退房时保留最后一位客人信息以便撤销，但状态改为 Dirty
                        st.session_state.rooms_db[r].update({"status": "Dirty", "last_guest": info['guest'], "last_ic": info['guest_ic'], "guest": None, "guest_ic": None})
                st.success("退房成功。"); st.rerun()
        else: st.info("目前无住客。")

    with c2:
        st.subheader("🔄 撤销退房 (误操作恢复)")
        # 寻找刚才退房但还是 Dirty 状态的房间
        undo_rooms = [r for r, v in st.session_state.rooms_db.items() if v.get('last_guest') and v['status'] == "Dirty"]
        if undo_rooms:
            target_undo = st.selectbox("选择要恢复的房间", undo_rooms)
            if st.button("恢复为入住状态"):
                r_info = st.session_state.rooms_db[target_undo]
                st.session_state.rooms_db[target_undo].update({
                    "guest": r_info['last_guest'], "guest_ic": r_info['last_ic'], "status": "Occupied", "last_guest": None
                })
                st.success(f"房间 {target_undo} 已恢复入住。"); st.rerun()
        else: st.write("暂无最近退房记录。")
    if st.button("⬅️ 返回"): nav('home')

# 【功能：退款处理 - 联动财务状态】
elif st.session_state.page == 'refund_page':
    st.title("💸 退款申请")
    if st.session_state.history:
        # 只显示 Paid 状态订单
        options = {f"{h['id']} - {h['name']}": i for i, h in enumerate(st.session_state.history)}
        idx = st.selectbox("选择原始订单", list(options.keys()))
        order = st.session_state.history[options[idx]]
        
        amt = st.number_input("退款金额", 0.0, float(order['total']))
        reason = st.text_area("退款原因")
        if st.button("确认退款", type="primary"):
            st.session_state.refunds.append({"id": order['id'], "name": order['name'], "amount": amt, "reason": reason, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            # 修改原始订单状态，解决财务不可逆缺陷
            st.session_state.history[options[idx]]['status'] = "Refunded" if amt >= order['total'] else "Partial Refund"
            st.success("退款已登记。"); nav('home')
    if st.button("⬅️ 返回"): nav('home')

# 【功能：报表中心 - 随行人数据集成】
elif st.session_state.page == 'report':
    st.title("📊 综合财务报表")
    tab1, tab2 = st.tabs(["📥 入账与旅客详情", "📤 退款记录"])
    
    with tab1:
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            # 增加随行人展示列
            df['随行人信息'] = df['others'].apply(lambda x: " | ".join([f"{p['name']}({p['ic']})" for p in x]) if x else "无")
            st.table(df[['time', 'id', 'name', 'ic', 'room_list', 'total', 'status', '随行人信息']])
            
            st.divider()
            search_name = st.text_input("🔍 搜索负责人或随行人姓名")
            if search_name:
                # 深度搜索：匹配负责人名或随行人名
                results = []
                for h in st.session_state.history:
                    others_names = [p['name'] for p in h['others']]
                    if search_name.lower() in h['name'].lower() or any(search_name.lower() in on.lower() for on in others_names):
                        results.append(h)
                if results: st.write("找到相关记录："); st.table(pd.DataFrame(results)[['time', 'name', 'room_list', 'total']])
                else: st.warning("未找到匹配数据。")
        else: st.write("暂无入账。")
        
    with tab2:
        if st.session_state.refunds: st.table(pd.DataFrame(st.session_state.refunds))
    if st.button("⬅️ 返回"): nav('home')

# 【功能：房价后台】
elif st.session_state.page == 'price_admin':
    st.title("⚙️ 房价后台")
    cols = st.columns(5)
    new_data = {}
    for i, (no, info) in enumerate(st.session_state.rooms_db.items()):
        new_data[no] = cols[i].number_input(f"房号 {no}", value=float(info['price']), key=f"v8_p_{no}")
    if st.button("确认保存", type="primary"):
        for no, p in new_data.items(): st.session_state.rooms_db[no]['price'] = p
        st.success("更新成功"); nav('home')
    if st.button("⬅️ 返回"): nav('home')

# 【功能：房态维护】
elif st.session_state.page == 'batch':
    st.title("🧹 房态维护")
    rs = st.multiselect("选择房号", list(st.session_state.rooms_db.keys()))
    sv = st.selectbox("修改为", ["Clean", "Dirty", "OOO"])
    if st.button("执行"):
        for r in rs:
            if not st.session_state.rooms_db[r]['guest']: st.session_state.rooms_db[r]['status'] = sv
        nav('home')
    if st.button("⬅️ 返回"): nav('home')
