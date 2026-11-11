"""Тесты этапа 4: обратные зависимости."""

import contextlib
import io
import os
import unittest

from graph import format_graph
from main import run
from ops import reverse_graph, reverse_repo
from pypi import RepoError
from testrepo import FileRepo, parse_test_repo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS = os.path.join(ROOT, "configs")


def repo_of(text):
    """Тестовый репозиторий из текста."""
    repo = FileRepo.__new__(FileRepo)
    repo.packages = parse_test_repo(text)
    return repo


class FakePypi:
    """PyPI без сети: flask -> werkzeug, jinja2 -> markupsafe."""

    def __init__(self):
        """Прямые зависимости пакетов."""
        self.deps = {"flask": ["werkzeug", "jinja2"],
                     "werkzeug": ["markupsafe"],
                     "jinja2": ["markupsafe"], "markupsafe": []}

    def get_deps(self, name, version=None):
        """Прямые зависимости пакета."""
        return list(self.deps[name])


def run_lines(*argv):
    """Запускает CLI из корня проекта, возвращает (код, строки stdout)."""
    cwd = os.getcwd()
    os.chdir(ROOT)
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(io.StringIO()):
            code = run(list(argv))
    finally:
        os.chdir(cwd)
    return code, out.getvalue().splitlines()


class ReverseTest(unittest.TestCase):
    """Обратные зависимости."""

    def test_diamond(self):
        """От D зависят B и C, от них — A."""
        g = reverse_graph(repo_of("A: B C\nB: D\nC: D\nD:"), "D", 10)
        self.assertEqual(g.edges, {
            "D": ["B", "C"], "B": ["A"], "A": [], "C": ["A"],
        })

    def test_transitive_depth(self):
        """max_depth ограничивает длину обратного пути."""
        g = reverse_graph(repo_of("A: B\nB: C\nC: D\nD:"), "D", 2)
        self.assertEqual(g.edges, {"D": ["C"], "C": ["B"]})
        self.assertEqual(g.cut, {"B"})

    def test_no_dependents(self):
        """От корневого пакета никто не зависит."""
        g = reverse_graph(repo_of("A: B\nB:"), "A", 10)
        self.assertEqual(g.edges, {"A": []})

    def test_cycle(self):
        """Цикл находится и в обратном графе."""
        g = reverse_graph(repo_of("A: B\nB: C\nC: A"), "B", 10)
        self.assertEqual(g.cycles, [["A", "C", "B", "A"]])

    def test_unknown_package(self):
        """Пакета нет в репозитории — ошибка."""
        with self.assertRaises(RepoError):
            reverse_graph(repo_of("A:"), "Z", 10)

    def test_pypi_graph(self):
        """PyPI: зависящие пакеты ищутся в графе корня (DFS этапа 3)."""
        back = reverse_repo(FakePypi(), "flask", "3.0.0", 10)
        g = reverse_graph(back, "markupsafe", 10)
        self.assertEqual(g.edges, {
            "markupsafe": ["werkzeug", "jinja2"], "werkzeug": ["flask"],
            "flask": [], "jinja2": ["flask"],
        })

    def test_pypi_unknown_target(self):
        """Пакета нет в графе корня — ошибка с понятным текстом."""
        back = reverse_repo(FakePypi(), "flask", "3.0.0", 10)
        with self.assertRaisesRegex(RepoError, "dependency graph of flask"):
            reverse_graph(back, "nope", 10)

    def test_format(self):
        """Вывод со стрелкой <-."""
        g = reverse_graph(repo_of("A: B C\nB: D\nC: D\nD:"), "D", 10)
        self.assertEqual(format_graph(g, "<-"), [
            "D <- B, C", "B <- A", "A", "C <- A",
        ])

    def test_run_complex(self):
        """CLI: обратные зависимости G в complex.txt."""
        code, lines = run_lines(
            "--config", os.path.join(CONFIGS, "test_reverse_complex.csv"),
            "--mode", "reverse",
        )
        self.assertEqual(code, 0)
        self.assertEqual(lines[0], "G <- E, F")
        self.assertIn("cycle: B <- D <- B", lines)



if __name__ == "__main__":
    unittest.main()
