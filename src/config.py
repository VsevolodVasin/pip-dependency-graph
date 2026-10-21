"""Чтение и проверка CSV-конфигурации."""

import csv
import os
import re
from urllib.parse import urlparse


class ConfigError(Exception):
    """Ошибка конфигурации."""


KEYS = ("package_name", "repo", "test_repo_mode", "version", "max_depth")

NAME_RE = re.compile(
    r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.IGNORECASE
)
VERSION_RE = re.compile(
    r"^\d+(\.\d+)*((a|b|rc)\d+)?(\.post\d+)?(\.dev\d+)?$"
)


def read_csv(path):
    """Читает CSV вида key,value и возвращает словарь параметров."""
    if not os.path.isfile(path):
        raise ConfigError(f"config file not found: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.reader(f) if r]

    raw = {}
    for row in rows:
        key, value = row[0].strip(), ",".join(row[1:]).strip()
        if key == "key":
            continue
        if key not in KEYS:
            raise ConfigError(f"unknown key: {key}")
        raw[key] = value

    missing = [k for k in KEYS if k not in raw]
    if missing:
        raise ConfigError(f"missing keys: {', '.join(missing)}")
    return raw


def parse_package_name(value):
    """Проверяет имя пакета по PEP 508."""
    if not NAME_RE.match(value):
        raise ConfigError(f"package_name: invalid name {value!r}")
    return value


def parse_test_repo_mode(value):
    """Преобразует true/false в bool."""
    if value not in ("true", "false"):
        raise ConfigError(
            f"test_repo_mode: expected true/false, got {value!r}"
        )
    return value == "true"


def parse_repo(value, test_mode):
    """В тестовом режиме ждёт путь к файлу, иначе http(s) URL."""
    if test_mode:
        if not os.path.isfile(value):
            raise ConfigError(
                f"repo: test repository file not found: {value!r}"
            )
        return value
    url = urlparse(value)
    if url.scheme not in ("http", "https") or not url.netloc:
        raise ConfigError(f"repo: expected http(s) URL, got {value!r}")
    return value


def parse_version(value):
    """Проверяет версию по PEP 440 (1.2.3, 2.0rc1, 1.0.post1, 1.0.dev2)."""
    if not VERSION_RE.match(value):
        raise ConfigError(f"version: invalid version {value!r}")
    return value


def parse_max_depth(value):
    """Проверяет, что глубина — целое число >= 1."""
    try:
        depth = int(value)
    except ValueError:
        raise ConfigError(f"max_depth: expected integer, got {value!r}")
    if depth < 1:
        raise ConfigError(f"max_depth: must be >= 1, got {depth}")
    return depth


def load_config(path):
    """Загружает и проверяет все параметры конфига."""
    raw = read_csv(path)
    test_mode = parse_test_repo_mode(raw["test_repo_mode"])
    return {
        "package_name": parse_package_name(raw["package_name"]),
        "repo": parse_repo(raw["repo"], test_mode),
        "test_repo_mode": test_mode,
        "version": parse_version(raw["version"]),
        "max_depth": parse_max_depth(raw["max_depth"]),
    }
