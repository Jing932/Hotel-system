import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 全局配置与样式 ---
st.set_page_config(page_title="Executive PMS v6.5", layout="wide")

# 初始化数据库：确保 5 间房固定不变
if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO",   "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
    }
    st.session_state.update({'page': 'home', 'history': [], 'temp': {}, 'paid': False})

# 统一跳转函数：避免 Callback 警告
def nav(target):
    st.session_state.page = target
    st.rerun()

# --- 2. 页面逻辑控制 ---

# 【主页：房态中心】
if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    rooms = st.session_state.rooms_db
    # 营收计算逻辑
    revenue = sum(h['total'] for h in st.session_state.history if h.get('status') == "已支付")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("入住率", f"{(sum(1 for r in rooms.values() if r['guest'])/len(rooms))*100:.0f}%")
    c2.metric("营收总计", f"RM {revenue:.2f}")
    c3.metric("房态监控", f"{sum(1 for r in rooms.values() if r['guest'])} 占用 / 5 总计")

    st.divider()
    # 房态格子渲染
    cols = st.columns(5)
    for idx, (no, info) in enumerate(rooms.items()):
        with cols[idx]:
            is_occ = info['guest'] is not None
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316")
            st.markdown(f"""
                <div style="padding:15px; border-radius:10px; background:white; border-top:5px solid {color}; box-shadow:0 2px 4px rgba(0,0,0,0.1); min-height:140px;">
                    <b style="font-size:1.1em;">{no}</b> <small>{info['type']}</small><br>
                    <div style="color:gray; font-size:0.85em;">单价: RM {info['price']}</div>
                    <div style="color:{color}; font-weight:bold; margin-top:5px;">
                        {f"👤 {info['guest']}" if is_occ else info['status']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    st.write("")
    # 功能区按钮：确保所有功能入口完整
    st.subheader("🛠️ 管理面板")
    btns = st.columns(5)
    if btns[0].button("📝 入住登记", type="primary"): st.session_state.temp = {}; nav('in')
    if btns[1].button("🔑 批量退房"): nav('out')
    if btns[2].button("⚙️ 房价后台"): nav('price_admin')
    if btns[3].button("🧹 房态维护"): nav('batch')
    if btns[4].button("📊 报表中心"): nav('report')

# 【1. 入住登记：动态随行人逻辑】
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    t = st.session_state.temp
    can_use = {k: f"{k} ({v['type']})" for k, v in st.session_state.rooms_db.items() if not v['guest'] or k in t.get('rs', [])}
    
    # 随行人数确认（放在 Form 外确保即时渲染）
    num_others = st.number_input("随行人数 (不含主登记人)", min_value=0, max_value=10, value=len(t.get('others', [])))

    with st.form("checkin_v65"):
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
                o_n = oc1.text_input(f"姓名", key=f"on_{i}", value=prev['name'])
                o_i = oc2.text_input(f"证件号", key=f"oi_{i}", value=prev['ic'])
                others_list.append({"name": o_n, "ic": o_i})

        st.divider(); st.subheader("🏨 预订详情")
        rs = st.multiselect("分配房间", options=list(can_use.keys()), default=t.get('rs', []), format_func=lambda x: can_use[x])
        ds = st.date_input("日期范围", value=[t.get('checkin', date.today()), t.get('checkout', date.today() + timedelta(1))])

        if st.form_submit_button("去结算确认"):
            if name and ic and rs and len(ds) == 2:
                st.session_state.temp = {"name": name, "ic": ic, "phone": phone, "email": email, "others": others_list, 
                                        "rs": rs, "days": (ds[1]-ds[0]).days, "checkin": ds[0], "checkout": ds[1], "id": datetime.now().strftime("%H%M%S")}
                nav('pay')
            else: st.error("请完整填写必要信息并选择房间。")
    if st.button("⬅️ 返回主页"): nav('home')

# 【2. 结算页：每一项由来清楚的完美表格】
elif st.session_state.page == 'pay':
    st.title("💳 账单确认明细")
    t = st.session_state.temp
    if not t: nav('home')
    
    if st.session_state.paid:
        st.success("✅ 支付并登记成功！"); 
        if st.button("回到房态主页", type="primary"): st.session_state.temp = {}; nav('home')
    else:
        st.write(f"*负责人:* {t['name']} ({t['ic']}) | *联系方式:* {t['phone']}")
        
        # 构建完美账单表格
        bill_data = []
        sub_total = 0
        for r_no in t['rs']:
            price = st.session_state.rooms_db[r_no]['price']
            amt = price * t['days']
            sub_total += amt
            bill_data.append({"收费项": f"房费 - {r_no}", "计算明细": f"RM {price:.2f} × {t['days']} 晚", "金额": f"{amt:.2f}"})
        
        tax = sub_total * 0.06
        bill_data.append({"收费项": "政府服务税 (SST 6%)", "计算明细": f"RM {sub_total:.2f} × 0.06", "金额": f"{tax:.2f}"})
        bill_data.append({"收费项": "离店可退押金", "计算明细": "固定按单收取", "金额": "100.00"})
        
        final_total = sub_total + tax + 100.0
        st.table(pd.DataFrame(bill_data))
        st.markdown(f"<h3 style='text-align:right; color:#ef4444;'>总计应付: RM {final_total:.2f}</h3>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        if c1.button("确认支付并完成入住", type="primary"):
            for r in t['rs']:
                st.session_state.rooms_db[r].update({"guest": t['name'], "guest_ic": t['ic'], "others": t['others'], "status": "Occupied"})
            st.session_state.history.append({**t, "total": final_total, "status": "已支付"})
            st.session_state.paid = True
            st.rerun()
        if c2.button("⬅️ 返回修改信息"): nav('in')

# 【3. 批量退房：支持一人多房一键退】
elif st.session_state.page == 'out':
    st.title("🔑 离店退房管理")
    # 找出所有在住的人
    in_house = {f"{v['guest']} (IC: {v['guest_ic']})": v['guest'] for k, v in st.session_state.rooms_db.items() if v['guest']}
    if in_house:
        target_label = st.selectbox("请选择要办理退房的负责人", list(set(in_house.keys())))
        target_name = in_house[target_label]
        
        rooms_to_free = [k for k, v in st.session_state.rooms_db.items() if v['guest'] == target_name]
        st.warning(f"该操作将一键释放以下房间: {', '.join(rooms_to_free)}")
        
        if st.button("确认退房并释放房间", type="primary"):
            for r in rooms_to_free:
                st.session_state.rooms_db[r].update({"guest": None, "guest_ic": None, "others": [], "status": "Dirty"})
            st.success("退房操作已完成，房间已转为待清扫。")
            if st.button("点击刷新数据"): nav('home')
    else: st.info("当前无住客")
    if st.button("⬅️ 返回主页"): nav('home')

# 【4. 房价后台：实时调整房价】
elif st.session_state.page == 'price_admin':
    st.title("⚙️ 房价后台配置")
    st.info("在此修改的价格将即时应用到所有新订单。")
    with st.form("price_form"):
        p_cols = st.columns(5)
        new_prices = {}
        for idx, (no, info) in enumerate(st.session_state.rooms_db.items()):
            new_prices[no] = p_cols[idx].number_input(f"房号 {no}", value=float(info['price']), step=10.0)
        if st.form_submit_button("确认保存新房价", type="primary"):
            for no, p in new_prices.items():
                st.session_state.rooms_db[no]['price'] = p
            st.success("✅ 房价已更新")
            st.rerun()
    if st.button("⬅️ 返回主页"): nav('home')

# 【5. 房态维护：批量修改 Dirty/Clean】
elif st.session_state.page == 'batch':
    st.title("🧹 房态批量维护")
    st.write("仅可修改空房的状态。")
    targets = st.multiselect("选择需要维护的房号", list(st.session_state.rooms_db.keys()))
    new_status = st.selectbox("将状态修改为", ["Clean", "Dirty", "OOO"])
    if st.button("立即执行", type="primary"):
        count = 0
        for r in targets:
            if not st.session_state.rooms_db[r]['guest']:
                st.session_state.rooms_db[r]['status'] = new_status
                count += 1
        st.success(f"成功更新 {count} 间房的状态。")
        if st.button("查看结果"): nav('home')
    if st.button("⬅️ 返回"): nav('home')

# 【6. 报表中心：财务历史】
elif st.session_state.page == 'report':
    st.title("📊 报表中心")
    if st.session_state.history:
        df_hist = pd.DataFrame(st.session_state.history)
        st.write("### 历史成交明细")
        st.table(df_hist[['id', 'name', 'rs', 'days', 'total', 'status']])
    else:
        st.info("暂无历史交易数据记录")
    if st.button("⬅️ 返回首页"): nav('home')
