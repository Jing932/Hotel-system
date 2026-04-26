import streamlit as st

PRICE_PER_DAY = 100

st.title("🏨 酒店入住系统")

if "rooms" not in st.session_state:
    st.session_state.rooms = 3

st.write(f"当前剩余房间：{st.session_state.rooms}")

name = st.text_input("客人姓名")
days = st.number_input("入住天数", min_value=1, step=1)

if st.button("开始办理"):

    if not name:
        st.warning("请输入姓名")

    elif st.session_state.rooms <= 0:
        st.error("❌ 无空房")

    else:
        st.session_state.rooms -= 1

        st.success(f"✅ 已为 {name} 分配房间")

        cost = days * PRICE_PER_DAY
        st.info(f"💰 费用：{cost} 元")

        pay = st.radio("是否支付成功？", ["是", "否"])

        if pay == "是":
            st.success("🎉 入住完成")
        else:
            st.warning("❌ 支付失败")
