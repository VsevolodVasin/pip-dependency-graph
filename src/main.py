"""Точка входа визуализатора графа зависимостей pip-пакетов."""

import argparse
import sys

from config import ConfigError, load_config
from graph import build_graph, format_graph
from pypi import PypiRepo, RepoError
from testrepo import FileRepo


def parse_args(argv=None):
    """Разбирает аргументы командной строки."""
    p = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей pip-пакетов"
    )
    p.add_argument(
        "--config", default="config.csv", help="путь к CSV-конфигу"
    )
    return p.parse_args(argv)


def make_repo(cfg):
    """Создаёт тестовый или PyPI-репозиторий по настройкам."""
    if cfg["test_repo_mode"]:
        return FileRepo(cfg["repo"])
    return PypiRepo(cfg["repo"])


def print_graph(cfg):
    """Строит граф зависимостей и печатает его."""
    graph = build_graph(
        make_repo(cfg), cfg["package_name"], cfg["version"],
        cfg["max_depth"],
    )
    for line in format_graph(graph):
        print(line)


def run(argv=None):
    """Загружает конфиг и печатает граф зависимостей, при ошибке — 1."""
    args = parse_args(argv)
    try:
        cfg = load_config(args.config)
        print_graph(cfg)
    except (ConfigError, RepoError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run())
