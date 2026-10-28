# pip-dependency-graph

Вариант 5

Инструмент визуализации графа зависимостей pip-пакетов.

Этап 1: минимальное CLI-приложение, параметры читаются из CSV-конфига.

Этап 2: получение прямых зависимостей заданной версии пакета из
репозитория PyPI (JSON API `{repo}/{name}/{version}/json`, поле
`requires_dist`). Менеджеры пакетов и сторонние библиотеки не используются.

## Запуск

```bash
./run.sh                            # конфиг config.csv
./run.sh --config configs/test.csv
```

## Параметры командной строки

| Параметр | Описание |
|---|---|
| `--config PATH` | Путь к CSV-конфигу (по умолчанию `config.csv`) |

## Конфигурация (CSV)

```csv
key,value
package_name,requests
repo,https://pypi.org/pypi
test_repo_mode,false
version,2.31.0
max_depth,3
```

| Ключ | Описание |
|---|---|
| `package_name` | Имя пакета (PEP 508) |
| `repo` | URL репозитория или путь к файлу тестового репозитория |
| `test_repo_mode` | Режим тестового репозитория: `true` / `false` |
| `version` | Версия пакета (PEP 440) |
| `max_depth` | Максимальная глубина анализа, `>= 1` |

При запуске выводятся прямые зависимости пакета:

```
$ ./run.sh --config configs/pypi.csv
requests==2.31.0:
  charset-normalizer
  idna
  urllib3
  certifi
```

Имена нормализуются по PEP 503. Зависимости, подключаемые только через
extras (`; extra == "..."`), пропускаются. Режим тестового репозитория
на этом этапе ещё не поддерживается.

При ошибке (конфиг, HTTP 404, нет сети) печатается `error: ...`,
код выхода `1`.

## Модули

`main.py`

- `parse_args()` — `--config`
- `print_direct_deps()` — вывод прямых зависимостей
- `run()` — точка входа

`config.py`

- `read_csv()` — чтение CSV
- `parse_*()` — проверка параметров
- `load_config()` — загрузка конфига

`pypi.py`

- `PypiRepo.get_deps()` — прямые зависимости пакета (версии)
- `parse_requires_dist()` — разбор `requires_dist`
- `fetch_json()` — загрузка JSON через `urllib`

## Тестовые скрипты

```bash
./scripts/stage1_config.sh
./scripts/stage1_errors.sh
./scripts/stage1_all.sh
./scripts/stage2_deps.sh    # прямые зависимости (нужна сеть)
./scripts/run_tests.sh      # unittest из tests/
```

## Структура

```
pip-dependency-graph/
├── src/          # main.py, config.py, pypi.py
├── tests/        # unittest
├── configs/      # конфиги, configs/errors/ — с ошибками
├── test_repos/   # тестовые репозитории
├── scripts/      # bash-обёртки для прогона тестов
├── config.csv
├── run.sh
└── README.md
```
