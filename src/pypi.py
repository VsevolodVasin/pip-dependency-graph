"""Получение зависимостей пакета из PyPI JSON API без сторонних библиотек."""

import json
import re
import urllib.error
import urllib.request

TIMEOUT = 15

REQ_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
EXTRA_RE = re.compile(r"\bextra\s*==")


class RepoError(Exception):
    """Ошибка получения данных из репозитория."""


def normalize(name):
    """Приводит имя пакета к каноническому виду (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirement(req):
    """Возвращает имя пакета из строки requires_dist или None.

    Зависимости, включаемые только через extras (маркер extra == ...),
    пропускаются: при обычной установке они не ставятся.
    """
    spec, _, marker = req.partition(";")
    if EXTRA_RE.search(marker):
        return None
    m = REQ_NAME_RE.match(spec)
    if not m:
        raise RepoError(f"cannot parse requirement {req!r}")
    return normalize(m.group(1))


def parse_requires_dist(requires):
    """Возвращает список имён прямых зависимостей без повторов."""
    names = []
    for req in requires or []:
        name = parse_requirement(req)
        if name and name not in names:
            names.append(name)
    return names


def metadata_url(base, name, version=None):
    """Формирует URL JSON-метаданных пакета (конкретной версии)."""
    base = base.rstrip("/")
    if version is None:
        return f"{base}/{name}/json"
    return f"{base}/{name}/{version}/json"


def fetch_json(url):
    """Скачивает и разбирает JSON по URL."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        raise RepoError(f"{url}: HTTP {e.code}")
    except urllib.error.URLError as e:
        raise RepoError(f"{url}: {e.reason}")
    except ValueError:
        raise RepoError(f"{url}: invalid JSON")


class PypiRepo:
    """Репозиторий PyPI, доступный по URL (например https://pypi.org/pypi)."""

    def __init__(self, base_url):
        """Запоминает базовый URL репозитория."""
        self.base_url = base_url

    def get_deps(self, name, version=None):
        """Возвращает прямые зависимости пакета заданной версии.

        Если версия не указана, берётся последняя версия пакета.
        """
        data = fetch_json(metadata_url(self.base_url, name, version))
        info = data.get("info") or {}
        return parse_requires_dist(info.get("requires_dist"))
