import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 全局配置与高级样式 ---
st.set_page_config(page_title="HOTEL SYSTEM", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.2em; font-weight: 600; }
    .room-card {
        padding: 20px; border-radius: 15px; background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 8px solid #ddd;
        margin-bottom: 15px; min-height: 150px;
    }
    .info-label { font-size: 0.82em; color: #64748b; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)

# 保持五位房间配置不变
if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO",   "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
    }
    st.session_state.update({'page': 'home', 'history': [], 'audit_logs': [], 'temp': {}, 'paid': False})

def nav(target):
    st.session_state.page = target
    st.rerun()

def add_log(action, detail):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.audit_logs.append({"时间": now, "操作": action, "详情": detail})

# --- 2. 页面逻辑控制 ---

# 【主页：房态中心】
if st.session_state.page == 'home':
    st.session_state.paid = False
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    rooms = st.session_state.rooms_db
    paid_total = sum(h['total'] for h in st.session_state.history if h.get('status') == "已支付")
    refunded_total = sum(h['total'] for h in st.session_state.history if h.get('status') == "已退款")
    net_revenue = max(0.0, paid_total - refunded_total)

    c1, c2, c3 = st.columns(3)
    c1.metric("入住率", f"{(sum(1 for r in rooms.values() if r['guest'])/len(rooms))*100:.1f}%")
    c2.metric("净营收", f"RM {net_revenue:.2f}")
    c3.metric("待清扫房间", f"{sum(1 for r in rooms.values() if r['status']=='Dirty')} 间")

    st.divider()
    room_cols = st.columns(5) # 始终保持5列显示
    for idx, (no, info) in enumerate(rooms.items()):
        with room_cols[idx]:
            is_occ = info['guest'] is not None
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316" if info['status']=="Dirty" else "#64748b")
            st.markdown(f"""<div class="room-card" style="border-top-color: {color};">
                <div style="font-size:1.2em;font-weight:800;">{no} <small style="font-weight:400;font-size:0.6em;">{info['type']}</small></div>
                <div style="color:{color};font-weight:700;margin-top:8px;">{f"👤 {info['guest']}" if is_occ else info['status']}</div>
                {f'<div class="info-label">IC: {info["guest_ic"]}</div>' if is_occ else ''}
                {f'<div class="info-label">同行: {len(info["others"])}人</div>' if is_occ and info["others"] else ''}
                </div>""", unsafe_allow_html=True)

    st.write("")
    nav_btns = st.columns(4)
    if nav_btns[0].button("📝 入住登记", type="primary"): st.session_state.temp = {}; nav('in')
    if nav_btns[1].button("🔑 批量退房"): nav('out')
    if nav_btns[2].button("🧹 批量维护"): nav('batch')
    if nav_btns[3].button("📊 报表与退款"): nav('report')

# 【1. 入住登记：动态多住客登记】
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    t = st.session_state.temp
    can_use = {k: f"{k} ({v['type']})" for k, v in st.session_state.rooms_db.items() if (v['status'] == 'Clean' and not v['guest']) or k in t.get('rs', [])}
    
    with st.form("comprehensive_checkin"):
        st.subheader("👤 主登记人 (负责人)")
        c1, c2, c3 = st.columns(3)
        m_name = c1.text_input("姓名", value=t.get('name', ""))
        m_ic = c2.text_input("证件号", value=t.get('ic', ""))
        m_phone = c3.text_input("手机号", value=t.get('phone', ""))
        m_email = st.text_input("邮箱地址", value=t.get('email', ""))
        
        st.divider()
        st.subheader("👥 随行人员登记")
        num_others = st.number_input("随行人数", min_value=0, max_value=10, value=len(t.get('others', [])))
        
        others_data = []
        for i in range(int(num_others)):
            st.markdown(f"*随行人员 {i+1}*")
            oc1, oc2 = st.columns(2)
            prev = t.get('others', [])[i] if i < len(t.get('others', [])) else {"name": "", "ic": ""}
            o_name = oc1.text_input(f"姓名", key=f"oname_{i}", value=prev['name'])
            o_ic = oc2.text_input(f"证件号", key=f"oic_{i}", value=prev['ic'])
            others_data.append({"name": o_name, "ic": o_ic})

        st.divider()
        st.subheader("🏨 房间与租期")
        rs = st.multiselect("分配房间", options=list(can_use.keys()), default=t.get('rs', []), format_func=lambda x: can_use[x])
        ds = st.date_input("入住/退房日期", value=[t.get('checkin', date.today()), t.get('checkout', date.today() + timedelta(1))])
        
        if st.form_submit_button("核算并支付"):
            if m_name and m_ic and m_phone and rs and len(ds) == 2:
                st.session_state.temp = {
                    "name": m_name, "ic": m_ic, "phone": m_phone, "email": m_email,
                    "others": others_data, "rs": rs, "days": (ds[1]-ds[0]).days,
                    "checkin": ds[0], "checkout": ds[1], "id": t.get('id', datetime.now().strftime("%Y%m%d%H%M%S"))
                }
                nav('pay')
            else: st.error("请确保主登记人信息完整且已选房")
            
    st.write("---")
    if st.button("⬅️ 取消并返回首页"): st.session_state.temp = {}; nav('home')

# 【2. 结算页】
elif st.session_state.page == 'pay':
    st.title("💳 账单确认")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("✅ 支付成功！")
        if st.button("进入房态主页", type="primary"): st.session_state.temp = {}; nav('home')
    elif not t: nav('home')
    else:
        with st.container(border=True):
            st.subheader(f"负责人: {t['name']} ({t['ic']})")
            if t['others']:
                st.write("*随行人员清单:*")
                st.table(pd.DataFrame(t['others']))
            
            base = sum(st.session_state.rooms_db[r]['price'] for r in t['rs']) * t['days']
            sst, ttax = base * 0.06, 10.0 * len(t['rs']) * t['days']
            total = base + sst + ttax + 100.0
            st.markdown(f"### 应收总额: RM {total:.2f}")

        cb = st.columns(3)
        if cb[0].button("✅ 确认支付", type="primary"):
            for r in t['rs']: 
                st.session_state.rooms_db[r].update({
                    "guest": t['name'], "guest_ic": t['ic'], "phone": t['phone'], 
                    "email": t['email'], "others": t['others'], "status": "Dirty"
                })
            st.session_state.history.append({**t, "total": total, "status": "已支付"})
            add_log("办理入住", f"住客 {t['name']} 入住房间 {', '.join(t['rs'])}")
            st.session_state.paid = True
            st.rerun()
        if cb[1].button("⬅️ 修改信息"): nav('in')
        if cb[2].button("❌ 取消办理"): st.session_state.temp = {}; nav('home')

# 【3. 批量退房：显示全员信息】
elif st.session_state.page == 'out':
    st.title("🔑 离店退房管理")
    unique_guests = {}
    for r, info in st.session_state.rooms_db.items():
        if info['guest']:
            label = f"{info['guest']} (IC: {info['guest_ic']})"
            if label not in unique_guests:
                unique_guests[label] = {"rooms": [], "others": [], "phone": info['phone']}
            unique_guests[label]["rooms"].append(r)
            unique_guests[label]["others"] = info['others']

    if unique_guests:
        target = st.selectbox("选择要退房的订单主登记人", list(unique_guests.keys()))
        data = unique_guests[target]
        
        with st.container(border=True):
            st.markdown("#### 📄 离店核对表")
            col_a, col_b = st.columns(2)
            col_a.write(f"*主住客:* {target}")
            col_a.write(f"*联系电话:* {data['phone']}")
            col_b.write(f"*占用房号:* {', '.join(data['rooms'])}")
            
            st.write("*所有入住人员名单 (含随行):*")
            # 合并主住客和随行人员到一个列表显示
            all_people = [{"身份": "主登记人", "姓名": target.split(" (")[0], "证件号": target.split("IC: ")[1].replace(")", "")}]
            for o in data['others']:
                if o['name']: all_people.append({"身份": "随行人员", "姓名": o['name'], "证件号": o['ic']})
            st.table(pd.DataFrame(all_people))

        if st.button("确认一键退房", type="primary"):
            for r in data['rooms']:
                st.session_state.rooms_db[r].update({"guest": None, "guest_ic": None, "others": [], "phone": "", "email": "", "status": "Dirty"})
            add_log("退房", f"{target} 订单已结账")
            st.success("退房成功！房间已释放为待清扫状态。")
            if st.button("返回主页"): nav('home')
    else: st.info("目前无在住旅客")
    
    st.write("---")
    if st.button("⬅️ 返回主页"): nav('home')

# 【4. 批量维护与报表】略 (保持 v5.8 精简版)
elif st.session_state.page == 'batch':
    st.title("🧹 房态批量维护")
    all_rs = list(st.session_state.rooms_db.keys())
    targets = st.multiselect("选择房间", all_rs)
    new_s = st.selectbox("目标状态", ["Clean", "Dirty", "OOO"])
    if st.button("更新房态"):
        for r in targets: 
            if not st.session_state.rooms_db[r]['guest']: st.session_state.rooms_db[r]['status'] = new_s
        nav('home')
    if st.button("返回"): nav('home')

elif st.session_state.page == 'report':
    st.title("📊 报表中心")
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history)[['id', 'name', 'ic', 'phone', 'total', 'status']])
    else: st.info("暂无历史记录")
    if st.button("⬅️ 返回主页"): nav('home')
