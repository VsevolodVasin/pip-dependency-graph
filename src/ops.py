"""Дополнительные операции над графом: обратные зависимости пакета."""

from graph import build_graph
from pypi import RepoError


def invert(packages):
    """Обратный индекс: пакет -> пакеты, которые от него зависят."""
    dependents = {name: [] for name in packages}
    for name, deps in packages.items():
        for dep in deps:
            if name not in dependents.setdefault(dep, []):
                dependents[dep].append(name)
    return dependents


def invert_specs(specs):
    """Ограничения по рёбрам в обратную сторону: specs[dep][name]."""
    result = {}
    for name, deps in specs.items():
        for dep, spec in deps.items():
            result.setdefault(dep, {})[name] = spec
    return result


class ReverseRepo:
    """Репозиторий с развёрнутыми рёбрами: get_deps возвращает зависящих.

    packages — словарь пакет -> прямые зависимости. Версии пакетов и
    ограничения на рёбрах (если известны) переносятся для картинки.
    """

    def __init__(self, packages, versions=None, specs=None, where="graph"):
        """Строит обратный индекс по словарю прямых зависимостей."""
        self.packages = packages
        self.dependents = invert(packages)
        self.versions = dict(versions or {})
        self.specs = invert_specs(specs or {})
        self.where = where

    def get_deps(self, name, version=None):
        """Возвращает пакеты, напрямую зависящие от name."""
        if name not in self.dependents:
            raise RepoError(f"package {name} not found in {self.where}")
        return list(self.dependents[name])


def reverse_repo(repo, root, version, max_depth):
    """Обратный репозиторий для тестового репозитория или PyPI.

    Тестовый репозиторий известен целиком, поэтому зависящие пакеты
    ищутся среди всех его пакетов. PyPI не даёт списка пакетов, которые
    зависят от данного, поэтому сначала тем же DFS из этапа 3 строится
    граф зависимостей root, и зависящие пакеты ищутся в нём.
    """
    packages = getattr(repo, "packages", None)
    if packages is not None:
        return ReverseRepo(packages, where="test repository")
    forward = build_graph(repo, root, version, max_depth)
    packages = {name: forward.edges.get(name, [])
                for name in forward.nodes()}
    return ReverseRepo(packages, forward.versions, forward.specs,
                       where=f"dependency graph of {root}")


def reverse_graph(repo, name, max_depth):
    """Граф обратных зависимостей: кто (транзитивно) зависит от name.

    Обход тот же DFS из graph.py, что и для прямых зависимостей, но по
    развёрнутым рёбрам; max_depth ограничивает длину обратного пути.
    """
    if not isinstance(repo, ReverseRepo):
        repo = ReverseRepo(repo.packages, where="test repository")
    return build_graph(repo, name, None, max_depth)
