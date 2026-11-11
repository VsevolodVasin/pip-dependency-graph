"""Точка входа визуализатора графа зависимостей pip-пакетов."""

import argparse
import sys

from config import ConfigError, load_config
from graph import build_graph, format_graph
from ops import reverse_graph, reverse_repo
from pypi import PypiRepo, RepoError, normalize
from testrepo import FileRepo
from viz import RenderError, check_output, save, show, to_dot

MODES = ("graph", "reverse", "dot")


def parse_args(argv=None):
    """Разбирает аргументы командной строки."""
    p = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей pip-пакетов"
    )
    p.add_argument(
        "--config", default="config.csv", help="путь к CSV-конфигу"
    )
    p.add_argument(
        "--mode", choices=MODES, default="graph",
        help="graph — граф зависимостей, reverse — обратные зависимости, "
             "dot — описание на Graphviz DOT",
    )
    p.add_argument(
        "--target", metavar="NAME",
        help="пакет, обратные зависимости которого ищутся в режиме "
             "reverse (по умолчанию package_name)",
    )
    p.add_argument(
        "--output", metavar="FILE",
        help="сохранить граф в FILE (.dot, .png, .svg, .pdf)",
    )
    p.add_argument(
        "--show", action="store_true",
        help="открыть изображение графа в системном просмотрщике",
    )
    return p.parse_args(argv)


def make_repo(cfg):
    """Создаёт тестовый или PyPI-репозиторий по настройкам."""
    if cfg["test_repo_mode"]:
        return FileRepo(cfg["repo"])
    return PypiRepo(cfg["repo"])


def reverse_target(cfg, target):
    """Имя пакета для режима reverse, по умолчанию package_name.

    Для PyPI имя --target нормализуется (PEP 503), как имена зависимостей.
    """
    if not target:
        return cfg["package_name"]
    return target if cfg["test_repo_mode"] else normalize(target)


def make_graph(cfg, reverse, target=None):
    """Строит граф прямых или обратных зависимостей пакета из конфига.

    В режиме reverse ищутся пакеты, зависящие от target: в тестовом
    репозитории — среди всех пакетов, в PyPI — в графе package_name.
    """
    repo = make_repo(cfg)
    if reverse:
        back = reverse_repo(repo, cfg["package_name"], cfg["version"],
                            cfg["max_depth"])
        return reverse_graph(back, reverse_target(cfg, target),
                             cfg["max_depth"])
    return build_graph(
        repo, cfg["package_name"], cfg["version"], cfg["max_depth"],
    )


def output_lines(graph, mode, reverse):
    """Строки вывода для выбранного режима."""
    if mode == "dot":
        return to_dot(graph, reverse).splitlines()
    return format_graph(graph, "<-" if reverse else "->")


def execute(cfg, args):
    """Строит граф, печатает его, сохраняет в файл и показывает картинку."""
    if args.output:
        check_output(args.output)
    reverse = args.mode == "reverse"
    graph = make_graph(cfg, reverse, args.target)
    for line in output_lines(graph, args.mode, reverse):
        print(line)
    if args.output:
        save(to_dot(graph, reverse), args.output)
        print(f"saved: {args.output}", file=sys.stderr)
    if args.show:
        show(to_dot(graph, reverse), args.output)


def run(argv=None):
    """Загружает конфиг и выполняет выбранный режим, при ошибке — 1."""
    args = parse_args(argv)
    try:
        cfg = load_config(args.config)
        execute(cfg, args)
    except (ConfigError, RepoError, RenderError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run())
