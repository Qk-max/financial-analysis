"""
app.py - 金融数据分析系统入口（登录页）

必须先登录才能进入系统。密码使用 bcrypt 自适应加盐哈希存储。
"""
import logging
import time

import streamlit as st
from database.mysql_conn import SessionLocal, test_connection, init_db, User
from utils.audit import audit_event
from utils.helpers import (
    hash_password,
    verify_password,
    needs_rehash,
    validate_password,
    validate_username,
)

logger = logging.getLogger(__name__)
MAX_LOGIN_FAILURES = 5
LOGIN_LOCK_SECONDS = 60


def login_is_locked() -> bool:
    return time.time() < st.session_state.get("login_locked_until", 0)


def record_login_failure() -> None:
    failures = st.session_state.get("login_failures", 0) + 1
    st.session_state["login_failures"] = failures
    if failures >= MAX_LOGIN_FAILURES:
        st.session_state["login_locked_until"] = time.time() + LOGIN_LOCK_SECONDS
        st.session_state["login_failures"] = 0


def clear_login_failures() -> None:
    st.session_state.pop("login_failures", None)
    st.session_state.pop("login_locked_until", None)

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="金融数据分析系统 - 登录",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ==================== 已登录 → 跳转首页 ====================
if st.session_state.get("logged_in"):
    st.switch_page("pages/1_🏠_首页.py")

# ==================== 数据库初始化 ====================
try:
    init_db()
except Exception:
    pass

db_ok, db_msg = test_connection()

# ==================== 页面样式 ====================
st.markdown(
    """
<style>
    .login-header { text-align:center; padding:20px 0 5px 0; }
    .login-header h1 { font-size:2.2rem; margin-bottom:0; }
    .login-header p { color:#888; font-size:0.95rem; }
    .stButton button { height:2.8rem; font-size:1rem; }
    div[data-testid="stForm"] { border:1px solid #e0e0e0; border-radius:12px; padding:20px; }
    .db-status-badge { text-align:center; font-size:0.8rem; }
</style>
""",
    unsafe_allow_html=True,
)

# ==================== 标题 ====================
st.markdown(
    """
<div class="login-header">
    <h1>📊 金融数据分析系统</h1>
    <p>期末课设项目 · 请先登录以继续</p>
</div>
""",
    unsafe_allow_html=True,
)

# 数据库状态指示
if db_ok:
    st.markdown(
        '<div class="db-status-badge">🟢 数据库已连接</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="db-status-badge">🔴 数据库暂时不可用</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ==================== 登录 / 注册 切换 ====================
# 注册成功后自动跳转到登录页
if st.session_state.get("reg_success"):
    st.session_state["auth_mode"] = "🔐 登录"
    st.success("注册成功！请登录。")
    st.session_state["reg_success"] = False

if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "🔐 登录"

auth_mode = st.radio(
    "选择操作",
    ["🔐 登录", "📝 注册"],
    horizontal=True,
    key="auth_mode",
    label_visibility="collapsed",
)

# ---------- 登录 ----------
if auth_mode == "🔐 登录":
    col_a, col_b, col_c = st.columns([1, 2.5, 1])
    with col_b:
        with st.form("login_form", border=True):
            st.markdown("#### 用户登录")
            username = st.text_input(
                "用户名", placeholder="请输入用户名", key="login_user"
            )
            password = st.text_input(
                "密码", type="password", placeholder="请输入密码", key="login_pass"
            )

            submitted = st.form_submit_button(
                "登 录", type="primary", use_container_width=True
            )

            if submitted:
                if not db_ok:
                    st.error("数据库未连接，请确保 MySQL 已启动")
                elif login_is_locked():
                    st.error("登录尝试过于频繁，请 1 分钟后再试")
                elif not username or not password:
                    st.warning("请填写用户名和密码")
                else:
                    with st.spinner("正在登录..."):
                        db = SessionLocal()
                        try:
                            user = (
                                db.query(User)
                                .filter(User.username == username)
                                .first()
                            )
                            if user and verify_password(password, user.password):
                                # 旧版 SHA-256 哈希自动迁移为 bcrypt
                                if needs_rehash(user.password):
                                    user.password = hash_password(password)
                                    db.commit()
                                st.session_state["logged_in"] = True
                                st.session_state["username"] = username
                                st.session_state["user_id"] = user.id
                                st.session_state["is_admin"] = bool(user.is_admin)
                                clear_login_failures()
                                audit_event("login", actor_user_id=user.id)
                                st.success("登录成功，正在跳转...")
                                redirect = st.session_state.pop("redirect_after_login", None)
                                st.switch_page(redirect or "pages/1_🏠_首页.py")
                            else:
                                record_login_failure()
                                audit_event("login", outcome="failure")
                                st.error("用户名或密码错误")
                        except Exception:
                            logger.exception("登录处理失败")
                            st.error("登录失败，请稍后重试")
                        finally:
                            db.close()

# ---------- 注册 ----------
elif auth_mode == "📝 注册":
    col_a, col_b, col_c = st.columns([1, 2.5, 1])
    with col_b:
        with st.form("register_form", border=True):
            st.markdown("#### 创建账号")
            reg_user = st.text_input(
                "用户名", placeholder="2-20个字符", key="reg_user"
            )
            reg_pass = st.text_input(
                "密码", type="password", placeholder="至少8个字符，含字母和数字", key="reg_pass"
            )
            reg_pass2 = st.text_input(
                "确认密码", type="password", placeholder="请再次输入密码", key="reg_pass2"
            )

            submitted_reg = st.form_submit_button(
                "注 册", type="primary", use_container_width=True
            )

            if submitted_reg:
                if not db_ok:
                    st.error("数据库未连接，请确保 MySQL 已启动")
                elif not reg_user or not reg_pass:
                    st.warning("请填写完整信息")
                elif not validate_username(reg_user)[0]:
                    st.warning(validate_username(reg_user)[1])
                elif not validate_password(reg_pass)[0]:
                    st.warning(validate_password(reg_pass)[1])
                elif reg_pass != reg_pass2:
                    st.warning("两次密码不一致")
                else:
                    with st.spinner("正在注册..."):
                        db = SessionLocal()
                        try:
                            exist = (
                                db.query(User)
                                .filter(User.username == reg_user)
                                .first()
                            )
                            if exist:
                                st.error("用户名已存在")
                            else:
                                user = User(
                                    username=reg_user,
                                    password=hash_password(reg_pass),
                                )
                                db.add(user)
                                db.commit()
                                audit_event("register", actor_user_id=user.id)
                                st.session_state["reg_success"] = True
                                st.success("注册成功！请切换到登录页签进行登录。")
                                st.rerun()
                        except Exception:
                            db.rollback()
                            logger.exception("注册处理失败")
                            st.error("注册失败，请稍后重试")
                        finally:
                            db.close()

# ==================== 底部 ====================
st.markdown("---")
st.caption(
    "提示：请确保 MySQL 已启动，并在 config.py 中配置正确的连接信息。"
    "密码使用 bcrypt 自适应加盐哈希存储。"
)
