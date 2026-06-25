"""使用环境变量创建或重置管理员账户。"""
import os
from pathlib import Path


def _load_dotenv(env_path: Path) -> None:
    """从 .env 文件加载环境变量（不覆盖已有的环境变量）"""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


# 尝试从项目根目录的 .env 文件加载配置
_project_root = Path(__file__).resolve().parent
_load_dotenv(_project_root / ".env")

from database.mysql_conn import SessionLocal, User
from utils.helpers import hash_password, validate_password, validate_username

admin_username = os.getenv("ADMIN_USERNAME", "admin")
admin_password = os.getenv("ADMIN_PASSWORD", "")

valid, message = validate_username(admin_username)
if not valid:
    raise SystemExit(f"ADMIN_USERNAME 无效：{message}")
valid, message = validate_password(admin_password)
if not valid:
    raise SystemExit(
        f"ADMIN_PASSWORD 无效：{message}。请在 .env 或系统环境变量中设置后重试。"
    )

db = SessionLocal()
try:
    admin = db.query(User).filter(User.username == admin_username).first()
    if admin:
        admin.password = hash_password(admin_password)
        admin.is_admin = 1
    else:
        admin = User(username=admin_username, password=hash_password(admin_password), is_admin=1)
        db.add(admin)
    db.commit()
    print(f"管理员账户已就绪：{admin_username}")
finally:
    db.close()
