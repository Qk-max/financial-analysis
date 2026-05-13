"""
首页 - 登录后可见
"""
import streamlit as st

st.set_page_config(
    page_title="首页 - 金融数据分析系统",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 登录守卫 ====================
if not st.session_state.get("logged_in"):
    st.warning("请先登录")
    st.switch_page("app.py")

# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("📊 金融数据分析")

    # 用户信息
    st.markdown(f"👤 **{st.session_state.get('username', '')}**")
    if st.button("🚪 退出", use_container_width=True):
        for key in ["logged_in", "username", "user_id"]:
            st.session_state[key] = False if key == "logged_in" else (
                "" if key == "username" else None
            )
        st.switch_page("app.py")

    st.markdown("---")
    st.markdown("### 📂 功能导航")
    st.markdown(
        """
    - 🏠 **首页** — 系统概览
    - 📈 **股票分析** — K线/均线/RSI
    - 📊 **数据统计** — 收益率/波动率
    - 👤 **用户管理** — 个人信息
    - 🎮 **游戏中心** — 预留
    """
    )
    st.markdown("---")
    st.caption("期末课设项目 | Powered by Streamlit")

# ==================== 主页内容 ====================
st.title("🏠 金融数据分析系统")
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="📈 股票分析", value="实时行情", delta="K线图 / 均线 / RSI")
with col2:
    st.metric(label="📊 数据统计", value="量化分析", delta="收益率 / 波动率")
with col3:
    st.metric(label="👤 用户管理", value="在线", delta=f"{st.session_state.get('username', '')}")

st.markdown("---")
st.subheader("📋 系统简介")
st.markdown(
    """
- **股票分析**：输入 A 股股票代码，获取实时行情数据，绘制 K 线图、均线、RSI 指标
- **数据统计**：提供收益率分析、波动率分析、最大涨跌幅统计等量化指标
- **用户管理**：浏览个人信息、修改密码
- **游戏中心**：娱乐模块（预留）

> 📡 数据来源：**AkShare** 金融数据接口
> 🗄️ 数据存储：**MySQL** + **SQLAlchemy** ORM
> 📈 图表引擎：**Plotly**
"""
)
st.info("👈 请从左侧边栏选择功能模块")
