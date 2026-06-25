"""
安全回归测试 — 覆盖密码存储、会话、授权、配置等关键路径

运行方式：
    cd 项目根目录
    python -m pytest tests/ -v
"""
import os
import sys
import hashlib
import ast
import unittest
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import (
    hash_password,
    verify_password,
    needs_rehash,
    is_legacy_hash,
    validate_password,
    validate_username,
    normalize_stock_code,
)


class TestPasswordHashing(unittest.TestCase):
    """密码哈希与验证 — bcrypt 自适应加盐 + 旧版 SHA-256 迁移"""

    def test_hash_is_bcrypt(self):
        """新密码哈希应以 $2b$ 或 $2a$ 开头（bcrypt 格式）"""
        h = hash_password("test123")
        self.assertTrue(
            h.startswith("$2"),
            f"期望 bcrypt 格式（$2b$/$2a$），实际: {h[:20]}",
        )

    def test_random_salt_per_hash(self):
        """每次哈希应生成不同的盐，即相同密码产生不同哈希"""
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        self.assertNotEqual(h1, h2, "bcrypt 应自动生成随机盐，相同密码不应产生相同哈希")

    def test_verify_correct_password(self):
        """正确密码验证通过"""
        h = hash_password("my_secret")
        self.assertTrue(verify_password("my_secret", h))

    def test_verify_wrong_password(self):
        """错误密码验证失败"""
        h = hash_password("correct")
        self.assertFalse(verify_password("wrong", h))

    def test_verify_empty_password(self):
        """空密码不会被验证通过"""
        h = hash_password("real_password")
        self.assertFalse(verify_password("", h))

    def test_is_legacy_hash_sha256(self):
        """64 字符 hex 字符串（SHA-256）被识别为旧版哈希"""
        legacy = hashlib.sha256(("test" + "fin_analysis_2024").encode()).hexdigest()
        self.assertTrue(is_legacy_hash(legacy))
        self.assertTrue(needs_rehash(legacy))

    def test_is_legacy_hash_bcrypt(self):
        """bcrypt 哈希不被识别为旧版"""
        h = hash_password("test")
        self.assertFalse(is_legacy_hash(h))
        self.assertFalse(needs_rehash(h))

    def test_legacy_hash_verification(self):
        """旧版 SHA-256 哈希仍能被 verify_password 验证（向后兼容）"""
        legacy = hashlib.sha256(
            ("mypassword" + "fin_analysis_2024").encode()
        ).hexdigest()
        self.assertTrue(
            verify_password("mypassword", legacy),
            "旧版 SHA-256 哈希应仍能通过验证（迁移期兼容）",
        )

    def test_legacy_hash_wrong_password(self):
        """旧版哈希 + 错误密码应失败"""
        legacy = hashlib.sha256(
            ("correct" + "fin_analysis_2024").encode()
        ).hexdigest()
        self.assertFalse(verify_password("wrong", legacy))

    def test_tampered_bcrypt_hash(self):
        """被篡改的 bcrypt 哈希不会导致崩溃，而是返回 False"""
        h = hash_password("test")
        tampered = h[:30] + "X" + h[31:]  # 翻转中间一个字符
        self.assertFalse(verify_password("test", tampered))


class TestConfigSecurity(unittest.TestCase):
    """配置安全 — 凭据不硬编码"""

    def test_no_hardcoded_password(self):
        """config.py 从环境变量读取密码，测试不依赖开发机的 .env。"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.py"
        )
        with open(config_path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        assignment = next(
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "DB_PASSWORD" for target in node.targets)
        )
        self.assertIsInstance(assignment.value, ast.Call)
        self.assertEqual(getattr(assignment.value.func, "attr", ""), "getenv")
        self.assertEqual(assignment.value.args[0].value, "DB_PASSWORD")
        self.assertEqual(assignment.value.args[1].value, "")

    def test_env_var_override(self):
        """环境变量应覆盖 config 默认值"""
        os.environ["DB_PASSWORD"] = "test_secret_123"
        # 重新导入以获得新值
        import importlib
        import config
        importlib.reload(config)
        self.assertEqual(config.DB_PASSWORD, "test_secret_123")
        del os.environ["DB_PASSWORD"]
        importlib.reload(config)

    def test_streamlit_binds_only_to_loopback(self):
        root = Path(__file__).resolve().parent.parent
        config = (root / ".streamlit" / "config.toml").read_text(encoding="utf-8")
        self.assertIn('address = "127.0.0.1"', config)
        self.assertIn("enableXsrfProtection = true", config)

    def test_local_only_database_guard(self):
        config_path = Path(__file__).resolve().parent.parent / "config.py"
        source = config_path.read_text(encoding="utf-8")
        self.assertIn("APP_LOCAL_ONLY", source)
        self.assertIn('"127.0.0.1"', source)

    def test_runtime_database_module_has_no_ddl(self):
        root = Path(__file__).resolve().parent.parent
        source = (root / "database" / "mysql_conn.py").read_text(encoding="utf-8")
        self.assertNotIn("create_all", source)
        self.assertNotIn("ALTER TABLE", source)


class TestRemovedModules(unittest.TestCase):
    """已下线模块不应残留可访问页面、静态资源或伪防护代码。"""

    def test_removed_modules_have_no_files(self):
        root = Path(__file__).resolve().parent.parent
        self.assertEqual(list((root / "pages").glob("5_*.py")), [])
        self.assertEqual(list((root / "static").glob("*")), [])
        self.assertFalse((root / "utils" / "security.py").exists())


class TestInputValidation(unittest.TestCase):
    def test_username_policy(self):
        self.assertTrue(validate_username("用户_01")[0])
        self.assertFalse(validate_username("a'")[0])
        self.assertFalse(validate_username("with space")[0])

    def test_password_policy(self):
        self.assertTrue(validate_password("Secure2026")[0])
        self.assertFalse(validate_password("short1")[0])
        self.assertFalse(validate_password("abcdefgh")[0])

    def test_stock_code_policy(self):
        self.assertEqual(normalize_stock_code("1"), "000001")
        self.assertEqual(normalize_stock_code("600519"), "600519")
        self.assertIsNone(normalize_stock_code("60051x"))


class TestAuthorization(unittest.TestCase):
    """授权 — 管理员功能仅限管理员"""

    def _read_page_source(self, filename_pattern: str) -> str:
        import glob
        pages_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "pages",
        )
        for f in glob.glob(os.path.join(pages_dir, filename_pattern)):
            with open(f, "r", encoding="utf-8") as fh:
                return fh.read()
        return ""

    def test_admin_page_checks_is_admin(self):
        """管理员后台每次加载时从数据库复核角色。"""
        source = self._read_page_source("*6_*管理员后台*")
        self.assertIn(
            "current_user = db.query(User)",
            source,
            "管理员后台应从数据库读取当前用户角色",
        )

    def test_setup_admin_requires_environment_password(self):
        root = Path(__file__).resolve().parent.parent
        source = (root / "setup_admin.py").read_text(encoding="utf-8")
        self.assertIn('os.getenv("ADMIN_PASSWORD", "")', source)
        self.assertNotIn('hash_password("admin")', source)


class TestTLSHandling(unittest.TestCase):
    """TLS — 不应全局禁用证书校验"""

    def test_no_global_ssl_disable(self):
        """helpers.py 不应全局禁用 SSL 证书校验"""
        import inspect
        import utils.helpers as helpers_mod

        source = inspect.getsource(helpers_mod)
        self.assertNotIn(
            "_create_unverified_context",
            source,
            "不应全局禁用 SSL 证书校验",
        )
        self.assertNotIn(
            "urllib3.disable_warnings",
            source,
            "不应全局禁用 urllib3 警告",
        )


class TestDataAccessSecurity(unittest.TestCase):
    def test_holding_delete_is_scoped_to_current_user(self):
        root = Path(__file__).resolve().parent.parent
        source = next((root / "pages").glob("1_*.py")).read_text(encoding="utf-8")
        self.assertIn("UserStock.user_id == user_id", source)

    def test_local_schema_uses_a_least_privilege_account(self):
        root = Path(__file__).resolve().parent.parent
        schema = (root / "database" / "schema.local.sql").read_text(encoding="utf-8")
        self.assertIn("GRANT SELECT, INSERT, UPDATE, DELETE", schema)
        self.assertNotIn("GRANT ALL", schema)

    def test_audit_log_is_not_committed(self):
        root = Path(__file__).resolve().parent.parent
        gitignore = (root / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("logs/", gitignore)


if __name__ == "__main__":
    unittest.main()
