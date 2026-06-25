"""本地安全审计：只记录操作元数据，严禁写入密码、令牌或连接串。"""
import json
import logging
from pathlib import Path
from typing import Any


_log_dir = Path(__file__).resolve().parent.parent / "logs"
_log_dir.mkdir(exist_ok=True)
_logger = logging.getLogger("financial_analysis.audit")

if not _logger.handlers:
    _handler = logging.FileHandler(_log_dir / "security-audit.log", encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def audit_event(
    action: str,
    *,
    actor_user_id: int | None = None,
    target_type: str = "",
    target_id: int | None = None,
    outcome: str = "success",
) -> None:
    """写入结构化审计事件；调用方不得传递敏感业务内容。"""
    event: dict[str, Any] = {
        "action": action,
        "actor_user_id": actor_user_id,
        "target_type": target_type,
        "target_id": target_id,
        "outcome": outcome,
    }
    _logger.info(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
