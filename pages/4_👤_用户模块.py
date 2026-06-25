"""
用户管理 - 浏览与修改个人信息
"""
import logging

import streamlit as st
import pandas as pd
from database.mysql_conn import User, SessionLocal, test_connection, init_db
from utils.audit import audit_event
from utils.helpers import hash_password, verify_password, validate_password

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="用户管理 - 金融数据分析系统",
    page_icon="👤",
    layout="wide",
)

# 登录守卫
if not st.session_state.get("logged_in"):
    st.switch_page("app.py")
    st.stop()

st.title("👤 用户管理")

# 初始化
try:
    init_db()
except Exception:
    pass

# 数据库状态
db_ok, db_msg = test_connection()

# ---- 已登录 ----
username = st.session_state.get("username", "")
user_id = st.session_state.get("user_id")

st.markdown("---")

# ===== 个人信息 + 修改密码 =====
col_info, col_edit = st.columns([1, 1])

with col_info:
    st.subheader("📋 个人信息")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            st.markdown(f"| 项目 | 内容 |")
            st.markdown(f"|---|---|")
            st.markdown(f"| 用户名 | **{user.username}** |")
            st.markdown(f"| 用户ID | {user.id} |")
            st.markdown(f"| 注册时间 | {user.created_at} |")
            st.markdown(f"| 状态 | 🟢 在线 |")
    except Exception:
        logger.exception("加载用户信息失败")
        st.error("加载用户信息失败，请稍后重试")
    finally:
        db.close()

    # 退出登录
    if st.button("🚪 退出登录", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["user_id"] = None
        st.session_state["is_admin"] = False
        st.rerun()

with col_edit:
    st.subheader("🔒 修改密码")
    with st.form("change_pw", border=True):
        old_pw = st.text_input("原密码", type="password")
        new_pw = st.text_input("新密码", type="password")
        new_pw2 = st.text_input("确认新密码", type="password")
        btn = st.form_submit_button("确认修改", type="primary")

        if btn:
            if not old_pw or not new_pw or not new_pw2:
                st.warning("请填写完整")
            elif not validate_password(new_pw)[0]:
                st.warning(validate_password(new_pw)[1])
            elif new_pw != new_pw2:
                st.warning("两次新密码不一致")
            else:
                db = SessionLocal()
                try:
                    u = db.query(User).filter(User.id == user_id).first()
                    if not u or not verify_password(old_pw, u.password):
                        st.error("原密码错误")
                    else:
                        u.password = hash_password(new_pw)
                        db.commit()
                        audit_event("change_password", actor_user_id=u.id)
                        st.success("密码修改成功！")
                        st.rerun()
                except Exception:
                    db.rollback()
                    logger.exception("修改密码失败")
                    st.error("修改密码失败，请稍后重试")
                finally:
                    db.close()

st.markdown("---")

if not db_ok:
    st.error("数据库暂时不可用")
