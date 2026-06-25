# 本地安全基线

本项目当前仅面向本机验证，不应直接暴露到公网。

## 已实现控制

- Streamlit 仅绑定 `127.0.0.1:8501`，启用 CORS 与 XSRF 防护。
- 数据库凭据通过 `.env` 或系统环境变量提供；`.env` 与 `logs/` 不进入版本控制。
- 应用使用 `financial_user@localhost`，仅具备业务所需的 `SELECT`、`INSERT`、`UPDATE`、`DELETE` 权限。
- 数据库初始化由管理员单独执行 `database/schema.local.sql`；应用运行过程不执行 DDL。
- 密码使用 bcrypt；新密码至少 8 位且同时包含字母与数字；旧 SHA-256 哈希在成功登录后迁移。
- 管理员权限在页面加载时从数据库复核；禁止删除当前管理员或移除最后一个管理员。
- 用户名、股票代码使用格式白名单；持仓表包含唯一、外键与数值检查约束。
- 用户界面不回显数据库异常；认证和管理员操作写入本地审计日志。

## 本地验证清单

1. 复制 `database/schema.local.sql` 为 `database/schema.local.private.sql`，仅在副本中将占位密码替换为强密码，再以 MySQL 管理员账户执行该副本。
2. 将相同密码写入 `.env` 的 `DB_PASSWORD`，且只允许 `DB_HOST=localhost`。
3. 设置强 `ADMIN_PASSWORD` 后运行 `python setup_admin.py`。
4. 运行 `python -m pytest tests -q`。
5. 确认 `netstat -ano | findstr :8501` 仅显示 `127.0.0.1:8501`。
6. 确认 MySQL 业务用户无法执行 `CREATE`、`ALTER` 或 `DROP`。

## 当前边界

- 登录限流在 Streamlit 会话内生效；若未来部署到多用户或公网环境，应在反向代理层补充按 IP 与账号维度的限流。
- 审计日志保存在本机，尚未接入集中日志与告警。
- 上线前还需完成 HTTPS、反向代理、安全响应头、备份恢复演练和依赖漏洞扫描。
