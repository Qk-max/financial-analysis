"""
MySQL 数据库连接模块
"""
import logging

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.orm import sessionmaker, declarative_base
import config

logger = logging.getLogger(__name__)

# 创建数据库引擎
try:
    engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception:
    engine = None
    SessionLocal = None
    Base = declarative_base()
    logger.exception("数据库引擎初始化失败")


# ==================== ORM 模型（统一定义，禁止重复） ====================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码(bcrypt)")
    is_admin = Column(Integer, default=0, nullable=False, comment="是否管理员 0=否 1=是")
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), comment="注册时间")


class UserStock(Base):
    __tablename__ = "user_stocks"
    __table_args__ = (
        UniqueConstraint("user_id", "stock_code", name="uq_user_stocks_user_code"),
        CheckConstraint("buy_price > 0", name="ck_user_stocks_buy_price_positive"),
        CheckConstraint("shares > 0", name="ck_user_stocks_shares_positive"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    stock_code = Column(String(6), nullable=False, comment="股票代码")
    stock_name = Column(String(50), nullable=False, comment="股票名称")
    buy_price = Column(Float, default=0.0, comment="买入价格")
    shares = Column(Integer, default=100, comment="持仓股数")
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), comment="添加时间")


# ==================== 工具函数 ====================


def get_db():
    """获取数据库会话（生成器，用于依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """测试数据库连接是否正常"""
    if engine is None:
        return False, "数据库引擎未初始化"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            if not _schema_ready(conn):
                return False, "数据库表结构未初始化"
        return True, "数据库连接成功"
    except Exception:
        logger.warning("数据库健康检查失败", exc_info=True)
        return False, "数据库暂时不可用"


def init_db() -> bool:
    """兼容旧调用：验证必要表存在，不在应用运行时执行 DDL。"""
    if engine is None:
        return False

    try:
        with engine.connect() as conn:
            return _schema_ready(conn)
    except Exception:
        logger.warning("数据库表结构检查失败", exc_info=True)
        return False


def _schema_ready(conn) -> bool:
    tables = {
        row[0]
        for row in conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = DATABASE()"
            )
        )
    }
    return {"users", "user_stocks"}.issubset(tables)
