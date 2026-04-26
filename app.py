import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 初始化 ---
st.set_page_config(page_title="Executive PMS v7.1", layout="wide")

if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "others": []},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "others": []},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None, "guest_ic": None, "others": []},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None, "guest_ic": None, "others": []},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO",   "guest": None, "guest_ic": None, "others": []},
    }
    st.session_state.update({'page': 'home', 'history': [], 'refunds': [], 'temp': {}, 'paid': False})

def nav(target):
    st.session_state.page = target
    st.rerun()

# --- 2. 页面逻辑 ---

if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.title("🏨 鸿蒙智慧酒店管理系统")
    total_in = sum(h['total'] for h in st.session_state.history)
    total_out = sum(r['amount'] for r in st.session_state.refunds)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("入住率", f"{(sum(1 for r in st.session_state.rooms_db.values() if r['guest'])/5)*100:.0f}%")
    c2.metric("净营收", f"RM {total_in - total_out:.2f}")
    c3.metric("总退款", f"RM {total_out:.2f}")
    c4.metric("在线房态", f"{sum(1 for r in st.session_state.rooms_db.values() if r['status']=='Clean' and not r['guest'])} 洁净")

    st.divider()
    cols = st.columns(5)
    for idx, (no, info) in enumerate(st.session_state.rooms_db.items()):
        with cols[idx]:
            is_occ = info['guest'] is not None
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316" if info['status']=="Dirty" else "#64748b")
            st.markdown(f"<div style='padding:15px; border-radius:10px; background:white; border-top:5px solid {color}; box-shadow:0 2px 4px rgba(0,0,0,0.1); min-height:150px;'><b>{no}</b> <small>{info['type']}</small><br><small>RM {info['price']}</small><br><div style='color:{color}; font-weight:bold; margin-top:10px;'>{'👤 '+info['guest'] if is_occ else info['status']}</div></div>", unsafe_allow_html=True)
            
    st.write("")
    menu = st.columns(6)
    if menu[0].button("📝 登记入住", type="primary"): st.session_state.temp = {}; nav('in')
    if menu[1].button("🔑 批量退房"): nav('out')
    if menu[2].button("⚙️ 房价管理"): nav('price_admin')
    if menu[3].button("🧹 房态维护"): nav('batch')
    if menu[4].button("📊 报表中心"): nav('report')
    if menu[5].button("💸 退款处理"): nav('refund_page')

# --- 【修复重点：登记页面的数据抓取】 ---
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    can_use = {k: f"{k} ({v['type']})" for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    
    with st.form("checkin_v71"):
        c1, c2 = st.columns(2)
        name = c1.text_input("主登记人姓名")
        ic = c2.text_input("证件号")
        phone = c1.text_input("手机号")
        email = c2.text_input("邮箱")
        
        st.write("--- 随行人信息 ---")
        num_others = st.number_input("随行人数", 0, 10, 0)
        # 预先定义随行人列表
        temp_others = []
        for i in range(int(num_others)):
            oc1, oc2 = st.columns(2)
            # 关键：显式定义 key 以确保数据被表单捕获
            o_name = oc1.text_input(f"随行人 {i+1} 姓名", key=f"oname_{i}")
            o_ic = oc2.text_input(f"随行人 {i+1} 证件号", key=f"oic_{i}")
            temp_others.append({"name": o_name, "ic": o_ic})
            
        st.write("--- 房间与日期 ---")
        rs = st.multiselect("选择房间 (仅限洁净房)", options=list(can_use.keys()))
        ds = st.date_input("入住起止", value=[date.today(), date.today() + timedelta(1)])
        
        if st.form_submit_button("核算账单"):
            if name and ic and rs and len(ds) == 2:
                # 价格快照锁定
                snap = {r: st.session_state.rooms_db[r]['price'] for r in rs}
                # 将表单内输入的所有数据直接压入 temp
                st.session_state.temp = {
                    "name": name, "ic": ic, "phone": phone, "email": email,
                    "others": temp_others, # 这里直接同步列表
                    "rs": snap, "days": (ds[1]-ds[0]).days, 
                    "id": datetime.now().strftime("%y%m%d%H%M"),
                    "checkin": ds[0], "checkout": ds[1]
                }
                nav('pay')
            else: st.error("请填完所有必填项。")
    if st.button("⬅️ 返回主页"): nav('home')

# --- 【修复重点：展示随行人的详细信息】 ---
elif st.session_state.page == 'pay':
    st.title("💳 账单确认")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("登记成功！"); st.button("返回首页", on_click=lambda: nav('home'))
    else:
        # 展示旅客概览
        st.subheader("旅客信息")
        st.write(f"*主登记人:* {t['name']} ({t['ic']})")
        if t['others']:
            st.write("*随行人员:*")
            # 修复展示逻辑：直接从 temp 的 others 列表中读取
            for i, p in enumerate(t['others']):
                if p['name']: # 只有填了名字才显示
                    st.write(f"- 随行人 {i+1}: {p['name']} (证件: {p['ic']})")
        
        st.divider()
        bill, sub = [], 0
        for r_no, p in t['rs'].items():
            amt = p * t['days']; sub += amt
            bill.append({"项目": f"房间 {r_no}", "明细": f"RM {p} x {t['days']}晚", "金额": f"{amt:.2f}"})
        tax = sub * 0.06
        total_f = sub + tax + 100.0
        st.table(pd.DataFrame(bill + [{"项目": "SST(6%)", "明细": "-", "金额": f"{tax:.2f}"}, {"项目": "押金", "明细": "-", "金额": "100.00"}]))
        st.metric("合计应付", f"RM {total_f:.2f}")

        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 确认支付成功", type="primary"):
            for r in t['rs'].keys():
                st.session_state.rooms_db[r].update({"guest": t['name'], "guest_ic": t['ic'], "others": t['others'], "status": "Occupied"})
            st.session_state.history.append({**t, "total": total_f, "room_list": ", ".join(t['rs'].keys()), "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            st.session_state.paid = True; st.rerun()
        if c2.button("❌ 支付失败 (取消订单)"): st.session_state.temp = {}; nav('home')
        if c3.button("⬅️ 返回修改"): nav('in')

# --- 【修复重点：房价修改立即生效逻辑】 ---
elif st.session_state.page == 'price_admin':
    st.title("⚙️ 房价后台配置")
    st.warning("注意：在此修改价格会立即更新数据库。")
    cols = st.columns(5)
    new_data = {}
    for i, (no, info) in enumerate(st.session_state.rooms_db.items()):
        # 强制使用 session_state 键值绑定
        new_data[no] = cols[i].number_input(f"房号 {no}", value=float(info['price']), key=f"price_set_{no}")
    
    if st.button("确认修改并保存", type="primary"):
        for no, price in new_data.items():
            st.session_state.rooms_db[no]['price'] = price
        st.success("✅ 价格更新成功！")
        if st.button("刷新主页查看"): nav('home')
    if st.button("⬅️ 返回"): nav('home')

# --- 财务与退款逻辑（完全保留原因及报表） ---
elif st.session_state.page == 'refund_page':
    st.title("💸 退款处理")
    if st.session_state.history:
        options = {f"{h['id']} - {h['name']}": i for i, h in enumerate(st.session_state.history)}
        idx = st.selectbox("选择订单", list(options.keys()))
        order = st.session_state.history[options[idx]]
        amt = st.number_input("金额", 0.0, float(order['total']))
        reason = st.text_area("退款原因")
        if st.button("确认退款"):
            st.session_state.refunds.append({"id": order['id'], "name": order['name'], "amount": amt, "reason": reason, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            st.success("已退款"); nav('home')
    if st.button("⬅️ 返回"): nav('home')

elif st.session_state.page == 'report':
    st.title("📊 报表中心")
    c_in, c_out = st.columns(2)
    with c_in:
        st.write("### 📥 入账")
        if st.session_state.history: st.table(pd.DataFrame(st.session_state.history)[['time', 'id', 'name', 'room_list', 'total']])
    with c_out:
        st.write("### 📤 退款 (含原因)")
        if st.session_state.refunds: st.table(pd.DataFrame(st.session_state.refunds)[['time', 'id', 'name', 'amount', 'reason']])
    if st.button("⬅️ 返回"): nav('home')

elif st.session_state.page == 'batch':
    st.title("🧹 房态清洁")
    rs = st.multiselect("房号", list(st.session_state.rooms_db.keys()))
    sv = st.selectbox("状态", ["Clean", "Dirty", "OOO"])
    if st.button("执行"):
        for r in rs: 
            if not st.session_state.rooms_db[r]['guest']: st.session_state.rooms_db[r]['status'] = sv
        nav('home')
    if st.button("⬅️ 返回"): nav('home')

elif st.session_state.page == 'out':
    st.title("🔑 批量退房")
    gs = list(set([v['guest'] for v in st.session_state.rooms_db.values() if v['guest']]))
    if gs:
        target = st.selectbox("负责人", gs)
        if st.button("确认退房"):
            for r, info in st.session_state.rooms_db.items():
                if info['guest'] == target: st.session_state.rooms_db[r].update({"guest": None, "guest_ic": None, "status": "Dirty"})
            nav('home')
    if st.button("⬅️ 返回"): nav('home')
