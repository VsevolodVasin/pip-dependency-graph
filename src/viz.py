"""Визуализация графа: описание на языке Graphviz DOT и рендер в картинку."""

import os
import shutil
import subprocess
import sys
import tempfile


class RenderError(Exception):
    """Ошибка сохранения или рендера изображения графа."""


IMAGE_FORMATS = ("png", "svg", "pdf")
VIEWERS = {"darwin": ["open"], "win32": ["cmd", "/c", "start", ""]}
DEFAULT_VIEWER = ["xdg-open"]


def quote(name):
    """Экранирует строку для DOT, перевод строки становится \\n."""
    text = name.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + text.replace("\n", "\\n") + '"'


def edge_attrs(graph, name, dep, in_cycle):
    """Атрибуты ребра name -> dep: подпись с ограничениями и цвет цикла."""
    attrs = []
    spec = graph.specs.get(name, {}).get(dep)
    if spec:
        attrs.append(f"label={quote(spec)}")
    if (name, dep) in in_cycle:
        attrs.append("color=red")
    return f" [{', '.join(attrs)}]" if attrs else ""


def cycle_edges(graph):
    """Множество рёбер (a, b), входящих в найденные циклы."""
    edges = set()
    for cycle in graph.cycles:
        edges.update(zip(cycle, cycle[1:]))
    return edges


def to_dot(graph, reverse=False):
    """Возвращает описание графа на языке DOT.

    Под именем пакета подписана его версия, на ребре — ограничения
    версии зависимости с условиями (маркерами окружения). Корень выделен
    заливкой, узлы на максимальной глубине — пунктиром, рёбра циклов —
    красным. Для графа обратных зависимостей рёбра разворачиваются, чтобы
    стрелка всегда шла от пакета к зависимости.
    """
    in_cycle = cycle_edges(graph)
    lines = [
        "digraph dependencies {",
        "    rankdir=LR;",
        '    node [shape=box, style=rounded, fontname="Helvetica"];',
        '    edge [fontname="Helvetica", fontsize=10];',
    ]
    for name in graph.nodes():
        attrs = []
        version = graph.versions.get(name)
        if version:
            attrs.append(f"label={quote(name + chr(10) + version)}")
        if name == graph.root:
            attrs.append('style="rounded,filled", fillcolor="#cfe3ff"')
        elif name in graph.cut:
            attrs.append('style="rounded,dashed", xlabel="max depth"')
        suffix = f" [{', '.join(attrs)}]" if attrs else ""
        lines.append(f"    {quote(name)}{suffix};")
    for name, deps in graph.edges.items():
        for dep in deps:
            a, b = (dep, name) if reverse else (name, dep)
            lines.append(f"    {quote(a)} -> {quote(b)}"
                         f"{edge_attrs(graph, name, dep, in_cycle)};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def check_output(path):
    """Проверяет файл вывода до построения графа и возвращает формат."""
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    if ext != "dot" and ext not in IMAGE_FORMATS:
        raise RenderError(
            f"output: unsupported format {ext!r}, "
            f"expected dot, {', '.join(IMAGE_FORMATS)}"
        )
    folder = os.path.dirname(path) or "."
    if not os.path.isdir(folder):
        raise RenderError(f"output: directory not found: {folder}")
    if ext != "dot" and shutil.which("dot") is None:
        raise RenderError("Graphviz 'dot' not found, install graphviz")
    return ext


def save(dot_text, path):
    """Сохраняет граф: .dot — как текст, .png/.svg/.pdf — через Graphviz."""
    ext = check_output(path)
    if ext == "dot":
        write_text(path, dot_text)
        return
    try:
        subprocess.run(
            ["dot", f"-T{ext}", "-o", path],
            input=dot_text, text=True, check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        raise RenderError(f"dot failed: {e.stderr.strip()}")


def write_text(path, text):
    """Записывает текст в файл, ошибки ОС превращает в RenderError."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    except OSError as e:
        raise RenderError(f"output: {e}")


def show(dot_text, path=None):
    """Показывает изображение графа в системном просмотрщике.

    Если path — уже сохранённая картинка, открывается она, иначе граф
    рендерится во временный PNG.
    """
    if path is None or path.lower().endswith(".dot"):
        fd, path = tempfile.mkstemp(suffix=".png", prefix="graph-")
        os.close(fd)
        save(dot_text, path)
    viewer = VIEWERS.get(sys.platform, DEFAULT_VIEWER)
    try:
        subprocess.run(viewer + [path], check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError) as e:
        raise RenderError(f"cannot open image viewer: {e}")
    print(f"shown: {path}", file=sys.stderr)
