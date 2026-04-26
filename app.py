import streamlit as st
import pandas as pd

# 初始化 Session State
if 'page' not in st.session_state:
    st.session_state.page = 'input_info'
if 'customer_data' not in st.session_state:
    st.session_state.customer_data = []
if 'rooms' not in st.session_state:
    # 模拟房间初始库存
    st.session_state.rooms = {"大床房": 5, "双床房": 3}
if 'temp_user' not in st.session_state:
    st.session_state.temp_user = {}

# 房价定义
ROOM_PRICES = {"大床房": 200, "双床房": 250}

def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()

# --- 页面 1: 输入客人资料 ---
if st.session_state.page == 'input_info':
    st.title("🏨 酒店入住系统 - 登记")
    name = st.text_input("客人姓名")
    ic = st.text_input("身份证号 (IC)")
    
    if st.button("下一步"):
        if name and ic:
            st.session_state.temp_user = {"姓名": name, "IC": ic}
            # 流程图：判断是否有空房
            if sum(st.session_state.rooms.values()) > 0:
                go_to('assign_room')
            else:
                go_to('no_room')
        else:
            st.error("请完整输入信息")

# --- 页面 2: 分配房间 (判断空房) ---
elif st.session_state.page == 'assign_room':
    st.title("🛏️ 分配房间")
    st.write("### 剩余房型库存：")
    cols = st.columns(2)
    cols[0].metric("大床房", st.session_state.rooms["大床房"])
    cols[1].metric("双床房", st.session_state.rooms["双床房"])

    room_type = st.radio("选择房型", ["大床房", "双床房"])
    # 流程图：输入入住天数
    days = st.number_input("输入入住天数", min_value=1, step=1, value=1)

    col_btn = st.columns(2)
    if col_btn[0].button("返回上一步"):
        go_to('input_info')
    
    if col_btn[1].button("办理入住"):
        if st.session_state.rooms[room_type] > 0:
            st.session_state.temp_user["房型"] = room_type
            st.session_state.temp_user["天数"] = days
            st.session_state.temp_user["费用"] = ROOM_PRICES[room_type] * days
            go_to('show_payment')
        else:
            st.error(f"抱歉，{room_type} 已满")

# --- 页面 3: 显示费用与付款 ---
elif st.session_state.page == 'show_payment':
    st.title("💳 费用确认与支付")
    user = st.session_state.temp_user
    st.write(f"*客人姓名:* {user['姓名']}")
    st.write(f"*选择房型:* {user['房型']}")
    st.write(f"*入住天数:* {user['天数']} 天")
    st.subheader(f"总计费用: RM {user['费用']}")

    col_pay = st.columns(3)
    if col_pay[0].button("返回修改"):
        go_to('assign_room')
    
    if col_pay[1].button("✅ 支付成功"):
        # 扣除库存
        st.session_state.rooms[user['房型']] -= 1
        # 记录财务资料
        st.session_state.customer_data.append(user)
        go_to('complete')
        
    if col_pay[2].button("❌ 支付失败"):
        st.toast("支付失败，正在返回首页...", icon="⚠️")
        # 流程图逻辑：支付不成功跳回第一面
        go_to('input_info')

# --- 页面 4: 无空房 ---
elif st.session_state.page == 'no_room':
    st.error("🚨 抱歉，目前酒店所有房型已满。")
    if st.button("返回首页"):
        go_to('input_info')

# --- 页面 5: 入住完成 (财务报表) ---
elif st.session_state.page == 'complete':
    st.balloons()
    st.success("✅ 入住办理完成！")
    
    st.subheader("📊 顾客入住记录 (按顺序排序)")
    if st.session_state.customer_data:
        df = pd.DataFrame(st.session_state.customer_data)
        df.index = df.index + 1  # 显示入住顺序
        df.index.name = "入住顺序"
        st.table(df)
        
        total_revenue = df["费用"].sum()
        st.markdown(f"### 💰 系统总收入: *RM {total_revenue}*")
    
    if st.button("继续办理下一位"):
        go_to('input_info')
