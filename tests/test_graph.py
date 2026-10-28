"""Тесты построения графа зависимостей на тестовых репозиториях."""

import contextlib
import io
import os
import unittest

from graph import build_graph, format_graph
from main import run
from pypi import RepoError
from testrepo import FileRepo, parse_test_repo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = os.path.join(ROOT, "test_repos")
CONFIGS = os.path.join(ROOT, "configs")


def graph_of(text, max_depth=10, root="A"):
    """Строит граф по тексту тестового репозитория."""
    repo = FileRepo.__new__(FileRepo)
    repo.packages = parse_test_repo(text)
    return build_graph(repo, root, "1.0", max_depth)


class ParseTestRepoTest(unittest.TestCase):
    """Разбор файла тестового репозитория."""

    def test_basic_file(self):
        """Файл basic.txt читается в словарь зависимостей."""
        repo = FileRepo(os.path.join(REPOS, "basic.txt"))
        self.assertEqual(repo.packages, {
            "A": ["B", "C"], "B": ["D"], "C": ["D"], "D": [],
        })

    def test_errors(self):
        """Неверные строки и имена вызывают RepoError."""
        for text in ("A B", "a: B", "A: B1", "A:\nA:"):
            with self.subTest(text=text):
                with self.assertRaises(RepoError):
                    parse_test_repo(text)

    def test_comments(self):
        """Комментарии и пустые строки пропускаются."""
        self.assertEqual(parse_test_repo("# x\n\nA: B\nB:"), {
            "A": ["B"], "B": [],
        })


class BuildGraphTest(unittest.TestCase):
    """Обход DFS: транзитивность, глубина, циклы."""

    def test_diamond(self):
        """Общая зависимость раскрывается один раз."""
        g = graph_of("A: B C\nB: D\nC: D\nD:")
        self.assertEqual(g.edges, {
            "A": ["B", "C"], "B": ["D"], "D": [], "C": ["D"],
        })
        self.assertEqual(g.cycles, [])

    def test_max_depth(self):
        """Узлы на максимальной глубине не раскрываются."""
        g = graph_of("A: B\nB: C\nC: D\nD:", max_depth=2)
        self.assertEqual(g.edges, {"A": ["B"], "B": ["C"]})
        self.assertEqual(g.cut, {"C"})

    def test_depth_one(self):
        """Глубина 1 — только прямые зависимости."""
        g = graph_of("A: B C\nB: D\nC:\nD:", max_depth=1)
        self.assertEqual(g.edges, {"A": ["B", "C"]})
        self.assertEqual(g.cut, {"B", "C"})

    def test_shorter_path_reexpands(self):
        """Узел, найденный глубже, раскрывается по более короткому пути."""
        g = graph_of("A: B C\nB: C\nC: D\nD: E\nE:", max_depth=3)
        self.assertEqual(g.edges["D"], ["E"])
        self.assertEqual(g.cut, {"E"})

    def test_cycle(self):
        """Цикл A -> B -> C -> A найден, обход завершается."""
        g = graph_of("A: B\nB: C\nC: A")
        self.assertEqual(g.cycles, [["A", "B", "C", "A"]])

    def test_self_loop(self):
        """Пакет, зависящий от самого себя."""
        g = graph_of("A: A B\nB:")
        self.assertEqual(g.cycles, [["A", "A"]])

    def test_complex_cycles(self):
        """Несколько циклов без повторов."""
        g = graph_of(open(os.path.join(REPOS, "complex.txt")).read())
        self.assertEqual(g.cycles, [["B", "D", "B"], ["C", "F", "C"]])
        self.assertEqual(len(g.nodes()), 7)

    def test_missing_package(self):
        """Ссылка на неописанный пакет — ошибка."""
        with self.assertRaises(RepoError):
            graph_of("A: B")


class OutputTest(unittest.TestCase):
    """Текстовый вывод графа."""

    def test_format(self):
        """Рёбра, листья, обрезанные узлы и циклы."""
        g = graph_of("A: B C\nB: A\nC: D\nD:", max_depth=2)
        self.assertEqual(format_graph(g), [
            "A -> B, C", "B -> A", "C -> D", "D (max depth)",
            "cycle: A -> B -> A",
        ])

    def test_run_test_mode(self):
        """run в режиме тестового репозитория печатает граф."""
        cwd = os.getcwd()
        os.chdir(ROOT)
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = run(["--config", os.path.join(CONFIGS, "test.csv")])
        finally:
            os.chdir(cwd)
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().splitlines(), [
            "A -> B, C", "B -> D", "D", "C -> D",
        ])


if __name__ == "__main__":
    unittest.main()
