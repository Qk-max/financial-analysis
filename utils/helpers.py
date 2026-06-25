"""
通用工具函数
"""
import time
import logging
import re
import pandas as pd

logger = logging.getLogger(__name__)


MIN_PASSWORD_LENGTH = 8
_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_\u4e00-\u9fff]{2,20}$")
_STOCK_CODE_PATTERN = re.compile(r"^\d{6}$")


def validate_username(username: str) -> tuple[bool, str]:
    """校验用户名，避免将任意显示层输入带入管理操作。"""
    if not isinstance(username, str) or not _USERNAME_PATTERN.fullmatch(username):
        return False, "用户名需为 2-20 个中文、字母、数字或下划线"
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """提供一致的密码策略；密码哈希仍由 bcrypt 负责。"""
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        return False, f"密码至少 {MIN_PASSWORD_LENGTH} 个字符"
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return False, "密码需同时包含字母和数字"
    return True, ""


def normalize_stock_code(stock_code: str) -> str | None:
    """仅接受 6 位 A 股代码，拒绝其他输入后再请求第三方数据源。"""
    normalized = str(stock_code or "").strip().zfill(6)
    return normalized if _STOCK_CODE_PATTERN.fullmatch(normalized) else None


# 内存缓存股票代码→名称映射
_stock_name_cache: dict = {}


def get_stock_name(stock_code: str) -> str:
    """根据股票代码获取中文名称（带缓存，首次调用拉取全量列表）"""
    if stock_code in _stock_name_cache:
        return _stock_name_cache[stock_code]

    # 首次调用：批量拉取所有A股代码→名称映射
    if not _stock_name_cache:
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot()
            if df is not None and not df.empty:
                code_col = df.columns[0]
                name_col = df.columns[1]
                for _, row in df.iterrows():
                    full_code = str(row[code_col])
                    name = str(row[name_col])
                    if not full_code or not name:
                        continue
                    _stock_name_cache[full_code] = name
                    # 也存无前缀版本（sz000001 → 000001）
                    if len(full_code) == 8:
                        _stock_name_cache[full_code[2:]] = name
        except Exception:
            pass

    return _stock_name_cache.get(stock_code, stock_code)


def fetch_stock_hist(stock_code, period="daily", start_date="", end_date="", max_retries=3):
    """
    股票历史数据获取

    优先使用新浪财经源（数据字段更全），失败则回退到腾讯源。
    使用系统默认 TLS 证书校验。返回 (DataFrame, source_name)
    """
    import akshare as ak
    from requests.exceptions import SSLError

    # 判断市场前缀
    if stock_code.startswith("6") or stock_code.startswith("9"):
        symbol = f"sh{stock_code}"
    else:
        symbol = f"sz{stock_code}"

    # ---- 源1: 新浪财经（字段全：日期/开/高/低/收/成交量/成交额） ----
    last_error = None
    for attempt in range(max_retries):
        try:
            df = ak.stock_zh_a_daily(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )
            if df is not None and not df.empty:
                cols = df.columns.tolist()
                rename_map = {}
                if "date" not in cols:
                    rename_map["日期"] = "date"
                for src, dst in [
                    ("开盘价", "open"), ("收盘价", "close"), ("最高价", "high"), ("最低价", "low"),
                    ("成交量", "volume"), ("成交额", "amount"),
                ]:
                    if src in cols:
                        rename_map[src] = dst
                if rename_map:
                    df = df.rename(columns=rename_map)
                df["date"] = pd.to_datetime(df["date"])
                return df, "sina"
        except SSLError as e:
            last_error = e
            logger.error("新浪数据源 TLS 证书校验失败（系统证书可能过期或受损）: %s", e)
            break  # TLS 错误不重试，直接回退
        except Exception as e:
            last_error = e
            logger.warning("新浪数据源请求失败（第 %d/%d 次）: %s", attempt + 1, max_retries, e)
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 1.5)

    # ---- 源2: 腾讯（回退源） ----
    try:
        df = ak.stock_zh_a_hist_tx(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
        if df is not None and not df.empty:
            df = df.rename(columns={
                "date": "date", "open": "open", "close": "close",
                "high": "high", "low": "low", "amount": "amount",
            })
            df["date"] = pd.to_datetime(df["date"])
            return df, "tencent"
    except SSLError as e:
        logger.error("腾讯数据源 TLS 证书校验失败: %s", e)
    except Exception as e:
        logger.warning("腾讯数据源请求失败: %s", e)

    raise last_error or RuntimeError("数据获取失败：所有数据源均不可用")


def safe_float(value, default=0.0):
    """安全转换为浮点数"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def format_pct(value, decimals=2):
    """格式化为百分比字符串"""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


def calc_ma(df, periods=(5, 10, 20, 60)):
    """计算移动平均线"""
    for p in periods:
        df[f"MA{p}"] = df["close"].rolling(window=p).mean()
    return df


def calc_rsi(df, period=14):
    """计算 RSI 指标"""
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


# ==================== 密码哈希工具 ====================
import hashlib
import bcrypt

# 旧版固定盐（仅用于迁移期间识别老密码；绝不用于新哈希）
_OLD_SALT = "fin_analysis_2024"


def hash_password(password: str) -> str:
    """使用 bcrypt 对密码进行自适应加盐哈希（自动生成随机盐）"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, stored_hash: str) -> bool:
    """
    验证密码是否匹配。
    支持 bcrypt 哈希和旧版 SHA-256 哈希（透明迁移）。
    返回 (is_valid, needs_rehash) 元组。
    """
    # bcrypt 哈希以 $2b$ 或 $2a$ 开头
    if stored_hash.startswith("$2"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            return False

    # 兼容旧版 SHA-256 固定盐哈希（迁移期）
    old_hash = hashlib.sha256((password + _OLD_SALT).encode("utf-8")).hexdigest()
    return old_hash == stored_hash


def is_legacy_hash(stored_hash: str) -> bool:
    """判断是否为旧版 SHA-256 哈希（需要迁移）"""
    return not stored_hash.startswith("$2")


def needs_rehash(stored_hash: str) -> bool:
    """检查密码哈希是否需要升级（旧版 SHA-256 → bcrypt）"""
    return is_legacy_hash(stored_hash)
