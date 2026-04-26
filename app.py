import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 初始化与配置 ---
st.set_page_config(page_title="Executive PMS v6.3", layout="wide")

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

# 【主页：房态中心】 (保持 5 间房)
if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.title("🏨 鸿蒙智慧酒店管理系统")
    rooms = st.session_state.rooms_db
    st.divider()
    cols = st.columns(5)
    for idx, (no, info) in enumerate(rooms.items()):
        with cols[idx]:
            is_occ = info['guest'] is not None
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316")
            st.markdown(f"""
                <div style="padding:15px; border-radius:10px; background:white; border-top:5px solid {color}; box-shadow:0 2px 4px rgba(0,0,0,0.1); min-height:140px;">
                    <b style="font-size:1.1em;">{no}</b> <small>{info['type']}</small><br>
                    <div style="color:gray; font-size:0.85em;">价格: RM {info['price']}</div>
                    <div style="color:{color}; font-weight:bold; margin-top:5px;">{f"👤 {info['guest']}" if is_occ else info['status']}</div>
                </div>
            """, unsafe_allow_html=True)
    st.write("")
    btns = st.columns(5)
    if btns[0].button("📝 入住登记", type="primary"): nav('in')
    if btns[1].button("🔑 批量退房"): nav('out')
    if btns[2].button("⚙️ 房价管理"): nav('price_admin')
    if btns[3].button("🧹 房态维护"): nav('batch')
    if btns[4].button("📊 报表中心"): nav('report')

# 【后台：房价管理】 (保持逻辑)
elif st.session_state.page == 'price_admin':
    st.title("⚙️ 房价后台管理")
    with st.form("price_update"):
        edit_cols = st.columns(5)
        new_prices = {}
        for idx, (no, info) in enumerate(st.session_state.rooms_db.items()):
            with edit_cols[idx]:
                new_prices[no] = st.number_input(f"房号 {no}", min_value=0.0, value=float(info['price']))
        if st.form_submit_button("确认更新"):
            for no, p in new_prices.items(): st.session_state.rooms_db[no]['price'] = p
            st.rerun()
    if st.button("⬅️ 返回主页"): nav('home')

# 【入住登记】 (保持逻辑)
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    t = st.session_state.temp
    can_use = {k: f"{k} ({v['type']})" for k, v in st.session_state.rooms_db.items() if not v['guest'] or k in t.get('rs', [])}
    num_others = st.number_input("随行人数", min_value=0, max_value=10, value=len(t.get('others', [])))
    with st.form("checkin_v63"):
        c1, c2 = st.columns(2)
        name, ic = c1.text_input("姓名"), c2.text_input("证件号")
        phone, email = c1.text_input("手机号"), c2.text_input("邮箱")
        others_list = []
        for i in range(int(num_others)):
            oc1, oc2 = st.columns(2)
            others_list.append({"姓名": oc1.text_input(f"随行人{i+1}姓名", key=f"n{i}"), "证件号": oc2.text_input(f"随行人{i+1}IC", key=f"i{i}")})
        rs = st.multiselect("分配房间", options=list(can_use.keys()), format_func=lambda x: can_use[x])
        ds = st.date_input("入住日期", value=[date.today(), date.today() + timedelta(1)])
        if st.form_submit_button("生成账单明细"):
            if name and ic and rs and len(ds) == 2:
                st.session_state.temp = {"name": name, "ic": ic, "phone": phone, "email": email, "others": others_list, "rs": rs, "days": (ds[1]-ds[0]).days, "checkin": ds[0], "checkout": ds[1]}
                nav('pay')
    if st.button("⬅️ 取消"): nav('home')

# 【结算页：完美表格明细】
elif st.session_state.page == 'pay':
    st.title("💳 账单确认明细")
    t = st.session_state.temp
    if not t: nav('home')
    
    if st.session_state.paid:
        st.success("✅ 支付成功！"); st.button("回到主页", on_click=lambda: nav('home'))
    else:
        st.subheader("📋 预订信息摘要")
        st.write(f"*负责人:* {t['name']} | *证件号:* {t['ic']} | *租期:* {t['checkin']} 至 {t['checkout']} ({t['days']} 晚)")
        
        # --- 构建完美账单表格 ---
        bill_items = []
        subtotal_rooms = 0
        
        # 1. 计算房费明细
        for r_no in t['rs']:
            unit_price = st.session_state.rooms_db[r_no]['price']
            amount = unit_price * t['days']
            subtotal_rooms += amount
            bill_items.append({
                "项目名称": f"房费 - 房间 {r_no} ({st.session_state.rooms_db[r_no]['type']})",
                "详情": f"RM {unit_price} × {t['days']} 晚",
                "金额 (RM)": f"{amount:.2f}"
            })
        
        # 2. 计算税费 (6% SST)
        sst_tax = subtotal_rooms * 0.06
        bill_items.append({"项目名称": "服务税 (SST 6%)", "详情": f"RM {subtotal_rooms:.2f} × 0.06", "金额 (RM)": f"{sst_tax:.2f}"})
        
        # 3. 押金 (固定)
        deposit = 100.0
        bill_items.append({"项目名称": "入住押金 (可退)", "详情": "固定按单收取", "金额 (RM)": f"{deposit:.2f}"})
        
        # 4. 合计
        total_final = subtotal_rooms + sst_tax + deposit
        
        # 显示表格
        bill_df = pd.DataFrame(bill_items)
        st.table(bill_df)
        
        # 底部醒目总计
        st.markdown(f"""
            <div style="text-align: right; padding: 20px; background: #f0f2f6; border-radius: 10px;">
                <span style="font-size: 1.2em; color: #555;">应付总额：</span>
                <span style="font-size: 2em; color: #ef4444; font-weight: bold;">RM {total_final:.2f}</span>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("🔥 确认支付并完成登记", type="primary"):
            for r in t['rs']:
                st.session_state.rooms_db[r].update({"guest": t['name'], "guest_ic": t['ic'], "others": t['others'], "status": "Occupied"})
            st.session_state.history.append({**t, "total": total_final, "status": "已支付"})
            st.session_state.paid = True
            st.rerun()
        if c2.button("⬅️ 返回修改信息"): nav('in')

# 其余页面略
elif st.session_state.page == 'out': nav('home')
elif st.session_state.page == 'batch': nav('home')
elif st.session_state.page == 'report': nav('home')
