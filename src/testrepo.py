"""Тестовый репозиторий: граф пакетов, описанный в текстовом файле.

Формат файла — по строке на пакет, имена из больших латинских букв:

    A: B C
    B: D
    D:

Пустые строки и строки, начинающиеся с #, пропускаются.
"""

import re

from pypi import RepoError

NAME_RE = re.compile(r"^[A-Z]+$")


def check_name(name, lineno):
    """Проверяет, что имя состоит из больших латинских букв."""
    if not NAME_RE.match(name):
        raise RepoError(f"line {lineno}: invalid package name {name!r}")
    return name


def parse_line(line, lineno):
    """Разбирает строку 'A: B C' в пару (имя, список зависимостей)."""
    name, sep, deps = line.partition(":")
    if not sep:
        raise RepoError(f"line {lineno}: expected 'NAME: DEPS'")
    name = check_name(name.strip(), lineno)
    return name, [check_name(d, lineno) for d in deps.split()]


def parse_test_repo(text):
    """Разбирает текст тестового репозитория в словарь имя -> зависимости."""
    packages = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, deps = parse_line(line, lineno)
        if name in packages:
            raise RepoError(f"line {lineno}: duplicate package {name}")
        packages[name] = deps
    return packages


class FileRepo:
    """Репозиторий, загруженный из файла; версии пакетов не учитываются."""

    def __init__(self, path):
        """Читает и разбирает файл тестового репозитория."""
        with open(path, encoding="utf-8") as f:
            self.packages = parse_test_repo(f.read())

    def get_deps(self, name, version=None):
        """Возвращает прямые зависимости пакета."""
        if name not in self.packages:
            raise RepoError(f"package {name} not found in test repository")
        return list(self.packages[name])
