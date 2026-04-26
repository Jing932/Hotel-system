import streamlit as st
import pandas as pd

# --- 1. 配置页面 ---
st.set_page_config(page_title="酒店入住管理系统", layout="centered")

# --- 2. 初始化 Session State (核心修复点) ---
def init_connection():
    if 'page' not in st.session_state:
        st.session_state.page = 'input_info'
    if 'customer_data' not in st.session_state:
        st.session_state.customer_data = []
    if 'rooms' not in st.session_state:
        # 初始库存
        st.session_state.rooms = {"大床房": 5, "双床房": 3}
    if 'temp_user' not in st.session_state:
        st.session_state.temp_user = {}
    if 'error_msg' not in st.session_state:
        st.session_state.error_msg = ""

init_connection()

# 房价配置
ROOM_PRICES = {"大床房": 200, "双床房": 250}

# 跳转函数
def navigate_to(page_name):
    st.session_state.page = page_name
    st.rerun()

# --- 3. 页面逻辑控制 ---

# 【页面 1: 输入客人资料】
if st.session_state.page == 'input_info':
    st.title("🏨 酒店入住系统 - 登记")
    
    if st.session_state.error_msg:
        st.error(st.session_state.error_msg)
        st.session_state.error_msg = "" # 显示一次后清空

    # 使用 key 确保组件独立性
    name = st.text_input("客人姓名", key="name_input")
    ic = st.text_input("身份证号 (IC)", key="ic_input")
    
    if st.button("下一步", use_container_width=True):
        if name.strip() and ic.strip():
            st.session_state.temp_user = {"姓名": name, "IC": ic}
            
            # 流程图逻辑：判断是否有空房
            if sum(st.session_state.rooms.values()) > 0:
                navigate_to('assign_room')
            else:
                navigate_to('no_room')
        else:
            st.warning("⚠️ 请输入完整的姓名和 IC。")

# 【页面 2: 分配房间与入住天数】
elif st.session_state.page == 'assign_room':
    st.title("🛏️ 分配房间与天数")
    
    st.subheader("当前剩余房型")
    col_a, col_b = st.columns(2)
    col_a.metric("大床房", f"{st.session_state.rooms['大床房']} 间")
    col_b.metric("双床房", f"{st.session_state.rooms['双床房']} 间")
    
    st.divider()
    
    # 房型选择与天数输入在同一面
    room_type = st.radio("选择房型", ["大床房", "双床房"], horizontal=True)
    days = st.number_input("入住天数", min_value=1, step=1, value=1)
    
    cols = st.columns(2)
    if cols[0].button("⬅️ 返回上一步", use_container_width=True):
        navigate_to('input_info')
    
    if cols[1].button("确认办理", use_container_width=True):
        if st.session_state.rooms[room_type] > 0:
            st.session_state.temp_user["房型"] = room_type
            st.session_state.temp_user["天数"] = days
            # 计算费用 = 房价 * 天数
            st.session_state.temp_user["费用"] = ROOM_PRICES[room_type] * days
            navigate_to('show_payment')
        else:
            st.error(f"❌ {room_type} 已没有空房，请选择其他房型。")

# 【页面 3: 费用显示与支付判断】
elif st.session_state.page == 'show_payment':
    st.title("💳 确认支付")
    user = st.session_state.temp_user
    
    st.write(f"### 客人：{user['姓名']}")
    st.info(f"房型：{user['房型']} | 天数：{user['天数']} 天")
    st.success(f"## 应付金额：RM {user['费用']}")
    
    st.write("---")
    st.write("确认支付是否成功？")
    
    c1, c2, c3 = st.columns(3)
    
    if c1.button("⬅️ 返回修改", use_container_width=True):
        navigate_to('assign_room')
    
    if c2.button("✅ 支付成功", type="primary", use_container_width=True):
        # 1. 扣除对应房间库存
        st.session_state.rooms[user['房型']] -= 1
        # 2. 记录财务资料
        st.session_state.customer_data.append(user)
        # 3. 进入完成页面
        navigate_to('complete')
        
    if c3.button("❌ 支付失败", use_container_width=True):
        # 流程图：支付失败自动跳转回第一面
        st.session_state.error_msg = "前一单支付失败，请重新登记。"
        st.session_state.temp_user = {} # 清空临时数据
        navigate_to('input_info')

# 【页面 4: 无空房提示】
elif st.session_state.page == 'no_room':
    st.error("🚨 酒店目前已满房，无法办理入住。")
    if st.button("返回首页"):
        navigate_to('input_info')

# 【页面 5: 入住完成及报表】
elif st.session_state.page == 'complete':
    st.balloons()
    st.title("🎊 办理完成")
    
    st.subheader("📋 今日入住记录清单")
    if st.session_state.customer_data:
        df = pd.DataFrame(st.session_state.customer_data)
        # 整理表格列顺序
        df = df[["姓名", "IC", "房型", "天数", "费用"]]
        # 设置入住顺序索引
        df.index = [f"顺序 {i+1}" for i in range(len(df))]
        
        st.table(df)
        
        # 计算总收入
        total_all = df["费用"].sum()
        st.markdown(f"### 💵 今日总营业额：*RM {total_all}*")
    
    if st.button("办理下一位客人", type="primary"):
        st.session_state.temp_user = {}
        navigate_to('input_info')
