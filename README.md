# pip-dependency-graph

Вариант 5

Инструмент визуализации графа зависимостей pip-пакетов.

Этап 1: минимальное CLI-приложение, параметры читаются из CSV-конфига.

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

При запуске все параметры выводятся в формате `ключ=значение`.
При ошибке печатается `error: ...`, код выхода `1`.

## Модули

`main.py`

- `parse_args()` — `--config`
- `print_config()` — вывод параметров
- `run()` — точка входа

`config.py`

- `read_csv()` — чтение CSV
- `parse_*()` — проверка параметров
- `load_config()` — загрузка конфига

## Тестовые скрипты

```bash
./scripts/stage1_config.sh
./scripts/stage1_errors.sh
./scripts/stage1_all.sh
```

## Структура

```
pip-dependency-graph/
├── src/          # main.py, config.py
├── configs/      # конфиги, configs/errors/ — с ошибками
├── test_repos/   # тестовые репозитории
├── scripts/      # bash-обёртки для прогона тестов
├── config.csv
├── run.sh
└── README.md
```
