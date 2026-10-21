"""Тесты загрузки и проверки конфигурации."""

import contextlib
import io
import os
import unittest

from config import ConfigError, load_config
from main import run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS = os.path.join(ROOT, "configs")
ERRORS = os.path.join(CONFIGS, "errors")


class LoadConfigTest(unittest.TestCase):
    """Проверка load_config на валидных и ошибочных конфигах."""

    def setUp(self):
        """Пути к тестовым репозиториям заданы относительно корня."""
        self.cwd = os.getcwd()
        os.chdir(ROOT)

    def tearDown(self):
        """Возвращает исходный рабочий каталог."""
        os.chdir(self.cwd)

    def test_pypi(self):
        """Удалённый режим: все параметры прочитаны и приведены."""
        cfg = load_config(os.path.join(CONFIGS, "pypi.csv"))
        self.assertEqual(cfg, {
            "package_name": "requests",
            "repo": "https://pypi.org/pypi",
            "test_repo_mode": False,
            "version": "2.31.0",
            "max_depth": 3,
        })

    def test_test_repo(self):
        """Тестовый режим: repo — существующий файл."""
        cfg = load_config(os.path.join(CONFIGS, "test.csv"))
        self.assertTrue(cfg["test_repo_mode"])
        self.assertEqual(cfg["repo"], "test_repos/basic.txt")
        self.assertEqual(cfg["max_depth"], 5)

    def test_errors(self):
        """Каждый конфиг из configs/errors вызывает ConfigError."""
        cases = {
            "nope.csv": "config file not found",
            "missing_key.csv": "missing keys",
            "unknown_key.csv": "unknown key",
            "name.csv": "package_name",
            "repo_url.csv": "repo: expected http(s) URL",
            "repo_file.csv": "repo: test repository file not found",
            "mode.csv": "test_repo_mode",
            "version.csv": "version",
            "depth.csv": "max_depth: expected integer",
            "depth_zero.csv": "max_depth: must be >= 1",
        }
        for name, message in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(ConfigError) as ctx:
                    load_config(os.path.join(ERRORS, name))
                self.assertIn(message, str(ctx.exception))


class RunTest(unittest.TestCase):
    """Проверка вывода и кода возврата run."""

    def test_prints_key_value(self):
        """Параметры печатаются как ключ=значение."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = run(["--config", os.path.join(CONFIGS, "pypi.csv")])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().splitlines(), [
            "package_name=requests",
            "repo=https://pypi.org/pypi",
            "test_repo_mode=false",
            "version=2.31.0",
            "max_depth=3",
        ])

    def test_error_exit_code(self):
        """При ошибке сообщение уходит в stderr, код 1."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = run(["--config", os.path.join(ERRORS, "version.csv")])
        self.assertEqual(code, 1)
        self.assertIn("error: version", err.getvalue())


if __name__ == "__main__":
    unittest.main()
