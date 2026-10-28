"""Точка входа визуализатора графа зависимостей pip-пакетов."""

import argparse
import sys

from config import ConfigError, load_config
from pypi import PypiRepo, RepoError


def parse_args(argv=None):
    """Разбирает аргументы командной строки."""
    p = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей pip-пакетов"
    )
    p.add_argument(
        "--config", default="config.csv", help="путь к CSV-конфигу"
    )
    return p.parse_args(argv)


def print_direct_deps(cfg):
    """Печатает прямые зависимости пакета заданной версии."""
    if cfg["test_repo_mode"]:
        raise RepoError("test repository mode is not supported yet")
    repo = PypiRepo(cfg["repo"])
    deps = repo.get_deps(cfg["package_name"], cfg["version"])
    print(f"{cfg['package_name']}=={cfg['version']}:")
    for name in deps:
        print(f"  {name}")
    if not deps:
        print("  (no dependencies)")


def run(argv=None):
    """Загружает конфиг и печатает прямые зависимости, при ошибке — 1."""
    args = parse_args(argv)
    try:
        cfg = load_config(args.config)
        print_direct_deps(cfg)
    except (ConfigError, RepoError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run())
