import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 全局配置与初始化 ---
st.set_page_config(page_title="Executive PMS v6.8", layout="wide")

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

# --- 2. 页面逻辑 ---

# 【主页：房态中心】
if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
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

# 【入住登记】
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    t = st.session_state.temp
    can_use = {k: f"{k} ({v['type']}) - RM{v['price']}" for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    if not can_use: st.warning("⚠️ 当前无洁净空房，请先进行房态维护。")
    
    num_others = st.number_input("随行人数", min_value=0, max_value=10, value=len(t.get('others', [])))
    with st.form("checkin_v68"):
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
                booked_rooms = {r: st.session_state.rooms_db[r]['price'] for r in rs}
                st.session_state.temp = {"name": name, "ic": ic, "phone": phone, "email": email, "others": others_list, 
                                        "rs": booked_rooms, "days": (ds[1]-ds[0]).days, "checkin": ds[0], "checkout": ds[1], "id": datetime.now().strftime("%y%m%d%H%M")}
                nav('pay')
            else: st.error("请完善必填信息。")
    if st.button("⬅️ 返回主页"): nav('home')

# 【结算确认页】
elif st.session_state.page == 'pay':
    st.title("💳 账单确认")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("✅ 交易已完成。"); st.button("返回主页", on_click=lambda: nav('home'))
    else:
        bill_data = []
        subtotal = 0
        for r_no, snap_price in t['rs'].items():
            amt = snap_price * t['days']; subtotal += amt
            bill_data.append({"项目": f"房费 - {r_no}", "明细": f"RM {snap_price} × {t['days']} 晚", "金额": f"{amt:.2f}"})
        tax = subtotal * 0.06
        bill_data.append({"项目": "SST 税费 (6%)", "明细": f"RM {subtotal:.2f} × 0.06", "金额": f"{tax:.2f}"})
        bill_data.append({"项目": "离店押金", "明细": "固定金额", "金额": "100.00"})
        total_f = subtotal + tax + 100.0
        st.table(pd.DataFrame(bill_data))
        st.markdown(f"<h2 style='text-align:right; color:#ef4444;'>应付总计: RM {total_f:.2f}</h2>", unsafe_allow_html=True)
        st.divider()
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 支付成功并入住", type="primary"):
            for r in t['rs'].keys(): st.session_state.rooms_db[r].update({"guest": t['name'], "guest_ic": t['ic'], "others": t['others'], "status": "Occupied"})
            st.session_state.history.append({**t, "total": total_f, "room_list": ", ".join(t['rs'].keys()), "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            st.session_state.paid = True; st.rerun()
        if c2.button("❌ 支付失败 (取消订单)"): st.session_state.temp = {}; nav('home')
        if c3.button("⬅️ 返回修改信息"): nav('in')

# 【退款处理：增加退款原因】
elif st.session_state.page == 'refund_page':
    st.title("💸 退款处理")
    if st.session_state.history:
        options = {f"{h['id']} - {h['name']}": i for i, h in enumerate(st.session_state.history)}
        idx = st.selectbox("选择订单", list(options.keys()))
        order = st.session_state.history[options[idx]]
        st.write(f"订单金额: RM {order['total']:.2f}")
        ref_amt = st.number_input("退款金额", min_value=0.0, max_value=float(order['total']))
        ref_reason = st.text_area("退款原因", placeholder="请输入退款原因（如：设施故障、提前退房等）")
        
        if st.button("确认提交退款", type="primary"):
            if ref_amt > 0:
                st.session_state.refunds.append({
                    "id": order['id'], 
                    "name": order['name'],
                    "amount": ref_amt, 
                    "reason": ref_reason,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.success("退款成功！已记录并计入财务。")
                st.button("完成并返回", on_click=lambda: nav('home'))
            else: st.error("退款金额必须大于 0")
    else: st.info("暂无成交历史记录")
    if st.button("⬅️ 返回主页"): nav('home')

# 【报表中心：显示退款原因】
elif st.session_state.page == 'report':
    st.title("📊 报表中心")
    c_in, c_out = st.columns(2)
    with c_in:
        st.write("### 📥 入账记录")
        if st.session_state.history: st.table(pd.DataFrame(st.session_state.history)[['time', 'id', 'name', 'room_list', 'total']])
    with c_out:
        st.write("### 📤 退款记录")
        if st.session_state.refunds: 
            # 确保在表格中显示原因
            st.table(pd.DataFrame(st.session_state.refunds)[['time', 'id', 'name', 'amount', 'reason']])
        else: st.write("暂无退款记录")
    if st.button("⬅️ 返回首页"): nav('home')

# 【房价后台：修复保存 Bug】
elif st.session_state.page == 'price_admin':
    st.title("⚙️ 房价后台配置")
    # 使用临时容器避免表单提交时丢失 session 状态
    with st.form("price_update_form"):
        st.write("修改完成后点击下方按钮保存")
        cols = st.columns(5)
        new_prices_input = {}
        for i, (no, info) in enumerate(st.session_state.rooms_db.items()):
            new_prices_input[no] = cols[i].number_input(f"房号 {no}", value=float(info['price']), step=1.0)
        
        submitted = st.form_submit_button("确认修改并立即生效", type="primary")
        if submitted:
            for no, price in new_prices_input.items():
                st.session_state.rooms_db[no]['price'] = price
            st.success("✅ 房价已成功更新！")
            # 这里的 rerun 确保主页能立即看到新价格
            st.rerun()
    if st.button("⬅️ 返回"): nav('home')

# 【房态维护】
elif st.session_state.page == 'batch':
    st.title("🧹 房态维护")
    rs = st.multiselect("房号", list(st.session_state.rooms_db.keys()))
    st_val = st.selectbox("状态", ["Clean", "Dirty", "OOO"])
    if st.button("执行更新"):
        for r in rs: 
            if not st.session_state.rooms_db[r]['guest']: st.session_state.rooms_db[r]['status'] = st_val
        nav('home')
    if st.button("⬅️ 返回"): nav('home')

# 【批量退房】
elif st.session_state.page == 'out':
    st.title("🔑 批量退房")
    guests = list(set([v['guest'] for v in st.session_state.rooms_db.values() if v['guest']]))
    if guests:
        target = st.selectbox("负责人", guests)
        if st.button("确认一键退房"):
            for r, info in st.session_state.rooms_db.items():
                if info['guest'] == target: st.session_state.rooms_db[r].update({"guest": None, "guest_ic": None, "status": "Dirty"})
            nav('home')
    else: st.info("目前没有在住客人")
    if st.button("⬅️ 返回"): nav('home')
