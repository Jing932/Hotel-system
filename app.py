import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 配置与样式 ---
st.set_page_config(page_title="Hotel System", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.2em; font-weight: 600; }
    .room-card {
        padding: 20px; border-radius: 15px; background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 8px solid #ddd;
        margin-bottom: 15px; min-height: 140px;
    }
    .info-label { font-size: 0.85em; color: #64748b; }
    </style>
    """, unsafe_allow_html=True)

# 数据初始化 (增加 others 字段存储随行人员)
if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        f"{i}{j:02d}": {"type": "大床房" if i==1 else "双床房", "price": 200.0 if i==1 else 250.0, 
                       "status": "Clean", "guest": None, "guest_ic": None, "others": []}
        for i in range(1, 3) for j in range(1, 4)
    }
    st.session_state.update({'page': 'home', 'history': [], 'audit_logs': [], 'temp': {}, 'paid': False})

def nav(target):
    st.session_state.page = target
    st.rerun()

def add_log(action, detail):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.audit_logs.append({"时间": now, "操作": action, "详情": detail})

# --- 2. 页面逻辑控制 ---

# 【主页】略 (保持 v5.7 逻辑)
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
    c3.metric("待清扫", f"{sum(1 for r in rooms.values() if r['status']=='Dirty')} 间")

    st.divider()
    room_cols = st.columns(5)
    for idx, (no, info) in enumerate(rooms.items()):
        with room_cols[idx % 5]:
            is_occ = info['guest'] is not None
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316" if info['status']=="Dirty" else "#64748b")
            st.markdown(f"""<div class="room-card" style="border-top-color: {color};">
                <div style="font-size:1.2em;font-weight:800;">{no} <small style="font-weight:400;font-size:0.6em;">{info['type']}</small></div>
                <div style="color:{color};font-weight:700;margin-top:8px;">{f"👤 {info['guest']}" if is_occ else info['status']}</div>
                {f'<div class="info-label">IC: {info["guest_ic"]}</div>' if is_occ else ''}
                </div>""", unsafe_allow_html=True)

    st.write("")
    nav_btns = st.columns(4)
    if nav_btns[0].button("📝 入住登记", type="primary"): st.session_state.temp = {}; nav('in')
    if nav_btns[1].button("🔑 批量退房"): nav('out')
    if nav_btns[2].button("🧹 批量维护"): nav('batch')
    if nav_btns[3].button("📊 报表与退款"): nav('report')

# 【1. 登记页】(支持多位住客、手机、邮箱)
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    t = st.session_state.temp
    can_use = {k: f"{k} ({v['type']})" for k, v in st.session_state.rooms_db.items() if (v['status'] == 'Clean' and not v['guest']) or k in t.get('rs', [])}
    
    with st.form("checkin_form"):
        col1, col2, col3 = st.columns(3)
        m_name = col1.text_input("主登记人姓名", value=t.get('name', ""))
        m_ic = col2.text_input("证件号", value=t.get('ic', ""))
        m_phone = col3.text_input("手机号", value=t.get('phone', ""))
        m_email = st.text_input("电子邮箱", value=t.get('email', ""))
        
        st.write("---")
        num_others = st.number_input("随行人数", min_value=0, max_value=5, value=len(t.get('others', [])))
        others_list = []
        for i in range(int(num_others)):
            oc1, oc2 = st.columns(2)
            prev = t.get('others', [])[i] if i < len(t.get('others', [])) else {"name": "", "ic": ""}
            o_n = oc1.text_input(f"随行人 {i+1} 姓名", key=f"on_{i}", value=prev['name'])
            o_i = oc2.text_input(f"随行人 {i+1} 证件号", key=f"oi_{i}", value=prev['ic'])
            others_list.append({"name": o_n, "ic": o_i})
        
        st.write("---")
        rs = st.multiselect("分配房间", options=list(can_use.keys()), default=t.get('rs', []), format_func=lambda x: can_use[x])
        ds = st.date_input("日期", value=[t.get('checkin', date.today()), t.get('checkout', date.today() + timedelta(1))])
        
        if st.form_submit_button("核算账单"):
            if m_name and m_ic and rs and len(ds) == 2:
                st.session_state.temp = {"name":m_name, "ic":m_ic, "phone":m_phone, "email":m_email, "others": others_list, 
                                        "rs":rs, "days":(ds[1]-ds[0]).days, "checkin":ds[0], "checkout":ds[1], 
                                        "id":t.get('id', datetime.now().strftime("%Y%m%d%H%M%S"))}
                nav('pay')
            else: st.error("请完整填写必要信息")
    if st.button("⬅️ 返回主页"): st.session_state.temp = {}; nav('home')

# 【2. 结算页】
elif st.session_state.page == 'pay':
    st.title("💳 账单确认")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("✅ 支付成功！")
        if st.button("回到首页", type="primary"): st.session_state.temp = {}; nav('home')
    elif not t: nav('home')
    else:
        with st.container(border=True):
            st.subheader(f"住客: {t['name']} ({t['ic']})")
            if t['others']: 
                st.write("*随行人员:* " + ", ".join([o['name'] for o in t['others'] if o['name']]))
            base = sum(st.session_state.rooms_db[r]['price'] for r in t['rs']) * t['days']
            total = base + (base * 0.06) + (10.0 * len(t['rs']) * t['days']) + 100.0
            st.table(pd.DataFrame([{"房号": r, "金额": f"RM {st.session_state.rooms_db[r]['price'] * t['days']}"} for r in t['rs']]))
            st.markdown(f"### 总额: RM {total:.2f}")

        c_btns = st.columns(3)
        if c_btns[0].button("✅ 确认支付", type="primary"):
            for r in t['rs']: st.session_state.rooms_db[r].update({"guest": t['name'], "guest_ic": t['ic'], "others": t['others'], "status": "Dirty"})
            st.session_state.history.append({**t, "total": total, "status": "已支付"})
            add_log("入住", f"{t['name']} ({t['ic']}) 已入住")
            st.session_state.paid = True
            st.rerun()
        if c_btns[1].button("⬅️ 修改信息"): nav('in')
        if c_btns[2].button("❌ 取消"): st.session_state.temp = {}; nav('home')

# 【3. 批量退房页 - 这里会显示多人的名字吗？答：会！】
elif st.session_state.page == 'out':
    st.title("🔑 离店退房管理")
    
    # 建立映射：标签 -> (房间列表, 随行人名单)
    guest_data = {}
    for r, info in st.session_state.rooms_db.items():
        if info['guest']:
            # 用 主住客姓名 + IC 作为 Key 确保唯一
            label = f"{info['guest']} (IC: {info['guest_ic']})"
            if label not in guest_data:
                guest_data[label] = {"rooms": [], "others": []}
            guest_data[label]["rooms"].append(r)
            guest_data[label]["others"] = info['others']
    
    if guest_data:
        target_label = st.selectbox("选择办理退房的住客 (按主登记人搜索)", list(guest_data.keys()))
        data = guest_data[target_label]
        
        # --- 这里回答了你的问题：显示所有人的名字 ---
        with st.container(border=True):
            st.markdown(f"### 📋 订单详情")
            st.write(f"*主登记人:* {target_label}")
            
            # 显示随行人员的名字
            if data["others"]:
                names = [o['name'] for o in data["others"] if o['name']]
                st.write(f"*随行人员:* {', '.join(names) if names else '无记录'}")
            else:
                st.write("*随行人员:* 无")
                
            st.write(f"*占用房号:* {', '.join(data['rooms'])}")
        
        if st.button("确认一键退房并释放房间", type="primary"):
            for r in data["rooms"]:
                st.session_state.rooms_db[r].update({"guest": None, "guest_ic": None, "others": [], "status": "Dirty"})
            add_log("退房", f"{target_label} 及其随行人已离店")
            st.success("退房操作成功！")
            if st.button("点此完成并返回"): nav('home')
    else:
        st.info("当前酒店内无在住旅客。")
    
    st.write("---")
    if st.button("⬅️ 返回主页"): nav('home')

# 【4. 批量维护】略
# 【5. 报表中心】略 (保持 v5.7 逻辑)
elif st.session_state.page == 'batch':
    st.title("🧹 房态维护")
    all_rs = list(st.session_state.rooms_db.keys())
    targets = st.multiselect("选择房间", all_rs)
    new_s = st.selectbox("目标状态", ["Clean", "Dirty", "OOO"])
    if st.button("更新"):
        for r in targets: 
            if not st.session_state.rooms_db[r]['guest']: st.session_state.rooms_db[r]['status'] = new_s
        nav('home')
    if st.button("返回"): nav('home')

elif st.session_state.page == 'report':
    st.title("📊 报表中心")
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history)[['id', 'name', 'ic', 'phone', 'total', 'status']])
    if st.button("返回主页"): nav('home')
