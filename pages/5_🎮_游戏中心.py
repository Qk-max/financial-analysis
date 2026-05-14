"""
游戏中心
"""
import streamlit as st

st.set_page_config(
    page_title="游戏中心 - 金融数据分析系统",
    page_icon="🎮",
    layout="wide",
)

if not st.session_state.get("logged_in"):
    st.switch_page("app.py")
    st.stop()

username = st.session_state.get("username", "")

with st.sidebar:
    st.title("📊 金融数据分析")
    st.markdown(f"👤 **{username}**")
    if st.button("🚪 退出", use_container_width=True):
        for key in ["logged_in", "username", "user_id"]:
            st.session_state[key] = False if key == "logged_in" else (
                "" if key == "username" else None
            )
        st.switch_page("app.py")

st.title("🎮 游戏中心")
st.info("暂无可用游戏，敬请期待。")
