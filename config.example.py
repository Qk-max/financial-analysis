"""
系统配置文件（模板）
复制此文件为 config.py 并填写实际值，或通过 .env 环境变量配置
注意：config.py 和 .env 均包含敏感信息，请勿提交到 Git 仓库
"""
import os
from urllib.parse import quote_plus

# MySQL 数据库配置（优先读取环境变量，未设置则使用默认值）
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "financial_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "financial_analysis")
APP_LOCAL_ONLY = os.getenv("APP_LOCAL_ONLY", "true").lower() == "true"

if APP_LOCAL_ONLY and DB_HOST.lower() not in {"localhost", "127.0.0.1", "::1"}:
    raise RuntimeError("本地验证模式仅允许本机数据库")

# 数据库连接URL
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

# 页面配置
PAGE_TITLE = "金融数据分析系统"
PAGE_ICON = "📊"
LAYOUT = "wide"
