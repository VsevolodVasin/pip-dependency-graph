# pip-dependency-graph

Вариант 5

Инструмент визуализации графа зависимостей pip-пакетов.

Этап 1: минимальное CLI-приложение, параметры читаются из CSV-конфига.

Этап 2: получение прямых зависимостей заданной версии пакета из
репозитория PyPI (JSON API `{repo}/{name}/{version}/json`, поле
`requires_dist`). Менеджеры пакетов и сторонние библиотеки не используются.

Этап 3: построение графа зависимостей с учётом транзитивности —
рекурсивный обход в глубину (DFS) с ограничением `max_depth`, обработкой
циклов и режимом тестового репозитория.

Этап 4: дополнительные операции — обратные зависимости пакета
(`--mode reverse`).

Этап 5: визуализация — описание графа на языке Graphviz DOT
(`--mode dot`), сохранение изображения (`--output graph.svg`) и показ
его на экране (`--show`).

## Запуск

```bash
./run.sh                            # конфиг config.csv
./run.sh --config configs/test.csv
./run.sh --config configs/test_reverse.csv --mode reverse
./run.sh --config configs/flask.csv --mode reverse --target markupsafe
./run.sh --config configs/flask.csv --output images/flask.svg
```

## Параметры командной строки

| Параметр | Описание |
|---|---|
| `--config PATH` | Путь к CSV-конфигу (по умолчанию `config.csv`) |
| `--mode MODE` | `graph` (по умолчанию), `reverse`, `dot` |
| `--target NAME` | Пакет, для которого ищутся обратные зависимости (по умолчанию `package_name`) |
| `--output FILE` | Сохранить граф: `.dot` — текстом, `.png`/`.svg`/`.pdf` — через Graphviz |
| `--show` | Открыть изображение графа в системном просмотрщике |

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

При запуске выводится граф зависимостей: для каждого раскрытого пакета —
строка `пакет -> зависимости`, лист печатается одним именем, узел на
максимальной глубине помечается `(max depth)`, найденные циклы — строками
`cycle: ...`.

```
$ ./run.sh --config configs/test_complex.csv
A -> B, C
B -> D, E
D -> B
E -> G
G
C -> E, F
F -> C, G
cycle: B -> D -> B
cycle: C -> F -> C
```

### Алгоритм

- Корневой пакет берётся в версии `version`, его зависимости — в
  последней версии из репозитория (`{repo}/{name}/json`).
- Обход — рекурсивный DFS. Корень на глубине 0, пакеты на глубине
  `max_depth` не раскрываются (`max_depth=1` — только прямые зависимости).
- Каждый пакет запрашивается из репозитория один раз. Уже пройденный узел
  раскрывается повторно, только если до него найден более короткий путь.
- Ребро в пакет из текущего пути DFS — цикл: он записывается, обход по
  нему не продолжается.
- Имена PyPI нормализуются по PEP 503, зависимости через extras
  (`; extra == "..."`) пропускаются.

### Тестовый репозиторий

При `test_repo_mode=true` параметр `repo` — путь к файлу, где пакеты
названы большими латинскими буквами, версии не учитываются:

```
# комментарий
A: B C
B: D
C: D
D:
```

Каждый пакет, упомянутый как зависимость, должен быть описан в файле.

| Файл | Случай |
|---|---|
| `basic.txt` | ромб: общая зависимость |
| `cycle.txt` | цикл A → B → C → A |
| `self.txt` | пакет зависит от себя |
| `chain.txt` | цепочка, обрезка по `max_depth=2` |
| `complex.txt` | два цикла и общие узлы |
| `bad_*.txt`, `missing.txt` | ошибки формата и неописанный пакет |

При ошибке (конфиг, HTTP 404, нет сети) печатается `error: ...`,
код выхода `1`. Обрывы соединения с PyPI повторяются до трёх раз.

## Этап 4: дополнительные операции

### Обратные зависимости (`--mode reverse`)

Для пакета `package_name` выводятся пакеты репозитория, которые от него
зависят, напрямую или транзитивно. Используется тот же DFS, что и для
прямых зависимостей, но по развёрнутым рёбрам: `max_depth` ограничивает
длину обратного пути, циклы находятся так же.

```
$ ./run.sh --config configs/test_reverse_complex.csv --mode reverse
G <- E, F
E <- B, C
B <- A, D
A
D <- B
C <- A, F
F <- C
cycle: B <- D <- B
cycle: C <- F <- C
```

Где ищутся зависящие пакеты:

- **Тестовый репозиторий** известен целиком, поэтому зависящие пакеты
  ищутся среди всех его пакетов; `--target` по умолчанию —
  `package_name`.
- **PyPI** не даёт списка пакетов, которые зависят от данного. Поэтому
  сначала тем же DFS из этапа 3 строится граф зависимостей
  `package_name` (в версии `version`, до `max_depth`), а затем по его
  развёрнутым рёбрам ищутся пакеты, зависящие от `--target`. Имя
  `--target` нормализуется по PEP 503 (`MarkupSafe` -> `markupsafe`).

```
$ ./run.sh --config configs/flask.csv --mode reverse --target markupsafe
markupsafe <- werkzeug, jinja2
werkzeug <- flask
flask
jinja2 <- flask

$ ./run.sh --config configs/flask.csv --mode reverse --target nope
error: package nope not found in dependency graph of flask
```

С `--output` или `--mode dot` обратный граф PyPI рисуется с теми же
версиями и ограничениями на рёбрах (`images/flask_reverse_markupsafe.svg`).

## Этап 5: визуализация

`--mode dot` печатает описание графа на языке Graphviz DOT. Под именем
пакета подписана его версия, на ребре — ограничения версии зависимости
с условием (маркером окружения), например
`>=3.6.0; python_version < '3.10'`. Версии известны только для PyPI: в
тестовом репозитории их нет, а пакеты на максимальной глубине не
запрашиваются. Корень залит цветом, узлы на максимальной глубине нарисованы пунктиром с подписью
`max depth`, рёбра циклов — красным. В графе обратных зависимостей
стрелка всё равно идёт от пакета к его зависимости.

```
$ ./run.sh --config configs/test.csv --mode dot
digraph dependencies {
    rankdir=LR;
    node [shape=box, style=rounded, fontname="Helvetica"];
    edge [fontname="Helvetica", fontsize=10];
    "A" [style="rounded,filled", fillcolor="#cfe3ff"];
    "B";
    "D";
    "C";
    "A" -> "B";
    "A" -> "C";
    "B" -> "D";
    "C" -> "D";
}
```

`--output FILE` работает в любом режиме: `.dot` сохраняется как текст,
`.png`, `.svg` и `.pdf` рендерятся программой `dot` из Graphviz
(`brew install graphviz`). Формат и каталог проверяются до построения
графа.

`--show` выводит изображение на экран: открывает сохранённую картинку
(или временный PNG, если `--output` не задан) в системном просмотрщике
(`open` на macOS, `xdg-open` на Linux, `start` на Windows).

```bash
./run.sh --config configs/flask.csv --show
```

Примеры в `images/`: `pypi.svg` (requests), `flask.svg`, `six.svg`,
`test_complex.svg`, `test_reverse_complex.svg`,
`flask_reverse_markupsafe.svg`.

### Сравнение со штатными инструментами

Штатный инструмент визуализации для pip — `pipdeptree`
(`pipdeptree -p flask --graph-output svg`). Для `flask 3.0.0` набор
пакетов в основном совпадает (werkzeug, jinja2, markupsafe, itsdangerous,
click, blinker), но есть расхождения:

- `pipdeptree` строит граф по установленным пакетам, а здесь граф
  строится по метаданным PyPI без установки.
- Маркеры окружения (`; python_version < "3.10"`) здесь не вычисляются,
  поэтому в граф попадает `importlib-metadata`, который pip на
  Python 3.10+ не ставит и `pipdeptree` не покажет.
- Зависимости берутся в последней версии, а pip выбирает версию под
  ограничения (`Werkzeug>=3.0.0`) и уже установленные пакеты; у другой
  версии может быть другой набор зависимостей.
- Под пакетом здесь подписана последняя версия с PyPI (у корня — версия
  из конфига), а `pipdeptree` показывает установленную; на рёбрах оба
  подписывают ограничения, но здесь к ним добавлено условие маркера.
- Глубина здесь ограничена `max_depth`, `pipdeptree` показывает всё
  дерево.

## Модули

`main.py`

- `parse_args()` — `--config`, `--mode`, `--target`, `--output`, `--show`
- `make_repo()` — выбор PyPI или тестового репозитория
- `reverse_target()` — пакет для режима `reverse`
- `make_graph()` — граф прямых или обратных зависимостей
- `output_lines()` — строки вывода для режима
- `execute()` — вывод, сохранение в файл и показ картинки
- `run()` — точка входа

`config.py`

- `read_csv()` — чтение CSV
- `parse_*()` — проверка параметров
- `load_config()` — загрузка конфига

`pypi.py`

- `PypiRepo.get_deps()` — прямые зависимости пакета (версии), запоминает
  версию пакета и ограничения зависимостей
- `parse_requires_dist()` — разбор `requires_dist`
- `parse_specs()` — ограничения версий и условия зависимостей
- `fetch_json()` — загрузка JSON через `urllib` с повтором при обрыве

`graph.py`

- `GraphBuilder` — рекурсивный DFS с ограничением глубины и поиском циклов
- `build_graph()` — построение `DependencyGraph`
- `format_graph()` — текстовый вывод

`ops.py`

- `ReverseRepo` — репозиторий с развёрнутыми рёбрами
- `reverse_repo()` — обратный репозиторий: весь тестовый или граф PyPI
- `reverse_graph()` — граф обратных зависимостей

`viz.py`

- `to_dot()` — описание графа на Graphviz DOT с версиями и ограничениями
- `check_output()` — проверка формата и каталога файла
- `save()` — сохранение `.dot` или рендер через `dot`
- `show()` — показ изображения в системном просмотрщике

`testrepo.py`

- `FileRepo.get_deps()` — зависимости из файла тестового репозитория
- `parse_test_repo()` — разбор файла

## Тестовые скрипты

```bash
./scripts/stage1_config.sh
./scripts/stage1_errors.sh
./scripts/stage1_all.sh
./scripts/stage2_deps.sh    # граф реальных пакетов (нужна сеть)
./scripts/stage3_graph.sh   # граф на тестовых репозиториях
./scripts/stage4_ops.sh     # обратные зависимости (PyPI — нужна сеть)
./scripts/stage5_viz.sh     # DOT и картинки в images/ (нужны сеть и Graphviz)
./scripts/run_tests.sh      # unittest из tests/
```

## Структура

```
pip-dependency-graph/
├── src/          # main.py, config.py, pypi.py, graph.py, testrepo.py,
│                 # ops.py, viz.py
├── tests/        # unittest
├── configs/      # конфиги, configs/errors/ — с ошибками
├── test_repos/   # тестовые репозитории
├── scripts/      # bash-обёртки для прогона тестов
├── images/       # картинки графов (этап 5)
├── config.csv
├── run.sh
└── README.md
```
