"""Построение графа зависимостей рекурсивным обходом в глубину (DFS)."""


class DependencyGraph:
    """Результат обхода: рёбра, найденные циклы и обрезанные узлы."""

    def __init__(self, root):
        """Создаёт пустой граф с корнем root."""
        self.root = root
        self.edges = {}
        self.cut = set()
        self.cycles = []
        self.versions = {}
        self.specs = {}

    def nodes(self):
        """Все узлы графа в порядке обхода."""
        result = list(self.edges)
        for deps in self.edges.values():
            result += [d for d in deps if d not in result]
        return result


def canonical_cycle(cycle):
    """Поворачивает цикл так, чтобы он начинался с наименьшего узла."""
    body = cycle[:-1]
    i = body.index(min(body))
    body = body[i:] + body[:i]
    return body + [body[0]]


class GraphBuilder:
    """Обходит репозиторий в глубину с ограничением глубины.

    Корень берётся в заданной версии, остальные пакеты — в последней.
    Узел на глубине max_depth не раскрывается. Повторно узел раскрывается,
    только если до него нашёлся более короткий путь. Ребро в узел из
    текущего пути означает цикл: он записывается, обход по нему не идёт.
    """

    def __init__(self, repo, root, version, max_depth):
        """Запоминает параметры обхода."""
        self.repo = repo
        self.version = version
        self.max_depth = max_depth
        self.graph = DependencyGraph(root)
        self.depth = {}
        self.cache = {}

    def build(self):
        """Строит граф от корня и возвращает DependencyGraph.

        Версии пакетов и ограничения зависимостей копируются из
        репозитория, если он их знает (PyPI), для подписей на картинке.
        """
        self._dfs(self.graph.root, 0, [])
        self.graph.versions = dict(getattr(self.repo, "versions", {}))
        self.graph.specs = dict(getattr(self.repo, "specs", {}))
        return self.graph

    def _deps(self, name):
        """Прямые зависимости пакета, каждый пакет запрашивается один раз."""
        if name not in self.cache:
            version = self.version if name == self.graph.root else None
            self.cache[name] = self.repo.get_deps(name, version)
        return self.cache[name]

    def _dfs(self, name, depth, path):
        """Рекурсивно раскрывает узел name, находящийся на глубине depth."""
        self.depth[name] = depth
        if depth >= self.max_depth:
            self.graph.cut.add(name)
            return
        self.graph.cut.discard(name)
        path.append(name)
        deps = self._deps(name)
        self.graph.edges[name] = deps
        for dep in deps:
            self._visit(dep, depth + 1, path)
        path.pop()

    def _visit(self, dep, depth, path):
        """Обрабатывает ребро в dep: цикл, уже пройденный узел или спуск."""
        if dep in path:
            cycle = canonical_cycle(path[path.index(dep):] + [dep])
            if cycle not in self.graph.cycles:
                self.graph.cycles.append(cycle)
            return
        if self.depth.get(dep, depth + 1) <= depth:
            return
        self._dfs(dep, depth, path)


def build_graph(repo, root, version, max_depth):
    """Строит граф зависимостей пакета root заданной версии."""
    return GraphBuilder(repo, root, version, max_depth).build()


def format_graph(graph, arrow="->"):
    """Возвращает текстовое представление графа списком строк.

    arrow — разделитель узла и его соседей: "->" для зависимостей,
    "<-" для обратных зависимостей.
    """
    lines = []
    for name in graph.nodes():
        if name in graph.cut:
            lines.append(f"{name} (max depth)")
        elif graph.edges.get(name):
            lines.append(f"{name} {arrow} {', '.join(graph.edges[name])}")
        else:
            lines.append(name)
    for cycle in graph.cycles:
        lines.append("cycle: " + f" {arrow} ".join(cycle))
    return lines
