import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 初始化 ---
st.set_page_config(page_title="Executive PMS v6.6", layout="wide")

if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO",   "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
    }
    # 增加 refunds 记录用于计算净营收
    st.session_state.update({'page': 'home', 'history': [], 'refunds': [], 'temp': {}, 'paid': False})

def nav(target):
    st.session_state.page = target
    st.rerun()

# --- 2. 页面逻辑 ---

# 【主页：房态中心】
if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    # 财务计算：总收入 - 总退款
    total_in = sum(h['total'] for h in st.session_state.history)
    total_out = sum(r['amount'] for r in st.session_state.refunds)
    net_revenue = total_in - total_out
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("入住率", f"{(sum(1 for r in st.session_state.rooms_db.values() if r['guest'])/5)*100:.0f}%")
    c2.metric("净营收", f"RM {net_revenue:.2f}")
    c3.metric("总退款", f"RM {total_out:.2f}", delta_color="inverse")
    c4.metric("在线房态", f"{sum(1 for r in st.session_state.rooms_db.values() if r['status']=='Clean')} 洁净")

    st.divider()
    cols = st.columns(5)
    for idx, (no, info) in enumerate(st.session_state.rooms_db.items()):
        with cols[idx]:
            is_occ = info['guest'] is not None
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316" if info['status']=="Dirty" else "#64748b")
            st.markdown(f"""
                <div style="padding:15px; border-radius:10px; background:white; border-top:5px solid {color}; box-shadow:0 2px 4px rgba(0,0,0,0.1); min-height:140px;">
                    <b style="font-size:1.1em;">{no}</b> <small>{info['type']}</small><br>
                    <div style="color:gray; font-size:0.85em;">标价: RM {info['price']}</div>
                    <div style="color:{color}; font-weight:bold; margin-top:5px;">
                        {f"👤 {info['guest']}" if is_occ else info['status']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    st.write("")
    st.subheader("🛠️ 系统功能面板")
    btns = st.columns(6) # 增加退款入口
    if btns[0].button("📝 入住登记", type="primary"): st.session_state.temp = {}; nav('in')
    if btns[1].button("🔑 批量退房"): nav('out')
    if btns[2].button("⚙️ 房价后台"): nav('price_admin')
    if btns[3].button("🧹 房态维护"): nav('batch')
    if btns[4].button("📊 报表中心"): nav('report')
    if btns[5].button("💸 退款处理"): nav('refund_page')

# 【1. 入住登记：强约束逻辑】
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    t = st.session_state.temp
    # 核心修复：只有状态为 Clean 且没人的房子才能卖
    can_use = {k: f"{k} ({v['type']}) - RM{v['price']}" for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    
    if not can_use:
        st.warning("⚠️ 当前没有可供入住的洁净房间，请先前往『房态维护』清理房间。")
    
    num_others = st.number_input("随行人数", min_value=0, max_value=10, value=len(t.get('others', [])))

    with st.form("checkin_v66"):
        c1, c2 = st.columns(2)
        name, ic = c1.text_input("姓名"), c2.text_input("证件号")
        phone, email = c1.text_input("手机号"), c2.text_input("邮箱")
        others_list = []
        for i in range(int(num_others)):
            oc1, oc2 = st.columns(2)
            others_list.append({"name": oc1.text_input(f"随行人{i+1}姓名", key=f"n{i}"), "ic": oc2.text_input(f"随行人{i+1}IC", key=f"i{i}")})
        
        # 房间选择
        rs = st.multiselect("选择房间 (仅显示洁净房)", options=list(can_use.keys()), format_func=lambda x: can_use[x])
        ds = st.date_input("入住租期", value=[date.today(), date.today() + timedelta(1)])

        if st.form_submit_button("核算并确认账单"):
            if name and ic and rs and len(ds) == 2:
                # 价格快照：在这里锁定当前房间的价格，后续后台改价不影响此单
                booked_rooms = {r: st.session_state.rooms_db[r]['price'] for r in rs}
                st.session_state.temp = {"name": name, "ic": ic, "phone": phone, "email": email, "others": others_list, 
                                        "rs": booked_rooms, "days": (ds[1]-ds[0]).days, "checkin": ds[0], "checkout": ds[1], "id": datetime.now().strftime("%y%m%d%H%M")}
                nav('pay')
            else: st.error("请填入必填项并选择房间")
    if st.button("⬅️ 返回"): nav('home')

# 【2. 结算页：使用快照价格】
elif st.session_state.page == 'pay':
    st.title("💳 账单确认")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("登记成功！"); st.button("返回首页", on_click=lambda: nav('home'))
    else:
        bill_data = []
        subtotal = 0
        for r_no, snap_price in t['rs'].items():
            amt = snap_price * t['days']
            subtotal += amt
            bill_data.append({"项目": f"房间 {r_no}", "由来": f"RM {snap_price} × {t['days']} 晚", "金额": f"{amt:.2f}"})
        
        tax = subtotal * 0.06
        bill_data.append({"项目": "SST (6%)", "由来": f"RM {subtotal:.2f} × 0.06", "金额": f"{tax:.2f}"})
        bill_data.append({"项目": "押金", "由来": "固定押金", "金额": "100.00"})
        total_f = subtotal + tax + 100.0
        
        st.table(pd.DataFrame(bill_data))
        st.metric("应付总额", f"RM {total_f:.2f}")

        if st.button("确认支付并入住", type="primary"):
            for r in t['rs'].keys():
                st.session_state.rooms_db[r].update({"guest": t['name'], "guest_ic": t['ic'], "others": t['others'], "status": "Occupied"})
            st.session_state.history.append({**t, "total": total_f, "room_list": ", ".join(t['rs'].keys()), "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            st.session_state.paid = True
            st.rerun()
        if st.button("⬅️ 返回修改"): nav('in')

# 【3. 退款处理界面】新增
elif st.session_state.page == 'refund_page':
    st.title("💸 退款申请处理")
    if not st.session_state.history:
        st.info("暂无已支付订单可退款。")
    else:
        # 选择订单
        options = {f"{h['id']} - {h['name']}": idx for idx, h in enumerate(st.session_state.history)}
        target_idx = st.selectbox("选择要退款的订单编号", list(options.keys()))
        order = st.session_state.history[options[target_idx]]
        
        st.write(f"订单金额: RM {order['total']:.2f}")
        ref_amount = st.number_input("输入退款金额 (RM)", min_value=0.0, max_value=float(order['total']), value=0.0)
        reason = st.text_input("退款原因")
        
        if st.button("提交退款", type="primary"):
            if ref_amount > 0:
                st.session_state.refunds.append({"id": order['id'], "amount": ref_amount, "reason": reason, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                st.success(f"已成功退款 RM {ref_amount:.2f}，该笔支出已计入财务报表。")
                if st.button("完成"): nav('home')
    if st.button("⬅️ 返回主页"): nav('home')

# 【4. 报表中心：消除代码化显示】
elif st.session_state.page == 'report':
    st.title("📊 报表中心")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📥 入账记录")
        if st.session_state.history:
            df_in = pd.DataFrame(st.session_state.history)
            # 格式化：将 rs 字典变成易读文字
            st.table(df_in[['time', 'id', 'name', 'room_list', 'total']])
    with col_b:
        st.subheader("📤 退款记录")
        if st.session_state.refunds:
            st.table(pd.DataFrame(st.session_state.refunds))
        else: st.write("暂无退款")
    
    if st.button("⬅️ 返回"): nav('home')

# 【5. 房价后台：不影响旧订单】
elif st.session_state.page == 'price_admin':
    st.title("⚙️ 房价配置 (不影响已售订单)")
    with st.form("price_admin"):
        cols = st.columns(5)
        new_ps = {}
        for idx, (no, info) in enumerate(st.session_state.rooms_db.items()):
            new_ps[no] = cols[idx].number_input(f"{no}", value=float(info['price']))
        if st.form_submit_button("保存"):
            for no, p in new_ps.items(): st.session_state.rooms_db[no]['price'] = p
            st.success("新房价已生效")
    if st.button("⬅️ 返回"): nav('home')

# 【6. 房态维护】
elif st.session_state.page == 'batch':
    st.title("🧹 房态维护")
    targets = st.multiselect("选择房号", list(st.session_state.rooms_db.keys()))
    new_s = st.selectbox("状态", ["Clean", "Dirty", "OOO"])
    if st.button("更新"):
        for r in targets:
            if not st.session_state.rooms_db[r]['guest']: st.session_state.rooms_db[r]['status'] = new_s
        nav('home')
    if st.button("⬅️ 返回"): nav('home')

# 【7. 批量退房】
elif st.session_state.page == 'out':
    st.title("🔑 批量退房")
    target_guest = st.selectbox("负责人", list(set([v['guest'] for v in st.session_state.rooms_db.values() if v['guest']])))
    if st.button("确认退房"):
        for r, info in st.session_state.rooms_db.items():
            if info['guest'] == target_guest:
                st.session_state.rooms_db[r].update({"guest": None, "guest_ic": None, "status": "Dirty"})
        nav('home')
    if st.button("⬅️ 返回"): nav('home')
