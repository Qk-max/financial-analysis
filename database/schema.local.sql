-- 仅限本机开发环境：以 MySQL 管理员账户执行。
-- 先将 __APP_PASSWORD__ 替换成强密码，再运行本文件。
-- 应用运行账户不具备 CREATE / ALTER / DROP 权限。

CREATE DATABASE IF NOT EXISTS financial_analysis
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'financial_user'@'localhost'
  IDENTIFIED BY '__APP_PASSWORD__';
ALTER USER 'financial_user'@'localhost'
  IDENTIFIED BY '__APP_PASSWORD__';

GRANT SELECT, INSERT, UPDATE, DELETE
  ON financial_analysis.* TO 'financial_user'@'localhost';
FLUSH PRIVILEGES;

USE financial_analysis;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  password VARCHAR(255) NOT NULL,
  is_admin TINYINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_users_username UNIQUE (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_stocks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  stock_code CHAR(6) NOT NULL,
  stock_name VARCHAR(50) NOT NULL,
  buy_price DECIMAL(12,2) NOT NULL,
  shares INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_user_stocks_user_code UNIQUE (user_id, stock_code),
  CONSTRAINT ck_user_stocks_buy_price_positive CHECK (buy_price > 0),
  CONSTRAINT ck_user_stocks_shares_positive CHECK (shares > 0),
  CONSTRAINT fk_user_stocks_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
