import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. 全局配置与状态初始化 ---
st.set_page_config(page_title="HOTEL SYSTEM", layout="wide")

# 初始化数据库与全局变量
if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO",   "guest": None, "guest_ic": None, "phone": "", "email": "", "others": []},
    }
    st.session_state.update({
        'page': 'home', 
        'history': [], 
        'refunds': [], 
        'temp': {}, 
        'paid': False
    })

# 统一导航函数
def nav(target):
    st.session_state.page = target
    st.rerun()

# --- 2. 页面逻辑控制 ---

# 【主页：房态中心】
if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    # 净营收 = 入账总和 - 退款总和
    total_in = sum(h['total'] for h in st.session_state.history)
    total_out = sum(r['amount'] for r in st.session_state.refunds)
    net_revenue = total_in - total_out
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("入住率", f"{(sum(1 for r in st.session_state.rooms_db.values() if r['guest'])/5)*100:.0f}%")
    c2.metric("净营收", f"RM {net_revenue:.2f}")
    c3.metric("总退款额", f"RM {total_out:.2f}")
    c4.metric("可用洁净房", f"{sum(1 for r in st.session_state.rooms_db.values() if r['status']=='Clean' and not r['guest'])} 间")

    st.divider()
    # 房态格子渲染
    cols = st.columns(5)
    for idx, (no, info) in enumerate(st.session_state.rooms_db.items()):
        with cols[idx]:
            is_occ = info['guest'] is not None
            # 颜色逻辑：红(占用), 绿(洁净), 橙(脏房), 蓝灰(维修)
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316" if info['status']=="Dirty" else "#64748b")
            st.markdown(f"""
                <div style="padding:15px; border-radius:10px; background:white; border-top:5px solid {color}; box-shadow:0 2px 4px rgba(0,0,0,0.1); min-height:150px;">
                    <b style="font-size:1.1em;">{no}</b> <small>{info['type']}</small><br>
                    <div style="color:gray; font-size:0.85em;">当前房价: RM {info['price']}</div>
                    <div style="color:{color}; font-weight:bold; margin-top:8px;">
                        {f"👤 {info['guest']}" if is_occ else f"✨ {info['status']}"}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    st.write("")
    st.subheader("🛠️ 控制台")
    menu = st.columns(6)
    if menu[0].button("📝 登记入住", type="primary", use_container_width=True): st.session_state.temp = {}; nav('in')
    if menu[1].button("🔑 办理退房", use_container_width=True): nav('out')
    if menu[2].button("⚙️ 房价管理", use_container_width=True): nav('price_admin')
    if menu[3].button("🧹 房态清洁", use_container_width=True): nav('batch')
    if menu[4].button("📊 财务报表", use_container_width=True): nav('report')
    if menu[5].button("💸 退款入口", use_container_width=True): nav('refund_page')

# 【功能 1：入住登记 - 强约束逻辑】
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    # 核心修复：只选 Clean 且空的房，杜绝污染房/维修房卖出
    can_use = {k: f"{k} ({v['type']}) - RM{v['price']}" for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    
    if not can_use:
        st.error("⚠️ 暂无可用洁净空房，请先完成房间清洁或维修。")
        if st.button("⬅️ 返回"): nav('home')
    else:
        with st.form("checkin_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("主登记人姓名")
            ic = c2.text_input("证件号 (IC/Passport)")
            phone = c1.text_input("联系电话")
            email = c2.text_input("电子邮箱")
            
            num_others = st.number_input("随行人数", 0, 10, 0)
            others_list = []
            if num_others > 0:
                for i in range(int(num_others)):
                    oc1, oc2 = st.columns(2)
                    others_list.append({"name": oc1.text_input(f"随行人 {i+1} 姓名", key=f"on_{i}"), "ic": oc2.text_input(f"随行人 {i+1} 证件号", key=f"oi_{i}")})
            
            st.divider()
            rs = st.multiselect("分配房间", options=list(can_use.keys()))
            ds = st.date_input("入住起止日期", value=[date.today(), date.today() + timedelta(1)])
            
            if st.form_submit_button("生成账单并预览"):
                if name and ic and rs and len(ds) == 2:
                    # 价格快照：锁定当前房价
                    snap = {r: st.session_state.rooms_db[r]['price'] for r in rs}
                    st.session_state.temp = {"name": name, "ic": ic, "phone": phone, "email": email, "others": others_list, 
                                            "rs": snap, "days": (ds[1]-ds[0]).days, "checkin": ds[0], "checkout": ds[1], "id": datetime.now().strftime("%y%m%d%H%M")}
                    nav('pay')
                else: st.error("请完整填写信息并至少选择一间房。")
        if st.button("⬅️ 返回主页"): nav('home')

# 【功能 2：账单结算 - 含支付失败处理】
elif st.session_state.page == 'pay':
    st.title("💳 账单确认预览")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("✅ 支付成功，入住手续已完成！")
        if st.button("回到首页"): st.session_state.temp = {}; nav('home')
    else:
        # 构建账单表格
        bill, sub = [], 0
        for r_no, price in t['rs'].items():
            amt = price * t['days']; sub += amt
            bill.append({"收费项目": f"客房 - {r_no}", "价格明细": f"RM {price} × {t['days']} 晚", "金额": f"{amt:.2f}"})
        tax = sub * 0.06
        bill.append({"收费项目": "SST 服务税 (6%)", "价格明细": f"RM {sub:.2f} × 0.06", "金额": f"{tax:.2f}"})
        bill.append({"收费项目": "离店可退押金", "价格明细": "固定按单收取", "金额": "100.00"})
        total_f = sub + tax + 100.0
        
        st.table(pd.DataFrame(bill))
        st.markdown(f"<h2 style='text-align:right; color:#ef4444;'>总计应付: RM {total_f:.2f}</h2>", unsafe_allow_html=True)
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 确认支付成功", type="primary", use_container_width=True):
            # 写入数据库
            for r in t['rs'].keys():
                st.session_state.rooms_db[r].update({"guest": t['name'], "guest_ic": t['ic'], "others": t['others'], "status": "Occupied"})
            st.session_state.history.append({**t, "total": total_f, "room_list": ", ".join(t['rs'].keys()), "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            st.session_state.paid = True
            st.rerun()
        
        if c2.button("❌ 支付失败 (取消)", use_container_width=True):
            st.warning("支付异常，正在返回...")
            st.session_state.temp = {}
            nav('home')
            
        if c3.button("⬅️ 返回修改信息", use_container_width=True): nav('in')

# 【功能 3：房价后台 - 彻底修复无法保存 Bug】
elif st.session_state.page == 'price_admin':
    st.title("⚙️ 房价策略管理")
    st.info("此处修改的价格仅对【新订单】生效，不会改变已成交订单的金额。")
    
    # 修复方案：不使用 form，利用 key 实时绑定 session_state
    st.write("### 实时价格调整区")
    cols = st.columns(5)
    current_inputs = {}
    for i, (no, info) in enumerate(st.session_state.rooms_db.items()):
        current_inputs[no] = cols[i].number_input(f"房号 {no}", value=float(info['price']), key=f"p_input_{no}")
    
    st.divider()
    if st.button("🔥 确认修改并保存到系统", type="primary"):
        # 强制更新数据库
        for no, new_price in current_inputs.items():
            st.session_state.rooms_db[no]['price'] = new_price
        st.success("✅ 全新价格配置已成功写入数据库并实时生效！")
        if st.button("点击刷新"): nav('home')
    
    if st.button("⬅️ 返回首页"): nav('home')

# 【功能 4：退款处理 - 含原因及报表集成】
elif st.session_state.page == 'refund_page':
    st.title("💸 退款申请管理")
    if st.session_state.history:
        # 获取未全额退款的订单
        options = {f"{h['id']} - {h['name']} (RM {h['total']})": i for i, h in enumerate(st.session_state.history)}
        target = st.selectbox("请选择要退款的订单:", list(options.keys()))
        order = st.session_state.history[options[target]]
        
        amt = st.number_input("退款金额 (RM)", 0.0, float(order['total']), 0.0)
        reason = st.text_area("退款原因 (将显示在报表中)", placeholder="例如：空调故障、提前退房...")
        
        if st.button("执行退款", type="primary"):
            if amt > 0:
                st.session_state.refunds.append({
                    "id": order['id'], "name": order['name'], "amount": amt, 
                    "reason": reason if reason else "未注明原因", 
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.success(f"已成功退款 RM {amt}。")
                if st.button("完成"): nav('home')
            else: st.error("请输入有效的退款金额。")
    else: st.info("暂无成交订单，无法办理退款。")
    if st.button("⬅️ 返回"): nav('home')

# 【功能 5：财务报表 - 数据全面展示】
elif st.session_state.page == 'report':
    st.title("📊 酒店财务与交易报表")
    tab1, tab2 = st.tabs(["📥 收入明细", "📤 退款明细"])
    
    with tab1:
        if st.session_state.history:
            df_in = pd.DataFrame(st.session_state.history)
            st.table(df_in[['time', 'id', 'name', 'room_list', 'total']])
        else: st.write("暂无收入记录")
        
    with tab2:
        if st.session_state.refunds:
            df_out = pd.DataFrame(st.session_state.refunds)
            # 报表中心增加退款原因展示
            st.table(df_out[['time', 'id', 'name', 'amount', 'reason']])
        else: st.write("暂无退款记录")
    
    if st.button("⬅️ 返回主页"): nav('home')

# 【功能 6：批量退房 & 房态清洁】
elif st.session_state.page == 'out':
    st.title("🔑 离店批量退房")
    current_guests = list(set([v['guest'] for v in st.session_state.rooms_db.values() if v['guest']]))
    if current_guests:
        target = st.selectbox("选择办理人", current_guests)
        if st.button("确认退房 (释放所有关联房间)", type="primary"):
            for r, info in st.session_state.rooms_db.items():
                if info['guest'] == target:
                    st.session_state.rooms_db[r].update({"guest": None, "guest_ic": None, "status": "Dirty"})
            st.success("退房成功，房间已转为待清洁状态。")
            if st.button("刷新"): nav('home')
    else: st.info("当前无住客。")
    if st.button("⬅️ 返回"): nav('home')

elif st.session_state.page == 'batch':
    st.title("🧹 房态清洁与维护")
    target_rooms = st.multiselect("选择需要操作的房号", list(st.session_state.rooms_db.keys()))
    status_choice = st.selectbox("修改状态为", ["Clean", "Dirty", "OOO (维修)"])
    if st.button("执行更新", type="primary"):
        for r in target_rooms:
            if not st.session_state.rooms_db[r]['guest']:
                st.session_state.rooms_db[r]['status'] = "OOO" if "维修" in status_choice else status_choice
        st.success("状态更新完毕。")
        if st.button("查看结果"): nav('home')
    if st.button("⬅️ 返回"): nav('home')
