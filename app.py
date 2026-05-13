"""
app.py - 金融数据分析系统入口（首页）

运行方式:
    pip install -r requirements.txt
    streamlit run app.py
"""
import streamlit as st

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="金融数据分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 侧边栏导航 ====================

with st.sidebar:
    st.title("📊 金融数据分析")

    st.markdown("---")
    st.markdown("### 📂 功能导航")
    st.markdown(
        """
    - 🏠 **首页** — 系统概览
    - 📈 **股票分析** — K线/均线/RSI
    - 📊 **数据统计** — 收益率/波动率
    - 👤 **用户模块** — 登录/注册
    - 🎮 **游戏中心** — 预留
    """
    )

    st.markdown("---")
    st.markdown("### 🔧 快速设置")
    st.markdown("请在 `config.py` 中配置 MySQL 连接信息")

    st.markdown("---")
    st.caption("期末课设项目 | Powered by Streamlit")

# ==================== 首页主体内容 ====================

st.title("🏠 金融数据分析系统")

st.markdown("---")

# 三列指标卡片
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="📈 股票分析",
        value="实时行情",
        delta="K线图 / 均线 / RSI",
    )

with col2:
    st.metric(
        label="📊 数据统计",
        value="量化分析",
        delta="收益率 / 波动率",
    )

with col3:
    st.metric(
        label="👤 用户管理",
        value="注册登录",
        delta="MySQL 持久化",
    )

st.markdown("---")

# 系统简介
st.subheader("📋 系统简介")
st.markdown(
    """
本系统是一个基于 **Python + Streamlit** 的金融数据分析平台，主要功能包括：

- **股票分析**：输入 A 股股票代码，获取实时行情数据，绘制 K 线图、均线、RSI 指标
- **数据统计**：提供收益率分析、波动率分析、最大涨跌幅统计等量化指标
- **用户模块**：支持用户注册与登录，数据持久化存储到 MySQL 数据库
- **游戏中心**：娱乐模块（预留）

> 📡 数据来源：**AkShare** 金融数据接口
> 🗄️ 数据存储：**MySQL** + **SQLAlchemy** ORM
> 📈 图表引擎：**Plotly**
"""
)

st.markdown("---")

# 技术架构
st.subheader("🛠️ 技术栈")

tech_col1, tech_col2, tech_col3 = st.columns(3)

with tech_col1:
    st.markdown(
        """
    **核心框架**
    - Python 3.10+
    - Streamlit (Web UI)
    - Pandas (数据处理)
    - Plotly (可视化)
    """
    )

with tech_col2:
    st.markdown(
        """
    **数据与存储**
    - AkShare (金融数据)
    - MySQL (关系数据库)
    - PyMySQL (驱动)
    - SQLAlchemy (ORM)
    """
    )

with tech_col3:
    st.markdown(
        """
    **项目结构**
    - `app.py` 主入口
    - `pages/` 多页面模块
    - `database/` 数据库层
    - `utils/` 工具函数
    """
    )

st.info("👈 请从左侧边栏选择功能模块开始使用")
