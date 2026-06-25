# 金融数据分析系统

面向本地学习与验证的 A 股数据分析应用。项目使用 Streamlit 构建界面，
结合 AkShare、Plotly 与 MySQL 提供行情分析、个人持仓和用户管理能力。

> 本项目是课程/作品集性质的本地应用，不提供交易建议，也不应直接暴露到公网。

## 维护与验证说明

- 本仓库为本地课程/作品集应用；运行、测试和发布均以仓库根目录为准，不应将其他历史副本或本地备份作为部署来源。
- 真实凭据只应保存在被 Git 忽略的 `.env` 或系统环境变量中；`config.example.py`、`.env.example` 和 SQL 模板仅允许保留占位值。
- 当前安全措施仅覆盖本地验证场景：bcrypt 密码存储、输入格式校验、基于当前用户的持仓授权、管理员角色复核和本地审计日志。它不构成生产环境安全承诺。
- 提交前请在仓库根目录运行以下检查，并确认未暂存 `.env`、`logs/`、数据库私有初始化文件或其他敏感信息：

```bash
python -m pytest tests -q
python -m compileall -q .
git status --short
```

## 功能概览

| 模块 | 说明 |
| --- | --- |
| 行情分析 | 查询 A 股历史行情，展示 K 线、均线、RSI 与成交量等图表。 |
| 指标统计 | 基于历史数据计算收益率、波动率、最大回撤与日胜率等指标。 |
| 持仓管理 | 用户维护个人持仓；删除操作按当前用户范围授权。 |
| 账户系统 | 注册、登录、修改密码，以及基于数据库角色复核的管理员后台。 |
| 本地审计 | 记录认证和管理操作的元数据，不记录密码、令牌或数据库连接串。 |

## 技术栈

- Python 3.10+
- Streamlit
- AkShare、Pandas、Plotly
- MySQL 8.0+、SQLAlchemy、PyMySQL
- bcrypt

## 安全设计

- 密码使用 bcrypt 存储；新密码至少 8 位，且同时包含字母和数字。
- 登录失败在当前 Streamlit 会话内限流：60 秒内连续 5 次失败后暂时锁定。
- 管理员页面每次加载均从数据库复核 `is_admin`；禁止删除当前管理员或最后一个管理员。
- 用户名、股票代码和持仓数据均有应用层校验；数据库包含唯一、外键和数值检查约束。
- 应用运行账号仅有 `SELECT`、`INSERT`、`UPDATE`、`DELETE` 权限，运行时不执行 DDL。
- Streamlit 与 MySQL 均应仅监听本机回环地址；默认配置启用 CORS 与 XSRF 防护。

完整的本地安全边界、验证步骤和上线前事项见
[SECURITY.md](SECURITY.md)。

## 快速开始

### 1. 获取代码并安装依赖

```bash
git clone https://github.com/Qk-max/financial-analysis.git
cd financial-analysis
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS / Linux：

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置本地环境变量

复制模板后编辑 `.env`。该文件已被 Git 忽略，不要提交真实密码。

```powershell
Copy-Item .env.example .env
```

至少设置以下项目：

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=financial_user
DB_PASSWORD=replace-with-a-strong-password
DB_NAME=financial_analysis
APP_LOCAL_ONLY=true
```

`APP_LOCAL_ONLY=true` 时，程序会拒绝连接非本机数据库主机。

### 3. 初始化 MySQL

应用账号不应拥有建库、建表或修改结构的权限。使用本机 MySQL 管理员账号执行初始化：

1. 复制 `database/schema.local.sql` 为 `database/schema.local.private.sql`；
2. 仅在私有副本中将 `__APP_PASSWORD__` 替换为与 `.env` 中相同的强密码；
3. 使用 MySQL 管理员账号执行该私有副本。

```powershell
mysql -u root -p < database/schema.local.private.sql
```

初始化脚本会创建：

| 表 | 用途 | 关键约束 |
| --- | --- | --- |
| `users` | 用户、bcrypt 密码和管理员标志 | 用户名唯一 |
| `user_stocks` | 用户持仓 | 用户-股票代码唯一、外键级联删除、价格与份额必须为正数 |

### 4. 创建本地管理员

在 `.env` 中设置强密码后执行：

```dotenv
ADMIN_USERNAME=admin
ADMIN_PASSWORD=replace-with-a-strong-password
```

```bash
python setup_admin.py
```

该脚本会创建或重置指定管理员账户；不要在命令行参数、截图或仓库中暴露密码。

### 5. 启动应用

```bash
streamlit run app.py
```

默认访问地址为 <http://127.0.0.1:8501>。`.streamlit/config.toml` 固定绑定
`127.0.0.1`，用于离线本地验证。

## 验证

执行安全回归测试与语法编译检查：

```bash
python -m pytest tests -q
python -m compileall -q .
```

测试覆盖密码哈希、输入校验、权限边界、本地监听约束、运行时无 DDL、
移除的游戏模块和审计日志忽略规则等关键行为。

## 项目结构

```text
.
├── app.py                     # 登录与注册入口
├── pages/                     # 持仓、行情、统计、用户与管理员页面
├── database/
│   ├── mysql_conn.py           # SQLAlchemy 模型与连接检查
│   └── schema.local.sql        # 仅供本机管理员执行的初始化模板
├── utils/
│   ├── audit.py                # 本地安全审计日志
│   └── helpers.py              # 数据处理、校验和密码工具
├── tests/                      # 安全回归测试
├── .env.example                # 环境变量模板
├── SECURITY.md                 # 本地安全基线与边界
└── setup_admin.py              # 管理员账户初始化脚本
```

## 使用边界

- 行情数据依赖第三方数据源，数据可用性和准确性以数据源实际返回为准。
- 本项目不处理真实交易，也不构成投资建议。
- 若要部署到公网，应先完成 HTTPS、反向代理、独立限流、备份恢复演练、
  依赖漏洞扫描和集中日志告警等生产化工作。

## 许可证

当前仓库尚未附加开源许可证；如需公开分发，请先补充明确的许可证文件。
