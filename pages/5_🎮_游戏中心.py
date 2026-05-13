"""
游戏中心 - 预留页面
"""
import streamlit as st

st.set_page_config(
    page_title="游戏中心 - 金融数据分析系统",
    page_icon="🎮",
    layout="wide",
)

# 登录守卫
if not st.session_state.get("logged_in"):
    st.switch_page("app.py")
    st.stop()

st.title("🎮 游戏中心")

st.markdown("---")

# 占位内容
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown(
        """
    <div style="text-align: center; padding: 80px 20px;">
        <h2 style="color: #888;">🚧 等待游戏模块接入 🚧</h2>
        <p style="color: #aaa; font-size: 16px; margin-top: 20px;">
            游戏功能正在开发中，敬请期待...
        </p>
        <p style="color: #bbb; font-size: 14px; margin-top: 10px;">
            此页面已预留给后续游戏模块扩展使用
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("---")
st.caption("💡 提示：此页面仅为功能预留，不包含实际游戏功能")
