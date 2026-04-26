import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 全局配置与初始化 ---
st.set_page_config(page_title="Executive PMS v6.7", layout="wide")

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

# --- 2. 核心页面逻辑 ---

# 【主页：房态中心】
if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    # 财务计算逻辑
    total_in = sum(h['total'] for h in st.session_state.history)
    total_out = sum(r['amount'] for r in st.session_state.refunds)
    net_revenue = total_in - total_out
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("入住率", f"{(sum(1 for r in st.session_state.rooms_db.values() if r['guest'])/5)*100:.0f}%")
    c2.metric("净营收", f"RM {net_revenue:.2f}")
    c3.metric("总退款", f"RM {total_out:.2f}")
    c4.metric("洁净房数", f"{sum(1 for r in st.session_state.rooms_db.values() if r['status']=='Clean')} 间")

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
    btns = st.columns(6) 
    if btns[0].button("📝 入住登记", type="primary"): st.session_state.temp = {}; nav('in')
    if btns[1].button("🔑 批量退房"): nav('out')
    if btns[2].button("⚙️ 房价后台"): nav('price_admin')
    if btns[3].button("🧹 房态维护"): nav('batch')
    if btns[4].button("📊 报表中心"): nav('report')
    if btns[5].button("💸 退款处理"): nav('refund_page')

# 【入住登记：房态强约束】
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    t = st.session_state.temp
    # 仅允许 Clean 且未被占用的房间
    can_use = {k: f"{k} ({v['type']}) - RM{v['price']}" for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    
    if not can_use:
        st.warning("⚠️ 当前无洁净空房，请先进行房态维护。")
    
    num_others = st.number_input("随行人数", min_value=0, max_value=10, value=len(t.get('others', [])))

    with st.form("checkin_v67"):
        c1, c2 = st.columns(2)
        name, ic = c1.text_input("姓名"), c2.text_input("证件号")
        phone, email = c1.text_input("手机号"), c2.text_input("邮箱")
        others_list = []
        for i in range(int(num_others)):
            oc1, oc2 = st.columns(2)
            others_list.append({"name": oc1.text_input(f"随行人{i+1}姓名", key=f"n{i}"), "ic": oc2.text_input(f"随行人{i+1}IC", key=f"i{i}")})
        
        rs = st.multiselect("选择房间", options=list(can_use.keys()), format_func=lambda x: can_use[x])
        ds = st.date_input("入住日期", value=[date.today(), date.today() + timedelta(1)])

        if st.form_submit_button("核算并确认账单"):
            if name and ic and rs and len(ds) == 2:
                # 记录快照单价
                booked_rooms = {r: st.session_state.rooms_db[r]['price'] for r in rs}
                st.session_state.temp = {"name": name, "ic": ic, "phone": phone, "email": email, "others": others_list, 
                                        "rs": booked_rooms, "days": (ds[1]-ds[0]).days, "checkin": ds[0], "checkout": ds[1], "id": datetime.now().strftime("%y%m%d%H%M")}
                nav('pay')
            else: st.error("请完善必填信息。")
    if st.button("⬅️ 返回主页"): nav('home')

# 【结算确认页：添加支付失败按钮】
elif st.session_state.page == 'pay':
    st.title("💳 账单确认")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("✅ 交易已完成，客房状态已更新。"); st.button("返回主页", on_click=lambda: nav('home'))
    else:
        # 显示明细表格
        bill_data = []
        subtotal = 0
        for r_no, snap_price in t['rs'].items():
            amt = snap_price * t['days']
            subtotal += amt
            bill_data.append({"项目": f"房费 - {r_no}", "明细": f"RM {snap_price} × {t['days']} 晚", "金额": f"{amt:.2f}"})
        
        tax = subtotal * 0.06
        bill_data.append({"项目": "SST 税费 (6%)", "明细": f"RM {subtotal:.2f} × 0.06", "金额": f"{tax:.2f}"})
        bill_data.append({"项目": "离店押金", "明细": "固定金额", "金额": "100.00"})
        total_f = subtotal + tax + 100.0
        
        st.table(pd.DataFrame(bill_data))
        st.markdown(f"<h2 style='text-align:right; color:#ef4444;'>应付总计: RM {total_f:.2f}</h2>", unsafe_allow_html=True)

        st.divider()
        # 按钮布局：增加“支付失败”
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 支付成功并入住", type="primary"):
            for r in t['rs'].keys():
                st.session_state.rooms_db[r].update({"guest": t['name'], "guest_ic": t['ic'], "others": t['others'], "status": "Occupied"})
            st.session_state.history.append({**t, "total": total_f, "room_list": ", ".join(t['rs'].keys()), "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            st.session_state.paid = True
            st.rerun()
        
        # 新增按钮：支付失败并直接返回主页
        if c2.button("❌ 支付失败 (取消订单)"):
            st.warning("支付未完成，正在返回主页面...")
            st.session_state.temp = {} # 清空临时预订数据
            nav('home')
            
        if c3.button("⬅️ 返回修改信息"): nav('in')

# 【其余功能保持不变】
elif st.session_state.page == 'refund_page':
    st.title("💸 退款处理")
    if st.session_state.history:
        options = {f"{h['id']} - {h['name']}": i for i, h in enumerate(st.session_state.history)}
        idx = st.selectbox("选择订单", list(options.keys()))
        order = st.session_state.history[options[idx]]
        ref_amt = st.number_input("退款金额", max_value=float(order['total']))
        if st.button("确认退款"):
            st.session_state.refunds.append({"id": order['id'], "amount": ref_amt, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            st.success("退款成功！"); st.button("刷新", on_click=lambda: nav('home'))
    if st.button("⬅️ 返回"): nav('home')

elif st.session_state.page == 'report':
    st.title("📊 报表中心")
    c_in, c_out = st.columns(2)
    with c_in:
        st.write("### 入账记录")
        if st.session_state.history: st.table(pd.DataFrame(st.session_state.history)[['time', 'id', 'name', 'room_list', 'total']])
    with c_out:
        st.write("### 退款记录")
        if st.session_state.refunds: st.table(pd.DataFrame(st.session_state.refunds))
    if st.button("⬅️ 返回首页"): nav('home')

elif st.session_state.page == 'price_admin':
    st.title("⚙️ 房价后台配置")
    with st.form("price"):
        cols = st.columns(5)
        new_ps = {no: cols[i].number_input(no, value=float(info['price'])) for i, (no, info) in enumerate(st.session_state.rooms_db.items())}
        if st.form_submit_button("确认修改"):
            for no, p in new_ps.items(): st.session_state.rooms_db[no]['price'] = p
            st.success("更新成功"); st.rerun()
    if st.button("⬅️ 返回"): nav('home')

elif st.session_state.page == 'batch':
    st.title("🧹 房态维护")
    rs = st.multiselect("房号", list(st.session_state.rooms_db.keys()))
    st_val = st.selectbox("状态", ["Clean", "Dirty", "OOO"])
    if st.button("执行"):
        for r in rs: 
            if not st.session_state.rooms_db[r]['guest']: st.session_state.rooms_db[r]['status'] = st_val
        nav('home')
    if st.button("⬅️ 返回"): nav('home')

elif st.session_state.page == 'out':
    st.title("🔑 批量退房")
    guests = list(set([v['guest'] for v in st.session_state.rooms_db.values() if v['guest']]))
    target = st.selectbox("负责人", guests)
    if st.button("确认退房"):
        for r, info in st.session_state.rooms_db.items():
            if info['guest'] == target: st.session_state.rooms_db[r].update({"guest": None, "guest_ic": None, "status": "Dirty"})
        nav('home')
    if st.button("⬅️ 返回"): nav('home')
