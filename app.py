import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 初始化与配置 ---
st.set_page_config(page_title="Executive PMS v6.2", layout="wide")

# 初始房间数据（如果不存在则初始化）
if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO",   "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
    }
    st.session_state.update({'page': 'home', 'history': [], 'temp': {}, 'paid': False})

def nav(target):
    st.session_state.page = target
    st.rerun()

# --- 2. 页面逻辑 ---

# 【主页：房态中心】
if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    rooms = st.session_state.rooms_db
    c1, c2, c3 = st.columns(3)
    c1.metric("入住率", f"{(sum(1 for r in rooms.values() if r['guest'])/len(rooms))*100:.0f}%")
    c2.metric("当前在住", f"{sum(1 for r in rooms.values() if r['guest'])} 间")
    
    st.divider()
    cols = st.columns(5)
    for idx, (no, info) in enumerate(rooms.items()):
        with cols[idx]:
            is_occ = info['guest'] is not None
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316")
            st.markdown(f"""
                <div style="padding:15px; border-radius:10px; background:white; border-top:5px solid {color}; box-shadow:0 2px 4px rgba(0,0,0,0.1); min-height:140px;">
                    <b style="font-size:1.1em;">{no}</b> <small>{info['type']}</small><br>
                    <div style="color:gray; font-size:0.85em;">当前房价: RM {info['price']}</div>
                    <div style="color:{color}; font-weight:bold; margin-top:5px;">
                        {f"👤 {info['guest']}" if is_occ else info['status']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    st.write("")
    btns = st.columns(5)
    if btns[0].button("📝 入住登记", type="primary"): st.session_state.temp = {}; nav('in')
    if btns[1].button("🔑 批量退房"): nav('out')
    if btns[2].button("⚙️ 房价管理"): nav('price_admin') # 新增后台入口
    if btns[3].button("🧹 房态维护"): nav('batch')
    if btns[4].button("📊 报表中心"): nav('report')

# 【新增：⚙️ 房价管理后台】
elif st.session_state.page == 'price_admin':
    st.title("⚙️ 后台管理：房价调整")
    st.write("在这里您可以实时修改每个房间的挂牌价格。修改后，新的价格将立即应用于新订单。")
    
    rooms = st.session_state.rooms_db
    
    # 转换为 DataFrame 方便显示
    price_data = []
    for no, info in rooms.items():
        price_data.append({"房号": no, "房型": info['type'], "当前价格 (RM)": info['price']})
    df = pd.DataFrame(price_data)
    
    st.subheader("📊 当前房价概览")
    st.table(df)
    
    st.divider()
    st.subheader("✏️ 快速修改")
    
    with st.form("price_update_form"):
        # 使用 5 列布局，方便对应 5 个房间
        edit_cols = st.columns(5)
        new_prices = {}
        for idx, (no, info) in enumerate(rooms.items()):
            with edit_cols[idx]:
                new_prices[no] = st.number_input(f"房号 {no}", min_value=0.0, value=float(info['price']), step=10.0)
        
        submit_price = st.form_submit_button("确认更新所有价格", type="primary")
        
        if submit_price:
            for no, price in new_prices.items():
                st.session_state.rooms_db[no]['price'] = price
            st.success("✅ 价格更新成功！")
            st.rerun()

    if st.button("⬅️ 返回房态主页"): nav('home')

# 【登记页：逻辑保持 v6.1 稳定版】
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    t = st.session_state.temp
    can_use = {k: f"{k} ({v['type']}) - RM{v['price']}" for k, v in st.session_state.rooms_db.items() if not v['guest'] or k in t.get('rs', [])}

    num_others = st.number_input("随行人数", min_value=0, max_value=10, value=len(t.get('others', [])))

    with st.form("checkin_form_v62"):
        st.subheader("👤 主登记人")
        c1, c2 = st.columns(2)
        name = c1.text_input("姓名", value=t.get('name', ""))
        ic = c2.text_input("证件号", value=t.get('ic', ""))
        phone = c1.text_input("手机号", value=t.get('phone', ""))
        email = c2.text_input("邮箱", value=t.get('email', ""))

        others_list = []
        if num_others > 0:
            st.divider(); st.subheader(f"👥 随行人员 ({num_others}位)")
            for i in range(int(num_others)):
                oc1, oc2 = st.columns(2)
                prev = t.get('others', [])[i] if i < len(t.get('others', [])) else {"name": "", "ic": ""}
                others_list.append({"name": oc1.text_input(f"姓名", key=f"on_{i}", value=prev['name']), 
                                    "ic": oc2.text_input(f"证件号", key=f"oi_{i}", value=prev['ic'])})

        st.divider(); st.subheader("🏨 预订详情")
        rs = st.multiselect("分配房间 (已显示最新房价)", options=list(can_use.keys()), default=t.get('rs', []), format_func=lambda x: can_use[x])
        ds = st.date_input("日期", value=[t.get('checkin', date.today()), t.get('checkout', date.today() + timedelta(1))])

        if st.form_submit_button("去结算确认"):
            if name and ic and phone and rs and len(ds) == 2:
                st.session_state.temp = {"name": name, "ic": ic, "phone": phone, "email": email, "others": others_list, 
                                        "rs": rs, "days": (ds[1]-ds[0]).days, "checkin": ds[0], "checkout": ds[1], "id": datetime.now().strftime("%H%M%S")}
                nav('pay')
            else: st.error("请完善信息")
    if st.button("⬅️ 返回主页"): nav('home')

# 【结算页：自动应用后台修改的价格】
elif st.session_state.page == 'pay':
    st.title("💳 账单确认")
    t = st.session_state.temp
    if not t: nav('home')
    
    if st.session_state.paid:
        st.success("支付成功！"); st.button("查看主页房态", on_click=lambda: nav('home'))
    else:
        # 核心：这里会实时读取房间最新的 price 字段
        base_price = sum(st.session_state.rooms_db[r]['price'] for r in t['rs']) * t['days']
        tax = base_price * 0.06
        total = base_price + tax + 100.0
        
        st.write(f"*负责人:* {t['name']}")
        st.write(f"*房号:* {', '.join(t['rs'])} | *天数:* {t['days']}")
        st.metric("总计金额", f"RM {total:.2f}")

        if st.button("🔥 确认支付", type="primary"):
            for r in t['rs']:
                st.session_state.rooms_db[r].update({"guest": t['name'], "guest_ic": t['ic'], "status": "Occupied", "others": t['others']})
            st.session_state.paid = True
            st.rerun()
        if st.button("⬅️ 返回修改"): nav('in')

# 退房、维护、报表逻辑保持不变...
elif st.session_state.page == 'out':
    st.title("🔑 退房")
    # ... (退房代码逻辑)
    if st.button("⬅️ 返回主页"): nav('home')
elif st.session_state.page == 'batch': nav('home')
elif st.session_state.page == 'report': nav('home')
