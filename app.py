import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- 1. 核心初始化 (含防重击锁) ---
if 'rooms_db' not in st.session_state:
    st.session_state.rooms_db = {f"{i}{j:02d}": {"price": 200.0, "status": "Clean", "guest": None} for i in range(1, 4) for j in range(1, 5)}
    st.session_state.update({'page': 'home', 'history': [], 'temp': {}, 'paid': False, 'btn_lock': False})

def nav(target):
    st.session_state.update({'page': target, 'btn_lock': False}) # 切换页面时解锁
    st.rerun()

# --- 2. 页面渲染 ---

# 【主页矩阵】
if st.session_state.page == 'home':
    st.session_state.paid = False
    st.title("🏨 智慧酒店 PMS (安全增强版)")
    rooms = st.session_state.rooms_db
    cols = st.columns(6)
    for idx, (no, info) in enumerate(rooms.items()):
        is_occ = info['guest'] is not None
        # 颜色逻辑：占用(红)，脏房(橙)，空房(绿)
        bg = "#fee2e2" if is_occ else ("#ffedd5" if info['status']=="Dirty" else "#dcfce7")
        cols[idx%6].markdown(f"""<div style="background:{bg};padding:10px;border-radius:8px;border-left:5px solid {'#ef4444' if is_occ else '#22c55e'};">
            <b>{no}</b><br><small>{info['guest'] if is_occ else info['status']}</small></div>""", unsafe_allow_html=True)
    
    st.write("")
    nav_cols = st.columns(5)
    if nav_cols[0].button("📝 登记入住", use_container_width=True, type="primary"): nav('in')
    if nav_cols[1].button("🔑 批量退房", use_container_width=True): nav('out')
    if nav_cols[2].button("🧹 快速清洁", use_container_width=True): nav('clean')
    if nav_cols[3].button("📒 营收报表", use_container_width=True): nav('his')

# 【登记入住 - 加入日期校验】
elif st.session_state.page == 'in':
    st.title("新旅客登记")
    # 逻辑修正：只准选 Clean 的房
    can_use = [k for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']]
    with st.form("in_f"):
        c1, c2 = st.columns(2)
        name, ic = c1.text_input("姓名"), c2.text_input("证件号")
        rs = st.multiselect("选择房号 (仅限已清洁房间)", can_use)
        ds = st.date_input("入住周期", [date.today(), date.today() + timedelta(1)])
        if st.form_submit_button("核算账单"):
            if name and rs and len(ds) == 2 and (ds[1]-ds[0]).days > 0:
                st.session_state.temp = {"name":name, "ic":ic, "rs":rs, "days":(ds[1]-ds[0]).days, "ds":ds}
                nav('pay')
            else: st.error("请完整填写，且入住必须大于 0 晚")
    if st.button("返回"): nav('home')

# 【结算支付 - 加入防重复锁】
elif st.session_state.page == 'pay':
    t = st.session_state.temp
    st.title("💳 账单确认")
    
    if st.session_state.paid:
        st.success("✅ 入住办理完成！")
        if st.button("完成并回到主页"): st.session_state.temp = {}; nav('home')
    else:
        # 修正：计算逻辑透明化
        room_sub = sum(st.session_state.rooms_db[r]['price'] for r in t['rs']) * t['days']
        tax, t_tax = room_sub * 0.06, 10.0 * len(t['rs']) * t['days']
        total = room_sub + tax + t_tax + 100.0 # 100 为押金
        
        st.table(pd.DataFrame({
            "明细": ["房费总计", "SST 税额", "旅游税", "预收押金"],
            "计算": [f"RM {room_sub:.2f}", "6%", "RM 10/房/晚", "RM 100.00"],
            "小计": [f"RM {room_sub:.2f}", f"RM {tax:.2f}", f"RM {t_tax:.2f}", "RM 100.00"]
        }))
        st.subheader(f"应付总计：RM {total:.2f}")

        if st.button("确认支付并办理入住", type="primary", disabled=st.session_state.btn_lock):
            st.session_state.btn_lock = True # 锁定按钮防止重复点击
            # 原子更新
            for r in t['rs']: 
                st.session_state.rooms_db[r].update({"guest": t['name'], "status": "Dirty"})
            st.session_state.history.append({**t, "total": total, "rooms_str": ", ".join(t['rs'])})
            st.session_state.paid = True
            st.rerun()
    if not st.session_state.paid and st.button("取消"): nav('home')

# 【批量退房 - 逻辑增强】
elif st.session_state.page == 'out':
    st.title("办理退房")
    g_map = {}
    for r, info in st.session_state.rooms_db.items():
        if info['guest']: g_map.setdefault(info['guest'], []).append(r)
    
    if g_map:
        target = st.selectbox("选择住客姓名", list(g_map.keys()))
        if st.button("确认结账并释放房间", type="primary"):
            for r in g_map[target]:
                st.session_state.rooms_db[r].update({"guest": None, "status": "Dirty"})
            st.success("退房成功，房间已转入待清扫状态")
            st.button("完成", on_click=lambda: nav('home'))
    else: st.info("目前无住客"); st.button("返回", on_click=lambda: nav('home'))

# 【新增：快速清洁模块】
elif st.session_state.page == 'clean':
    st.title("🧹 快速清洁管理")
    dirty_rooms = [k for k, v in st.session_state.rooms_db.items() if v['status'] == 'Dirty' and not v['guest']]
    if dirty_rooms:
        to_clean = st.multiselect("选择已打扫完成的房间", dirty_rooms)
        if st.button("更新为 Clean 状态"):
            for r in to_clean: st.session_state.rooms_db[r]['status'] = 'Clean'
            st.success("更新成功"); nav('home')
    else: st.success("所有房间都很干净！")
    st.button("返回", on_click=lambda: nav('home'))

# 【报表】
elif st.session_state.page == 'his':
    st.title("营收历史报表")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df[['name', 'rooms_str', 'days', 'total']])
    st.button("返回", on_click=lambda: nav('home'))
