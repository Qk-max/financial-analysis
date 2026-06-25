"""
系统配置文件 — 通过环境变量注入敏感信息
"""
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

# 自动加载项目根目录的 .env 文件（若存在）
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# MySQL 数据库配置（优先读取环境变量，未设置则使用开发默认值）
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "financial_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "financial_analysis")
APP_LOCAL_ONLY = os.getenv("APP_LOCAL_ONLY", "true").lower() == "true"

if APP_LOCAL_ONLY and DB_HOST.lower() not in {"localhost", "127.0.0.1", "::1"}:
    raise RuntimeError("本地验证模式仅允许连接 localhost、127.0.0.1 或 ::1")

# 数据库连接URL（密码中的特殊字符需 URL 编码）
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

# 启动前校验：未设置 DB_PASSWORD 时给出警告（不阻止启动，但数据库功能不可用）
if not DB_PASSWORD:
    import sys
    print(
        "[WARNING] 环境变量 DB_PASSWORD 未设置。"
        "数据库功能将不可用。请在 .env 文件或系统环境变量中配置。",
        file=sys.stderr,
    )

# 页面配置
PAGE_TITLE = "金融数据分析系统"
PAGE_ICON = "📊"
LAYOUT = "wide"
