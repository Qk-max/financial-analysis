"""
用户模块 - 登录/注册，MySQL 数据存储
"""
import streamlit as st
from sqlalchemy import Column, Integer, String, DateTime, text
from database.mysql_conn import Base, SessionLocal, init_db, test_connection

st.set_page_config(
    page_title="用户模块 - 金融数据分析系统",
    page_icon="👤",
    layout="wide",
)

st.title("👤 用户模块")

# ==================== 用户 ORM 模型 ====================


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password = Column(String(100), nullable=False, comment="密码")
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), comment="注册时间")


# ==================== 数据库操作函数 ====================


def create_user(username: str, password: str):
    """创建新用户"""
    db = SessionLocal()
    try:
        # 检查用户名是否已存在
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return False, "用户名已存在"
        user = User(username=username, password=password)
        db.add(user)
        db.commit()
        return True, "注册成功"
    except Exception as e:
        db.rollback()
        return False, f"注册失败: {e}"
    finally:
        db.close()


def verify_user(username: str, password: str):
    """验证用户登录"""
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.username == username, User.password == password)
            .first()
        )
        if user:
            return True, "登录成功"
        return False, "用户名或密码错误"
    except Exception as e:
        return False, f"登录失败: {e}"
    finally:
        db.close()


def get_all_users():
    """获取所有用户（管理用）"""
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return users
    except Exception as e:
        return []
    finally:
        db.close()


# ==================== 数据库初始化 ====================
try:
    init_db()
except Exception:
    pass  # MySQL 未启动时忽略建表错误

# 测试数据库连接
connected, conn_msg = test_connection()

if connected:
    st.success(f"✅ 数据库连接正常 — {conn_msg}")
else:
    st.error(f"❌ {conn_msg}")
    st.info("请确保 MySQL 服务已启动，并在 config.py 中配置正确的连接信息")

# ==================== 登录注册布局 ====================

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🔑 用户登录")

    with st.form("login_form"):
        login_username = st.text_input("用户名", key="login_user")
        login_password = st.text_input("密码", type="password", key="login_pass")
        login_btn = st.form_submit_button("登录", type="primary", use_container_width=True)

        if login_btn:
            if not login_username or not login_password:
                st.warning("请输入用户名和密码")
            elif not connected:
                st.error("数据库未连接，无法登录")
            else:
                success, msg = verify_user(login_username, login_password)
                if success:
                    st.success(msg)
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = login_username
                    st.rerun()
                else:
                    st.error(msg)

with col_right:
    st.subheader("📝 用户注册")

    with st.form("register_form"):
        reg_username = st.text_input("用户名", key="reg_user")
        reg_password = st.text_input("密码", type="password", key="reg_pass")
        reg_password2 = st.text_input("确认密码", type="password", key="reg_pass2")
        reg_btn = st.form_submit_button("注册", type="secondary", use_container_width=True)

        if reg_btn:
            if not reg_username or not reg_password:
                st.warning("请填写完整信息")
            elif reg_password != reg_password2:
                st.warning("两次密码不一致")
            elif not connected:
                st.error("数据库未连接，无法注册")
            else:
                success, msg = create_user(reg_username, reg_password)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# ==================== 登录状态显示 ====================

if st.session_state.get("logged_in"):
    st.markdown("---")
    st.subheader(f"🎉 欢迎回来，{st.session_state.get('username', '用户')}！")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.rerun()

# ==================== 用户列表（管理功能） ====================

with st.expander("📋 已注册用户列表"):
    users = get_all_users()
    if users:
        import pandas as pd

        user_data = [
            {"ID": u.id, "用户名": u.username, "注册时间": u.created_at} for u in users
        ]
        st.dataframe(pd.DataFrame(user_data), use_container_width=True, hide_index=True)
    else:
        st.info("暂无注册用户")
