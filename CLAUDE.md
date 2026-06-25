# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 运行与开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用（默认 http://localhost:8501）
streamlit run app.py

# 运行安全回归测试
python -m pytest tests/ -v
```

## 架构概览

这是一个基于 Streamlit 多页面的金融数据分析系统，无前端框架、无后端 API，全部由 Streamlit 原生渲染。

**数据流：** 用户输入股票代码 → `utils/helpers.py::fetch_stock_hist()` → AkShare → Plotly 图表渲染

**多页面机制：** Streamlit 自动扫描 `pages/` 目录，按文件名排序生成侧边栏导航。`app.py` 是首页，每个子页面必须独立调用 `st.set_page_config()`（Streamlit 要求）。

## 关键设计决策

### 双数据源回退

`fetch_stock_hist()` 优先使用新浪财经源（`ak.stock_zh_a_daily`，字段含 date/open/close/high/low/volume/amount），失败则回退到腾讯源（`ak.stock_zh_a_hist_tx`）。新浪源在某些网络环境下会被阻断，腾讯源作为稳定备选。函数返回 `(DataFrame, source_name)` 元组——调用方必须解包两个值。

腾讯源**无 `volume` 字段**，仅含 `date/open/close/high/low/amount`。各页面在绘制成交量图前需检查 `"volume" in df.columns`。

TLS 使用系统默认证书校验；SSL 错误会记录日志并直接回退到备选数据源，不重试。

### 股票名称缓存

`get_stock_name()` 首次调用时通过 `ak.stock_zh_a_spot()` 批量拉取全量 A 股代码→名称映射，存入模块级 `_stock_name_cache` dict。同时缓存带前缀（sh/sz）和无前缀（6 位纯数字）两种 key，因此 O(1) 查找不需网络请求。

### 密码存储

密码使用 **bcrypt** 自适应加盐哈希存储（`hash_password` / `verify_password`），每次哈希自动生成随机盐。`User.password` 列宽 `VARCHAR(255)`。旧版 SHA-256 固定盐哈希在用户登录时透明迁移为 bcrypt（`is_legacy_hash` / `needs_rehash`）。

### 凭据管理

数据库密码通过环境变量 `DB_PASSWORD` 注入，`config.py` 中无硬编码密码。`.env.example` 作为模板；`.env` 和 `config.py`（如含敏感值）已在 `.gitignore`。

### 会话与授权

- **会话**：使用 Streamlit 服务端 session_state（签名 Cookie）。连续 5 次登录失败后锁定当前会话 60 秒。
- **授权**：管理员后台每次加载时从数据库复核当前用户的 `is_admin` 角色；不能删除当前管理员，也不能移除最后一个管理员。普通用户模块仅展示个人信息。

### 数据库模块

- `database/mysql_conn.py` — SQLAlchemy ORM 引擎，`User` / `UserStock` 模型；`init_db()` 仅验证表结构，`test_connection()` 执行健康检查。建库建表仅由 `database/schema.local.sql` 的本地管理员副本执行。

### MySQL 可选运行

用户模块页面在 MySQL 不可用或表结构未初始化时会展示错误提示，登录注册按钮不会执行实际查询。应用运行时不执行 DDL。

### 输入与输出安全

不要使用基于关键词的“SQL 注入/XSS 检测”模拟防护。用户名和股票代码使用格式白名单，密码使用统一策略；数据库访问使用 ORM；任何进入 `unsafe_allow_html=True` 的外部股票名称必须先用 `html.escape()` 转义。

### 页面独立性

每个页面文件顶部都有完整的 import 和 `st.set_page_config()`。页面之间不共享状态（除 `st.session_state` 外），可独立测试。

## 配置文件

`config.py` 通过 `os.getenv()` 读取环境变量，未设置时使用开发默认值。启动时若 `DB_PASSWORD` 为空会输出警告。`.env.example` 提供配置模板。

## 安全测试

`tests/test_security.py` 覆盖 bcrypt 哈希/迁移、配置无硬编码密码、输入格式、管理员鉴权、TLS 证书校验和已下线模块校验。修改安全相关代码后应运行测试验证。
