"""Тесты этапа 5: описание графа на Graphviz DOT и сохранение."""

import contextlib
import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

from graph import build_graph
from main import run
from ops import reverse_graph
from testrepo import FileRepo, parse_test_repo
import viz
from viz import RenderError, check_output, quote, save, to_dot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS = os.path.join(ROOT, "configs")


def repo_of(text):
    """Тестовый репозиторий из текста."""
    repo = FileRepo.__new__(FileRepo)
    repo.packages = parse_test_repo(text)
    return repo


class DotTest(unittest.TestCase):
    """Генерация DOT."""

    def test_edges_and_styles(self):
        """Рёбра, корень, обрезанный узел и цикл."""
        g = build_graph(repo_of("A: B C\nB: A\nC: D\nD:"), "A", "1.0", 2)
        dot = to_dot(g)
        self.assertTrue(dot.startswith("digraph dependencies {"))
        self.assertIn('"A" -> "C";', dot)
        self.assertIn('"A" -> "B" [color=red];', dot)
        self.assertIn('"B" -> "A" [color=red];', dot)
        self.assertIn('"A" [style="rounded,filled"', dot)
        self.assertIn('"D" [style="rounded,dashed", xlabel="max depth"]', dot)
        self.assertTrue(dot.rstrip().endswith("}"))

    def test_reverse_keeps_direction(self):
        """Обратный граф: стрелка идёт от пакета к его зависимости."""
        g = reverse_graph(repo_of("A: B\nB:"), "B", 10)
        self.assertIn('"A" -> "B";', to_dot(g, reverse=True))

    def test_version_labels(self):
        """Версия под именем пакета, ограничения с условием на ребре."""
        g = build_graph(repo_of("A: B\nB:"), "A", "1.0", 10)
        g.versions = {"A": "1.0", "B": "2.1"}
        g.specs = {"A": {"B": ">=2; python_version < '3.10'"}}
        dot = to_dot(g)
        self.assertIn('"A" [label="A\\n1.0"', dot)
        self.assertIn('"B" [label="B\\n2.1"];', dot)
        self.assertIn(
            '"A" -> "B" [label=">=2; python_version < \'3.10\'"];', dot)

    def test_quote(self):
        """Кавычки в имени экранируются."""
        self.assertEqual(quote('a"b'), '"a\\"b"')


class SaveTest(unittest.TestCase):
    """Сохранение в файл."""

    def setUp(self):
        """Временный каталог для файлов."""
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        """Удаляет временный каталог."""
        shutil.rmtree(self.tmp)

    def test_dot_file(self):
        """.dot сохраняется как текст."""
        path = os.path.join(self.tmp, "g.dot")
        save("digraph {}\n", path)
        with open(path) as f:
            self.assertEqual(f.read(), "digraph {}\n")

    @unittest.skipIf(shutil.which("dot") is None, "graphviz not installed")
    def test_svg_file(self):
        """.svg рендерится через Graphviz."""
        path = os.path.join(self.tmp, "g.svg")
        save('digraph { "A" -> "B"; }\n', path)
        with open(path) as f:
            self.assertIn("<svg", f.read())

    def test_bad_output(self):
        """Неизвестный формат и несуществующий каталог — ошибки."""
        for path in ("g.jpg", os.path.join(self.tmp, "no", "g.png")):
            with self.subTest(path=path):
                with self.assertRaises(RenderError):
                    check_output(path)

    def test_run_mode_dot(self):
        """CLI --mode dot печатает DOT, --output сохраняет файл."""
        path = os.path.join(self.tmp, "g.dot")
        cwd = os.getcwd()
        os.chdir(ROOT)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(io.StringIO()):
                code = run(["--config", os.path.join(CONFIGS, "test.csv"),
                            "--mode", "dot", "--output", path])
        finally:
            os.chdir(cwd)
        self.assertEqual(code, 0)
        with open(path) as f:
            self.assertEqual(f.read(), out.getvalue())

    def test_run_bad_output_no_graph(self):
        """Ошибка вывода обнаруживается до построения графа."""
        out, err = io.StringIO(), io.StringIO()
        cwd = os.getcwd()
        os.chdir(ROOT)
        try:
            with contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(err):
                code = run(["--config", os.path.join(CONFIGS, "test.csv"),
                            "--output", "g.jpg"])
        finally:
            os.chdir(cwd)
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("unsupported format", err.getvalue())

    @mock.patch.object(viz.subprocess, "run")
    def test_show_saved_image(self, run_cmd):
        """--show открывает сохранённую картинку системным просмотрщиком."""
        with contextlib.redirect_stderr(io.StringIO()):
            viz.show("digraph {}", "g.svg")
        self.assertEqual(run_cmd.call_args[0][0][-1], "g.svg")

    @mock.patch.object(viz.subprocess, "run")
    def test_show_viewer_error(self, run_cmd):
        """Ошибка просмотрщика превращается в RenderError."""
        run_cmd.side_effect = OSError("no viewer")
        with self.assertRaises(RenderError):
            viz.show("digraph {}", "g.svg")


if __name__ == "__main__":
    unittest.main()
