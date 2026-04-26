import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- 1. 初始化与高级样式 ---
st.set_page_config(page_title="Executive PMS v4.1", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f1f5f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: 600; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .room-card {
        padding: 20px; border-radius: 15px; background: white;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border-top: 8px solid #ddd; margin-bottom: 15px;
        min-height: 120px; display: flex; flex-direction: column; justify-content: space-between;
    }
    .room-no { font-size: 1.4em; font-weight: 800; color: #1e293b; }
    .room-type { font-size: 0.85em; color: #64748b; margin-top: -5px; }
    .room-status { font-weight: 700; margin-top: 10px; font-size: 1em; }
    </style>
    """, unsafe_allow_html=True)

if 'rooms_db' not in st.session_state:
    # 保持原始房间数据与房型
    st.session_state.rooms_db = {
        "101": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None},
        "102": {"type": "大床房", "price": 200.0, "status": "Clean", "guest": None},
        "103": {"type": "大床房", "price": 200.0, "status": "Dirty", "guest": None},
        "201": {"type": "双床房", "price": 250.0, "status": "Clean", "guest": None},
        "202": {"type": "双床房", "price": 250.0, "status": "OOO", "guest": None},
    }
    st.session_state.update({'page': 'home', 'history': [], 'temp': {}, 'paid': False})

def navigate_to(target):
    st.session_state.page = target
    st.rerun()

# --- 2. 页面渲染逻辑 ---

# 【主页：房态矩阵】
if st.session_state.page == 'home':
    st.session_state.paid = False
    st.title("🏨 智慧酒店云端管理系统")
    
    rooms = st.session_state.rooms_db
    occ = sum(1 for r in rooms.values() if r['guest'])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("今日入住率", f"{(occ/len(rooms))*100:.1f}%")
    c2.metric("当前住客", f"{occ} 人")
    c3.metric("累计营收", f"RM {sum(h.get('total',0) for h in st.session_state.history):.2f}")
    c4.metric("待清扫", f"{sum(1 for r in rooms.values() if r['status']=='Dirty')} 间")

    st.divider()
    room_cols = st.columns(5)
    for idx, (no, info) in enumerate(rooms.items()):
        with room_cols[idx % 5]:
            is_occ = info['guest'] is not None
            color = "#ef4444" if is_occ else ("#22c55e" if info['status']=="Clean" else "#f97316" if info['status']=="Dirty" else "#64748b")
            st.markdown(f"""
                <div class="room-card" style="border-top-color: {color};">
                    <div><div class="room-no">{no}</div><div class="room-type">{info['type']}</div></div>
                    <div class="room-status" style="color: {color};">{f"👤 {info['guest']}" if is_occ else info['status']}</div>
                </div>
            """, unsafe_allow_html=True)

    st.write("")
    nav_btns = st.columns(5)
    if nav_btns[0].button("📝 入住登记", type="primary"): navigate_to('in')
    if nav_btns[1].button("🔑 批量退房"): navigate_to('out')
    if nav_btns[2].button("🧹 批量编辑"): navigate_to('batch') # 重新加入批量编辑
    if nav_btns[3].button("📊 财务报表"): navigate_to('his')

# 【登记入住】
elif st.session_state.page == 'in':
    st.title("旅客登记入住")
    can_use = {k: f"{k} ({v['type']})" for k, v in st.session_state.rooms_db.items() if v['status'] == 'Clean' and not v['guest']}
    with st.form("in_f"):
        c1, c2 = st.columns(2)
        name, ic = c1.text_input("住客姓名"), c2.text_input("证件号码")
        rs = st.multiselect("分配房间", options=list(can_use.keys()), format_func=lambda x: can_use[x])
        ds = st.date_input("入住周期", [date.today(), date.today() + timedelta(1)])
        if st.form_submit_button("核算账单"):
            if name and rs and len(ds) == 2 and (ds[1]-ds[0]).days > 0:
                st.session_state.temp = {"name": name, "ic": ic, "rs": rs, "days": (ds[1]-ds[0]).days, "ds": ds}
                navigate_to('pay')
            else: st.error("请确保资料完整且日期有效")
    if st.button("返回首页"): navigate_to('home')

# 【结算支付：明细累加】
elif st.session_state.page == 'pay':
    st.title("🧾 账单明细确认")
    t = st.session_state.temp
    if st.session_state.paid:
        st.success("✅ 支付成功！入住手续已办妥。")
        if st.button("完成并返回主页", type="primary"): 
            st.session_state.temp = {}
            navigate_to('home')
    else:
        room_list = []
        total_base = 0
        for r in t['rs']:
            info = st.session_state.rooms_db[r]
            sub = info['price'] * t['days']
            room_list.append({"房号": f"{r} ({info['type']})", "单价": f"RM {info['price']}", "小计": f"RM {sub:.2f}"})
            total_base += sub
        sst, ttax = total_base * 0.06, 10.0 * len(t['rs']) * t['days']
        total = total_base + sst + ttax + 100.0
        
        with st.container(border=True):
            st.subheader(f"住客: {t['name']}")
            st.table(pd.DataFrame(room_list))
            st.write(f"政府税 (SST 6%): RM {sst:.2f} | 旅游税: RM {ttax:.2f} | 押金: RM 100.00")
            st.markdown(f"### 应付总计: RM {total:.2f}")

        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 确认支付", type="primary"):
            for r in t['rs']: st.session_state.rooms_db[r].update({"guest": t['name'], "status": "Dirty"})
            st.session_state.history.append({**t, "total": total, "rooms_str": ", ".join(t['rs'])})
            st.session_state.paid = True
            st.rerun()
        if c2.button("❌ 取消"): navigate_to('home')
        if c3.button("⬅️ 修改"): navigate_to('in')

# 【批量编辑房间状态 - 重点回归】
elif st.session_state.page == 'batch':
    st.title("🧹 批量房态维护")
    st.info("提示：系统会自动跳过当前有住客的房间，以保护住客隐私。")
    
    rooms_dict = {k: f"{k} ({v['type']}) - 当前: {v['status']}" for k, v in st.session_state.rooms_db.items()}
    
    with st.container(border=True):
        if st.checkbox("选择全部房间"):
            selected_rs = st.multiselect("已选房间", options=list(rooms_dict.keys()), default=list(rooms_dict.keys()), format_func=lambda x: rooms_dict[x])
        else:
            selected_rs = st.multiselect("手动选择房间", options=list(rooms_dict.keys()), format_func=lambda x: rooms_dict[x])
            
        new_stat = st.select_slider("目标状态", options=["Clean", "Dirty", "OOO"])
        
        if st.button("🚀 立即应用更改", type="primary", use_container_width=True):
            if selected_rs:
                count = 0
                for r in selected_rs:
                    # 只有没有住客的房间才可以批量改状态
                    if not st.session_state.rooms_db[r]['guest']:
                        st.session_state.rooms_db[r]['status'] = new_stat
                        count += 1
                st.success(f"操作完成！已成功更新 {count} 间房的状态。")
                if st.button("点此刷新主页"): navigate_to('home')
            else:
                st.error("请先选择房间")
                
    if st.button("取消并返回首页"): navigate_to('home')

# 【批量退房】
elif st.session_state.page == 'out':
    st.title("🔑 批量退房结算")
    g_map = {}
    for r, info in st.session_state.rooms_db.items():
        if info['guest']: g_map.setdefault(info['guest'], []).append(f"{r} ({info['type']})")
    
    if g_map:
        target = st.selectbox("选择在住客姓名", list(g_map.keys()))
        if st.button("确认结账并释放房间", type="primary"):
            for r_str in g_map[target]:
                r_no = r_str.split(" ")[0]
                st.session_state.rooms_db[r_no].update({"guest": None, "status": "Dirty"})
            st.success("退房成功！房间已转为待清扫。")
            if st.button("完成"): navigate_to('home')
    else:
        st.info("无在住旅客")
        if st.button("返回"): navigate_to('home')

# 【财务报表】
elif st.session_state.page == 'his':
    st.title("📈 营收财务报表")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df[['name', 'rooms_str', 'days', 'total']], use_container_width=True)
    else: st.info("暂无数据")
    if st.button("返回"): navigate_to('home')
