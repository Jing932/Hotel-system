import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time

# --- 1. 视觉 UI 引擎配置 ---
st.set_page_config(page_title="Harmony PMS v11.0 Gold", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f1f5f9; }
    .stApp { background: linear-gradient(to bottom, #f8fafc, #e2e8f0); }
    [data-testid="stMetric"] {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border-left: 5px solid #3b82f6;
    }
    .room-box {
        padding: 22px;
        border-radius: 18px;
        background: white;
        border: 1px solid #dee2e6;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .room-box:hover { transform: scale(1.02); box-shadow: 0 15px 30px rgba(0,0,0,0.1); }
    .status-tag { font-size: 0.85em; padding: 4px 10px; border-radius: 20px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心状态初始化 (保持 v10.0 全部数据并新增风控字段) ---
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
        'paid': False,
        'is_logged_in': False,
        'checkout_history': [],
        'refund_ledger': {} # 新增：记录订单 ID -> 已退款总额，防止重复退款
    })

# --- 3. 核心工具逻辑 ---
def nav_to(target):
    st.session_state.page = target

def get_room_label(room_no):
    if room_no in st.session_state.rooms_db:
        return f"{room_no} ({st.session_state.rooms_db[room_no]['type']})"
    return room_no

# --- 4. 员工安全网关 (abcd / 12345) ---
if not st.session_state.is_logged_in:
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.markdown("<div style='margin-top:100px;'>", unsafe_allow_html=True)
        st.title("🔐 鸿蒙系统安全认证")
        with st.form("security_portal"):
            user_input = st.text_input("工号")
            pass_input = st.text_input("密码", type="password")
            if st.form_submit_button("进入系统", use_container_width=True):
                if user_input == "abcd" and pass_input == "12345":
                    st.session_state.is_logged_in = True
                    st.rerun()
                else:
                    st.error("认证失败，系统锁定中...")
                    time.sleep(1)
                    st.rerun()
    st.stop()

# --- 5. 业务模块 ---

# 【页面：首页看板】
if st.session_state.page == 'home':
    st.session_state.paid = False 
    st.title("🏨 鸿蒙智慧酒店管理系统")
    
    # 财务数据透视
    gross_in = sum(h['total'] for h in st.session_state.history)
    gross_out = sum(r['amount'] for r in st.session_state.refunds)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("实时出租率", f"{(sum(1 for r in st.session_state.rooms_db.values() if r['guest'])/5)*100:.0f}%")
    m2.metric("净营收 (Net)", f"RM {gross_in - gross_out:.2f}")
    m3.metric("累计退款额", f"RM {gross_out:.2f}", delta=f"{len(st.session_state.refunds)} 笔")
    m4.metric("洁净空房", f"{sum(1 for r in st.session_state.rooms_db.values() if r['status']=='Clean' and not r['guest'])} 间")

    st.divider()
    # 房态格点渲染
    grid = st.columns(5)
    for idx, (room_id, d) in enumerate(st.session_state.rooms_db.items()):
        with grid[idx]:
            occupied = d['guest'] is not None
            theme = "#ef4444" if occupied else ("#22c55e" if d['status']=="Clean" else "#f97316")
            st.markdown(f"""
                <div class='room-box' style='border-top: 5px solid {theme};'>
                    <div style='display: flex; justify-content: space-between;'>
                        <b style='font-size: 1.4em;'>{room_id}</b>
                        <span style='color: {theme}; background: {theme}22;' class='status-tag'>{d['status']}</span>
                    </div>
                    <p style='color: #64748b; margin: 5px 0;'>{d['type']}</p>
                    <hr style='margin: 10px 0; border: 0; border-top: 1px solid #eee;'>
                    <div style='font-weight: 600; min-height: 24px;'>
                        {'👤 '+d['guest'] if occupied else '---'}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.write("")
    ctrl = st.columns(7)
    if ctrl[0].button("📝 登记入住", type="primary"): nav_to('in'); st.rerun()
    if ctrl[1].button("🔑 批量退房"): nav_to('out'); st.rerun()
    if ctrl[2].button("⚙️ 房价管理"): nav_to('price'); st.rerun()
    if ctrl[3].button("🧹 房态维护"): nav_to('batch'); st.rerun()
    if ctrl[4].button("📊 报表中心"): nav_to('report'); st.rerun()
    if ctrl[5].button("💸 退款处理"): nav_to('refund'); st.rerun()
    if ctrl[6].button("🚪 登出系统"): 
        st.session_state.is_logged_in = False
        st.rerun()

# 【页面：登记入住】
elif st.session_state.page == 'in':
    st.title("登记入住 - 旅客信息采集")
    st.subheader("1. 负责人核心档案")
    c1, c2 = st.columns(2)
    p_name = c1.text_input("姓名 *")
    p_ic = c2.text_input("证件号 *")
    p_tel = c1.text_input("联系电话 *")
    p_mail = c2.text_input("邮箱地址 *")
    
    st.write("---")
    st.subheader("2. 随行人员 (多录入引擎)")
    s_num = st.number_input("随行人数", 0, 10, 0)
    s_list = []
    for i in range(int(s_num)):
        sc1, sc2 = st.columns(2)
        sn = sc1.text_input(f"随行人 {i+1} 姓名", key=f"s_n_{i}")
        si = sc2.text_input(f"随行人 {i+1} 证件", key=f"s_i_{i}")
        s_list.append({"name": sn, "ic": si})

    st.write("---")
    st.subheader("3. 房源核实")
    avail_rooms = {k: get_room_label(k) for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    
    with st.form("v11_form"):
        sel_rs = st.multiselect("分配洁净客房 *", options=list(avail_rooms.keys()), format_func=lambda x: avail_rooms[x])
        dates = st.date_input("入住起止 *", value=[date.today(), date.today() + timedelta(1)])
        
        if st.form_submit_button("核算账单"):
            if len(dates) < 2 or dates[0] >= dates[1]:
                st.error("日期区间非法：离店日期须晚于入住日期")
            elif not (p_name and p_ic and p_tel and p_mail and sel_rs):
                st.error("必填字段缺失，请检查 * 号项")
            else:
                uid = f"PMS-{datetime.now().strftime('%m%d%H%M%S')}"
                st.session_state.temp = {
                    "uid": uid, "name": p_name, "ic": p_ic, "phone": p_tel, "email": p_mail,
                    "others": s_list, "rs": {r: st.session_state.rooms_db[r]['price'] for r in sel_rs},
                    "days": (dates[1]-dates[0]).days, "checkin": dates[0], "checkout": dates[1]
                }
                nav_to('pay'); st.rerun()
    if st.button("⬅️ 返回看板"): nav_to('home'); st.rerun()

# 【页面：账单核对】
elif st.session_state.page == 'pay':
    st.title("结算清单核对")
    data = st.session_state.temp
    if st.session_state.paid:
        st.success(f"入住成功！唯一识别码: {data['uid']}"); st.button("完成", on_click=lambda: nav_to('home'))
    else:
        st.info(f"单号: {data['uid']} | 客户: {data['name']}")
        bill_data, sub = [], 0
        for r, p in data['rs'].items():
            cost = p * data['days']
            sub += cost
            bill_data.append({"账项": f"客房服务 - {get_room_label(r)}", "计费": f"RM {p} x {data['days']}晚", "小计": f"RM {cost:.2f}"})
        
        tax_val = sub * 0.06
        total_val = sub + tax_val + 100.0
        st.table(pd.DataFrame(bill_data + [{"账项": "政府SST (6%)", "计费": "-", "小计": f"RM {tax_val:.2f}"}, {"账项": "履约押金 (离店退)", "计费": "-", "小计": "RM 100.00"}]))
        st.markdown(f"<h3 style='text-align:right;'>应缴总额: <span style='color:red;'>RM {total_val:.2f}</span></h3>", unsafe_allow_html=True)

        pc1, pc2, pc3 = st.columns(3)
        if pc1.button("✅ 确认支付入库", type="primary", use_container_width=True):
            for r in data['rs'].keys():
                st.session_state.rooms_db[r].update({
                    "guest": data['name'], "guest_ic": data['ic'], "phone": data['phone'],
                    "email": data['email'], "others": data['others'], "status": "Occupied", "current_uid": data['uid']
                })
            st.session_state.history.append({**data, "total": total_val, "room_list": ", ".join([get_room_label(r) for r in data['rs'].keys()]), "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "Paid"})
            st.session_state.paid = True; st.rerun()
        if pc2.button("放弃本次登记", use_container_width=True): nav_to('home'); st.rerun()
        if pc3.button("修改资料", use_container_width=True): nav_to('in'); st.rerun()

# 【页面：批量退房与记忆系统】
elif st.session_state.page == 'out':
    st.title("离店结算与房态释放")
    # 建立活跃住客映射
    guests_in_house = {}
    for r, v in st.session_state.rooms_db.items():
        if v['guest']:
            tag = f"{v['guest']} ({v['guest_ic']}) - UID: {v.get('current_uid', 'N/A')}"
            guests_in_house[tag] = {"name": v['guest'], "ic": v['guest_ic'], "uid": v.get('current_uid')}

    L, R = st.columns(2)
    with L:
        st.subheader("快捷退房办理")
        if guests_in_house:
            target_tag = st.selectbox("选择在店住客", list(guests_in_house.keys()))
            info = guests_in_house[target_tag]
            if st.button("执行退房并生成待清任务", type="primary"):
                released = []
                for r_no, r_data in st.session_state.rooms_db.items():
                    if r_data['guest'] == info['name'] and r_data['guest_ic'] == info['ic']:
                        released.append(r_no)
                        st.session_state.checkout_history.append({"room": r_no, "snapshot": r_data.copy(), "ts": time.time()})
                        st.session_state.rooms_db[r_no].update({"status": "Dirty", "guest": None, "guest_ic": None, "current_uid": None})
                st.success(f"退房成功：{', '.join(released)} 已释放。")
                time.sleep(0.5); st.rerun()
        else: st.info("目前没有在店住客。")

    with R:
        st.subheader("🔄 退房撤销记忆")
        if st.session_state.checkout_history:
            recent_out = st.session_state.checkout_history[-5:][::-1]
            for idx, item in enumerate(recent_out):
                st.write(f"房: {get_room_label(item['room'])} | 客: {item['snapshot']['guest']}")
                if st.button(f"撤销该房退房", key=f"undo_v11_{idx}"):
                    st.session_state.rooms_db[item['room']] = item['snapshot']
                    st.session_state.checkout_history.remove(item)
                    st.success("状态已回滚"); st.rerun()
        else: st.write("暂无历史操作。")
    if st.button("⬅️ 返回主页"): nav_to('home'); st.rerun()

# 【页面：风控退款系统 - 核心逻辑升级点】
elif st.session_state.page == 'refund':
    st.title("💸 财务安全退款中心")
    if st.session_state.history:
        # 建立订单选择器，显示房型备注
        ref_map = {f"{h['uid']} | {h['name']} | 房: {h['room_list']}": idx for idx, h in enumerate(st.session_state.history)}
        sel_order_key = st.selectbox("选择需退款的历史订单", list(ref_map.keys()))
        target_h = st.session_state.history[ref_map[sel_order_key]]
        order_id = target_h['uid']
        
        # 1. 核心防御：计算该订单已退金额，防止重复退款
        already_refunded = st.session_state.refund_ledger.get(order_id, 0.0)
        remaining_balance = target_h['total'] - already_refunded
        
        st.warning(f"订单总额: RM {target_h['total']} | 已退额: RM {already_refunded:.2f} | 剩余可退: RM {remaining_balance:.2f}")
        
        if remaining_balance <= 0:
            st.error("🚫 该订单已全额退款，禁止重复操作。")
        else:
            r_amt = st.number_input("本次退款金额", 0.0, float(remaining_balance), 0.0)
            r_msg = st.text_area("退款原因说明 (必填)")
            
            if st.button("确认退款申请", type="primary"):
                if r_amt <= 0:
                    st.error("退款金额必须大于 0")
                elif not r_msg:
                    st.error("必须填写退款原因以备审计")
                else:
                    # 更新风控账本
                    st.session_state.refund_ledger[order_id] = already_refunded + r_amt
                    # 记录详细日志（带原因）
                    st.session_state.refunds.append({
                        "uid": order_id, "name": target_h['name'], "amount": r_amt, 
                        "reason": r_msg, "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    # 更新历史订单状态
                    new_status = "Fully Refunded" if (already_refunded + r_amt) >= target_h['total'] else "Partial Refund"
                    st.session_state.history[ref_map[sel_order_key]]['status'] = new_status
                    
                    st.success(f"退款成功！已记录日志并更新财务看板。")
                    time.sleep(1); nav_to('home'); st.rerun()
    else: st.info("系统内尚无已支付订单。")
    if st.button("⬅️ 返回"): nav_to('home'); st.rerun()

# 【页面：报表与实时日志】
elif st.session_state.page == 'report':
    st.title("📊 酒店经营与财务报表")
    t1, t2, t3 = st.tabs(["💰 成交订单明细", "📄 退款实时日志", "🔍 综合查询"])
    
    with t1:
        if st.session_state.history:
            rdf = pd.DataFrame(st.session_state.history)
            rdf['随行人'] = rdf['others'].apply(lambda x: " / ".join([p['name'] for p in x]) if x else "-")
            st.table(rdf[['time', 'uid', 'name', 'room_list', 'total', 'status', '随行人']])
        else: st.write("暂无成交。")
        
    with t2:
        st.subheader("退款历史原因及明细")
        if st.session_state.refunds:
            # 实时更新的退款日志，显示原因
            refund_df = pd.DataFrame(st.session_state.refunds)
            st.table(refund_df[['time', 'uid', 'name', 'amount', 'reason']])
        else: st.write("暂无退款记录。")
        
    with t3:
        search_kw = st.text_input("搜寻旅客姓名 (主客/随行人)")
        if search_kw:
            hits = []
            for h in st.session_state.history:
                names = [h['name'].lower()] + [o['name'].lower() for o in h['others']]
                if any(search_kw.lower() in n for n in names):
                    hits.append({"UID": h['uid'], "主客": h['name'], "入店": h['checkin'], "状态": h['status']})
            if hits: st.table(pd.DataFrame(hits))
            else: st.warning("未匹配到相关结果")
    if st.button("⬅️ 返回主页"): nav_to('home'); st.rerun()

# 【页面：房价配置】
elif st.session_state.page == 'price':
    st.title("⚙️ 房型定价管理")
    p_grid = st.columns(5)
    p_updates = {}
    for i, (no, d) in enumerate(st.session_state.rooms_db.items()):
        p_updates[no] = p_grid[i].number_input(f"{get_room_label(no)}", value=float(d['price']), key=f"price_v11_{no}")
    if st.button("应用并保存全局房价", type="primary"):
        for no, p in p_updates.items(): st.session_state.rooms_db[no]['price'] = p
        st.success("调价生效。"); nav_to('home'); st.rerun()
    if st.button("⬅️ 返回"): nav_to('home'); st.rerun()

# 【页面：房态控制】
elif st.session_state.page == 'batch':
    st.title("🧹 房态批量调度")
    all_rooms_list = {k: get_room_label(k) for k in st.session_state.rooms_db.keys()}
    target_rs = st.multiselect("目标房间", options=list(all_rooms_list.keys()), format_func=lambda x: all_rooms_list[x])
    target_st = st.selectbox("设定状态为", ["Clean", "Dirty", "OOO (维修)"])
    if st.button("执行状态同步"):
        for r in target_rs:
            if not st.session_state.rooms_db[r]['guest']:
                st.session_state.rooms_db[r]['status'] = "OOO" if "维修" in target_st else target_st
        st.success("同步完成。"); nav_to('home'); st.rerun()
    if st.button("⬅️ 返回"): nav_to('home'); st.rerun()
