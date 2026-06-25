"""
管理员后台 - 用户与用户股票管理
"""
import logging

import streamlit as st
import pandas as pd
from database.mysql_conn import User, UserStock, SessionLocal, test_connection, init_db
from utils.audit import audit_event
from utils.helpers import (
    hash_password,
    validate_password,
    validate_username,
)

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="管理员后台 - 金融数据分析系统",
    page_icon="🔧",
    layout="wide",
)

# ==================== 登录守卫 ====================
if not st.session_state.get("logged_in"):
    st.switch_page("app.py")
    st.stop()

current_user_id = st.session_state.get("user_id")
try:
    db = SessionLocal()
    current_user = db.query(User).filter(User.id == current_user_id).first()
except Exception:
    logger.exception("管理员角色校验失败")
    st.error("无法验证管理员权限，请稍后重试")
    st.stop()
finally:
    if "db" in locals():
        db.close()

if not current_user or not current_user.is_admin:
    st.session_state["is_admin"] = False
    st.error("⛔ 您没有管理员权限，无法访问此页面。")
    st.stop()

# ==================== 数据库初始化 ====================
try:
    init_db()
except Exception:
    pass

db_ok, db_msg = test_connection()

st.title("🔧 管理员后台")
st.caption("仅管理员可访问此页面")
st.markdown("---")

# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("📊 金融数据分析")
    st.markdown(f"👤 **{st.session_state.get('username', '')}** (管理员)")
    if st.button("🚪 退出", use_container_width=True):
        for key in ["logged_in", "username", "user_id", "is_admin"]:
            st.session_state[key] = False if key == "logged_in" else ("" if key == "username" else None)
        st.switch_page("app.py")


# ==================== 工具函数 ====================

def get_all_users():
    db = SessionLocal()
    try:
        return db.query(User).order_by(User.id).all()
    finally:
        db.close()


def get_all_user_stocks():
    db = SessionLocal()
    try:
        return (
            db.query(UserStock, User.username)
            .join(User, UserStock.user_id == User.id)
            .order_by(UserStock.id.desc())
            .all()
        )
    finally:
        db.close()


def update_user(user_id, username, password, is_admin, actor_id):
    valid, message = validate_username(username)
    if not valid:
        return False, message
    if password:
        valid, message = validate_password(password)
        if not valid:
            return False, message
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"
        admin_count = db.query(User).filter(User.is_admin == 1).count()
        if user.id == actor_id and not is_admin:
            return False, "不能移除当前管理员自己的管理员权限"
        if user.is_admin and not is_admin and admin_count <= 1:
            return False, "系统至少需要保留一个管理员"
        # 检查用户名是否被其他用户占用
        exist = db.query(User).filter(User.username == username, User.id != user_id).first()
        if exist:
            return False, "用户名已被占用"
        user.username = username
        if password:
            user.password = hash_password(password)
        user.is_admin = 1 if is_admin else 0
        db.commit()
        audit_event(
            "update_user",
            actor_user_id=actor_id,
            target_type="user",
            target_id=user.id,
        )
        return True, "更新成功"
    except Exception:
        db.rollback()
        logger.exception("管理员更新用户失败")
        return False, "更新失败，请稍后重试"
    finally:
        db.close()


def delete_user(user_id, actor_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"
        if user.id == actor_id:
            return False, "不能删除当前登录的管理员账户"
        if user.is_admin and db.query(User).filter(User.is_admin == 1).count() <= 1:
            return False, "系统至少需要保留一个管理员"
        # 级联删除用户的股票收藏
        db.query(UserStock).filter(UserStock.user_id == user_id).delete()
        db.delete(user)
        db.commit()
        audit_event(
            "delete_user",
            actor_user_id=actor_id,
            target_type="user",
            target_id=user_id,
        )
        return True, "删除成功（含关联股票数据）"
    except Exception:
        db.rollback()
        logger.exception("管理员删除用户失败")
        return False, "删除失败，请稍后重试"
    finally:
        db.close()


def add_user(username, password, is_admin=False, actor_id=None):
    valid, message = validate_username(username)
    if not valid:
        return False, message
    valid, message = validate_password(password)
    if not valid:
        return False, message
    db = SessionLocal()
    try:
        exist = db.query(User).filter(User.username == username).first()
        if exist:
            return False, "用户名已存在"
        user = User(
            username=username,
            password=hash_password(password),
            is_admin=1 if is_admin else 0,
        )
        db.add(user)
        db.commit()
        audit_event(
            "create_user",
            actor_user_id=actor_id,
            target_type="user",
            target_id=user.id,
        )
        return True, "添加成功"
    except Exception:
        db.rollback()
        logger.exception("管理员添加用户失败")
        return False, "添加失败，请稍后重试"
    finally:
        db.close()


def delete_user_stock(stock_id, actor_id):
    db = SessionLocal()
    try:
        stock = db.query(UserStock).filter(UserStock.id == stock_id).first()
        if not stock:
            return False, "记录不存在"
        db.delete(stock)
        db.commit()
        audit_event(
            "delete_user_stock",
            actor_user_id=actor_id,
            target_type="user_stock",
            target_id=stock_id,
        )
        return True, "删除成功"
    except Exception:
        db.rollback()
        logger.exception("管理员删除股票记录失败")
        return False, "删除失败，请稍后重试"
    finally:
        db.close()


# ==================== Tab 1: 用户管理 ====================
tab_users, tab_stocks = st.tabs(["👥 用户管理", "📈 用户股票管理"])

with tab_users:
    st.subheader("👥 用户列表")
    users = get_all_users()
    if users:
        user_data = [
            {
                "ID": u.id,
                "用户名": u.username,
                "是否管理员": "✅ 是" if u.is_admin else "❌ 否",
                "注册时间": u.created_at,
            }
            for u in users
        ]
        st.dataframe(pd.DataFrame(user_data), use_container_width=True, hide_index=True)
        st.caption(f"共 {len(users)} 名用户")
    else:
        st.info("暂无用户")

    st.markdown("---")
    st.subheader("✏️ 编辑 / 删除用户")

    col_edit, col_del = st.columns(2)

    with col_edit:
        with st.form("edit_user_form", border=True):
            st.markdown("**修改用户信息**")
            edit_id = st.number_input("用户ID", min_value=1, step=1, key="edit_id")
            edit_name = st.text_input("新用户名", placeholder="留空则不修改", key="edit_name")
            edit_pw = st.text_input("新密码", type="password", placeholder="留空则不修改", key="edit_pw")
            edit_admin = st.checkbox("设为管理员", key="edit_admin")
            submitted = st.form_submit_button("💾 保存修改", type="primary")
            if submitted:
                if edit_id and edit_name:
                    ok, msg = update_user(edit_id, edit_name, edit_pw, edit_admin, current_user_id)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("请填写用户ID和新用户名")

    with col_del:
        with st.form("del_user_form", border=True):
            st.markdown("**删除用户**")
            del_id = st.number_input("要删除的用户ID", min_value=1, step=1, key="del_id")
            st.warning("⚠️ 删除用户会同时删除其所有股票收藏记录！")
            submitted = st.form_submit_button("🗑️ 确认删除", type="primary")
            if submitted:
                if del_id:
                    ok, msg = delete_user(del_id, current_user_id)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("请填写用户ID")

    st.markdown("---")
    st.subheader("➕ 添加新用户")
    with st.form("add_user_form", border=True):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("用户名", placeholder="2-20个字符")
            new_pw = st.text_input("密码", type="password", placeholder="至少8个字符，含字母和数字")
        with col2:
            new_pw2 = st.text_input("确认密码", type="password")
            new_admin = st.checkbox("设为管理员")
        submitted = st.form_submit_button("➕ 添加用户", type="primary")
        if submitted:
            if not new_name or not new_pw:
                st.warning("请填写完整信息")
            elif not validate_username(new_name)[0]:
                st.warning(validate_username(new_name)[1])
            elif not validate_password(new_pw)[0]:
                st.warning(validate_password(new_pw)[1])
            elif new_pw != new_pw2:
                st.warning("两次密码不一致")
            else:
                ok, msg = add_user(new_name, new_pw, new_admin, current_user_id)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# ==================== Tab 2: 用户股票管理 ====================
with tab_stocks:
    st.subheader("📈 所有用户股票收藏")
    stocks = get_all_user_stocks()
    if stocks:
        stock_data = [
            {
                "ID": s.UserStock.id,
                "用户": s.username,
                "股票代码": s.UserStock.stock_code,
                "股票名称": s.UserStock.stock_name,
                "买入价": s.UserStock.buy_price,
                "持仓股数": s.UserStock.shares,
                "添加时间": s.UserStock.created_at,
            }
            for s in stocks
        ]
        st.dataframe(pd.DataFrame(stock_data), use_container_width=True, hide_index=True)
        st.caption(f"共 {len(stocks)} 条记录")
    else:
        st.info("暂无用户股票收藏记录")

    st.markdown("---")
    st.subheader("🗑️ 删除股票记录")
    with st.form("del_stock_form", border=True):
        del_stock_id = st.number_input("要删除的记录ID", min_value=1, step=1)
        submitted = st.form_submit_button("🗑️ 确认删除", type="primary")
        if submitted:
            if del_stock_id:
                ok, msg = delete_user_stock(del_stock_id, current_user_id)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("请填写记录ID")


if not db_ok:
    st.error("数据库暂时不可用")
