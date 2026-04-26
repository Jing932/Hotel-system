import streamlit as st
import pandas as pd

# ========================
# 初始化系统数据
# ========================
if "rooms" not in st.session_state:
    st.session_state.rooms = 5  # 总房间

if "records" not in st.session_state:
    st.session_state.records = []  # 入住记录

if "step" not in st.session_state:
    st.session_state.step = "start"

if "cost" not in st.session_state:
    st.session_state.cost = 0


PRICE_PER_DAY = 100

st.title("酒店管理系统")

# ========================
# 步骤1：输入客人资料
# ========================
if st.session_state.step == "start":
    st.header("输入客人资料")

    name = st.text_input("客人姓名")

    if st.button("提交资料"):
        if not name:
            st.warning("请输入姓名")
        else:
            st.session_state.name = name
            st.session_state.step = "check_room"
            st.rerun()

# ========================
# 步骤2：判断是否有空房
# ========================
elif st.session_state.step == "check_room":
    st.header("判断是否有空房")

    if st.session_state.rooms <= 0:
        st.error("❌ 无空房")
        st.session_state.step = "end"
    else:
        st.success("✅ 有空房")
        st.session_state.step = "assign_room"

    st.rerun()

# ========================
# 步骤3：分配房间
# ========================
elif st.session_state.step == "assign_room":
    st.header("分配房间")

    st.session_state.rooms -= 1
    st.success(f"已为 {st.session_state.name} 分配房间")

    st.session_state.step = "checkin"
    st.rerun()

# ========================
# 步骤4：办理入住
# ========================
elif st.session_state.step == "checkin":
    st.header("办理入住")

    days = st.number_input("请输入入住天数", min_value=1)

    if st.button("确认入住"):
        st.session_state.days = days
        st.session_state.step = "calculate"
        st.rerun()

# ========================
# 步骤5：计算费用
# ========================
elif st.session_state.step == "calculate":
    st.header("计算费用")

    cost = st.session_state.days * PRICE_PER_DAY
    st.session_state.cost = cost

    st.info(f"费用为：{cost} 元")

    st.session_state.step = "payment"
    st.rerun()

# ========================
# 步骤6：付款
# ========================
elif st.session_state.step == "payment":
    st.header("付款")

    st.write(f"应支付：{st.session_state.cost} 元")

    pay = st.radio("支付是否成功？", ["是", "否"])

    if st.button("确认支付"):
        if pay == "是":
            st.success("支付成功")
            st.session_state.step = "record"
        else:
            st.warning("支付失败，请重新付款")

        st.rerun()

# ========================
# 步骤7：记录财务
# ========================
elif st.session_state.step == "record":
    st.header("记录财务资料")

    st.session_state.records.append({
        "姓名": st.session_state.name,
        "天数": st.session_state.days,
        "费用": st.session_state.cost
    })

    st.success("财务记录已保存")

    st.session_state.step = "complete"
    st.rerun()

# ========================
# 步骤8：入住完成
# ========================
elif st.session_state.step == "complete":
    st.header("入住完成")

    st.success("🎉 入住完成！")

    st.dataframe(pd.DataFrame(st.session_state.records))

    if st.button("新客人"):
        st.session_state.step = "start"
        st.rerun()

# ========================
# 结束
# ========================
elif st.session_state.step == "end":
    st.header("结束")
    st.write("流程结束")
