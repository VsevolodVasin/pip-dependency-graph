"""Тесты получения прямых зависимостей из PyPI (без сети)."""

import contextlib
import io
import json
import os
import unittest
from unittest import mock

import pypi
from main import run
from pypi import PypiRepo, RepoError, parse_requires_dist

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS = os.path.join(ROOT, "configs")

REQUESTS_2_31 = [
    "charset-normalizer (<4,>=2)",
    "idna (<4,>=2.5)",
    "urllib3 (<3,>=1.21.1)",
    "certifi (>=2017.4.17)",
    "PySocks (!=1.5.7,>=1.5.6) ; extra == 'socks'",
    "chardet (<6,>=3.0.2) ; extra == 'use_chardet_on_py3'",
]


def fake_response(requires):
    """Имитирует ответ urlopen с заданным requires_dist."""
    body = json.dumps({"info": {"requires_dist": requires}}).encode()
    return contextlib.nullcontext(io.BytesIO(body))


class ParseTest(unittest.TestCase):
    """Разбор строк requires_dist."""

    def test_requests(self):
        """Версии и extras отбрасываются, имена нормализуются."""
        self.assertEqual(parse_requires_dist(REQUESTS_2_31), [
            "charset-normalizer", "idna", "urllib3", "certifi",
        ])

    def test_formats(self):
        """Разные формы записи требований."""
        reqs = [
            "Jinja2>=3.1.2",
            "zope.interface",
            "foo[bar]>=1; python_version < '3.10'",
            "jinja2<4",
        ]
        self.assertEqual(
            parse_requires_dist(reqs), ["jinja2", "zope-interface", "foo"]
        )

    def test_empty(self):
        """requires_dist может быть null."""
        self.assertEqual(parse_requires_dist(None), [])

    def test_bad_requirement(self):
        """Нераспознаваемая строка — ошибка."""
        with self.assertRaises(RepoError):
            parse_requires_dist(["(>=1.0)"])


class PypiRepoTest(unittest.TestCase):
    """Запрос метаданных конкретной версии."""

    @mock.patch.object(pypi.urllib.request, "urlopen")
    def test_get_deps_version_url(self, urlopen):
        """URL содержит имя и версию пакета."""
        urlopen.return_value = fake_response(REQUESTS_2_31)
        deps = PypiRepo("https://pypi.org/pypi/").get_deps(
            "requests", "2.31.0"
        )
        self.assertEqual(len(deps), 4)
        url = urlopen.call_args[0][0]
        self.assertEqual(url, "https://pypi.org/pypi/requests/2.31.0/json")

    @mock.patch.object(pypi.urllib.request, "urlopen")
    def test_run_prints_direct_deps(self, urlopen):
        """run печатает пакет и его прямые зависимости."""
        urlopen.return_value = fake_response(REQUESTS_2_31)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = run(["--config", os.path.join(CONFIGS, "pypi.csv")])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().splitlines(), [
            "requests==2.31.0:",
            "  charset-normalizer",
            "  idna",
            "  urllib3",
            "  certifi",
        ])

    @mock.patch.object(pypi.urllib.request, "urlopen")
    def test_http_error(self, urlopen):
        """HTTP-ошибка превращается в RepoError и код 1."""
        urlopen.side_effect = pypi.urllib.error.HTTPError(
            "url", 404, "Not Found", None, None
        )
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = run(["--config", os.path.join(CONFIGS, "pypi.csv")])
        self.assertEqual(code, 1)
        self.assertIn("HTTP 404", err.getvalue())


if __name__ == "__main__":
    unittest.main()
