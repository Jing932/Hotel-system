import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 配置 ---
st.set_page_config(page_title="Executive PMS v6.0", layout="wide")

# 样式
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3.2em; font-weight: 600; }
    .room-card {
        padding: 20px; border-radius: 15px; background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 8px solid #ddd;
        margin-bottom: 15px; min-height: 150px;
    }
    </style>
    """, unsafe_allow_html=True)

# 保持固定5间房
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

# --- 2. 页面逻辑 ---

# 【主页】
if st.session_state.page == 'home':
    st.title("🏨 鸿蒙智慧酒店管理系统")
    # (主页逻辑保持不变，确保5个房间显示)
    rooms = st.session_state.rooms_db
    c1, c2, c3 = st.columns(3)
    c1.metric("入住率", f"{(sum(1 for r in rooms.values() if r['guest'])/len(rooms))*100:.1f}%")
    st.divider()
    room_cols = st.columns(5)
    for idx, (no, info) in enumerate(rooms.items()):
        with room_cols[idx]:
            is_occ = info['guest'] is not None
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316" if info['status']=="Dirty" else "#64748b")
            st.markdown(f"""<div class="room-card" style="border-top-color: {color};">
                <b>{no}</b> ({info['type']})<br>
                <span style="color:{color};">{f'👤 {info["guest"]}' if is_occ else info['status']}</span>
                </div>""", unsafe_allow_html=True)
    st.write("")
    btns = st.columns(4)
    if btns[0].button("📝 入住登记", type="primary"): st.session_state.temp = {}; nav('in')
    if btns[1].button("🔑 批量退房"): nav('out')
    if btns[2].button("🧹 批量维护"): nav('batch')
    if btns[3].button("📊 报表中心"): nav('report')

# 【1. 入住登记：改进即时动态表单】
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    t = st.session_state.temp
    can_use = {k: f"{k} ({v['type']})" for k, v in st.session_state.rooms_db.items() if (v['status'] == 'Clean' and not v['guest']) or k in t.get('rs', [])}
    
    # --- 核心改进：将人数选择放在 Form 之外 ---
    st.subheader("👥 随行人数确认")
    current_num_others = st.number_input(
        "请先选择随行人数（不含主登记人），下方登记表将自动刷新", 
        min_value=0, max_value=10, 
        value=len(t.get('others', []))
    )

    # 开启表单
    with st.form("dynamic_checkin_form"):
        st.subheader("👤 主登记人信息")
        c1, c2, c3 = st.columns(3)
        m_name = c1.text_input("姓名", value=t.get('name', ""))
        m_ic = c2.text_input("证件号", value=t.get('ic', ""))
        m_phone = c3.text_input("手机号", value=t.get('phone', ""))
        m_email = st.text_input("邮箱地址", value=t.get('email', ""))
        
        st.divider()
        st.subheader(f"👥 随行人员登记 ({current_num_others} 位)")
        
        others_data = []
        for i in range(int(current_num_others)):
            st.markdown(f"*随行人员 {i+1}*")
            oc1, oc2 = st.columns(2)
            # 尽量回填数据
            prev = t.get('others', [])[i] if i < len(t.get('others', [])) else {"name": "", "ic": ""}
            o_name = oc1.text_input(f"姓名", key=f"oname_{i}", value=prev['name'])
            o_ic = oc2.text_input(f"证件号", key=f"oic_{i}", value=prev['ic'])
            others_data.append({"name": o_name, "ic": o_ic})

        st.divider()
        st.subheader("🏨 房间与租期")
        rs = st.multiselect("分配房间", options=list(can_use.keys()), default=t.get('rs', []), format_func=lambda x: can_use[x])
        ds = st.date_input("入住/退房日期", value=[t.get('checkin', date.today()), t.get('checkout', date.today() + timedelta(1))])
        
        # 提交按钮
        submit = st.form_submit_button("核算账单并下一步", type="primary")
        
        if submit:
            if m_name and m_ic and m_phone and rs and len(ds) == 2:
                st.session_state.temp = {
                    "name": m_name, "ic": m_ic, "phone": m_phone, "email": m_email,
                    "others": others_data, "rs": rs, "days": (ds[1]-ds[0]).days,
                    "checkin": ds[0], "checkout": ds[1], "id": t.get('id', datetime.now().strftime("%Y%m%d%H%M%S"))
                }
                nav('pay')
            else:
                st.error("❗ 请确保主登记人信息完整且已选择房间。")

    st.write("---")
    if st.button("⬅️ 返回主页"): st.session_state.temp = {}; nav('home')

# 【2. 结算页】
elif st.session_state.page == 'pay':
    st.title("💳 确认账单")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("支付成功！")
        if st.button("回到主页"): nav('home')
    else:
        st.write(f"负责人: {t['name']} | 随行: {len(t['others'])}人")
        st.table(pd.DataFrame(t['others']))
        if st.button("✅ 确认支付"):
            for r in t['rs']:
                st.session_state.rooms_db[r].update({
                    "guest": t['name'], "guest_ic": t['ic'], "phone": t['phone'], 
                    "email": t['email'], "others": t['others'], "status": "Dirty"
                })
            st.session_state.history.append({**t, "total": 200.0, "status": "已支付"}) # 简化金额计算
            st.session_state.paid = True
            st.rerun()
        if st.button("⬅️ 修改信息"): nav('in')

# 【3. 批量退房】
elif st.session_state.page == 'out':
    st.title("🔑 离店退房")
    unique_guests = {}
    for r, info in st.session_state.rooms_db.items():
        if info['guest']:
            label = f"{info['guest']} (IC: {info['guest_ic']})"
            unique_guests.setdefault(label, []).append(r)
    
    if unique_guests:
        target = st.selectbox("选择主登记人", list(unique_guests.keys()))
        # 获取随行人
        sample_room = unique_guests[target][0]
        others = st.session_state.rooms_db[sample_room]['others']
        
        st.info(f"房号: {', '.join(unique_guests[target])}")
        st.write("*入住名单 (包含随行人员):*")
        all_list = [{"姓名": target.split(" (")[0], "证件号": target.split("IC: ")[1][:-1]}]
        for o in others: all_list.append({"姓名": o['name'], "证件号": o['ic']})
        st.table(pd.DataFrame(all_list))
        
        if st.button("确认退房"):
            for r in unique_guests[target]:
                st.session_state.rooms_db[r].update({"guest": None, "guest_ic": None, "others": [], "status": "Dirty"})
            st.success("退房成功")
            if st.button("完成"): nav('home')
    else: st.info("空房中")
    if st.button("⬅️ 返回"): nav('home')

# 【报表与维护逻辑略】
elif st.session_state.page == 'batch': nav('home')
elif st.session_state.page == 'report': nav('home')
