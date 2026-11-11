#!/usr/bin/env bash
# Этап 4: обратные зависимости на тестовых репозиториях и на PyPI.
cd "$(dirname "$0")/.."
for f in configs/test_reverse.csv configs/test_reverse_complex.csv \
         configs/test_reverse_depth.csv configs/test_reverse_cycle.csv; do
    echo "\$ ./run.sh --config $f --mode reverse"
    ./run.sh --config "$f" --mode reverse
    echo
done
for args in "configs/flask.csv markupsafe" "configs/flask.csv zipp" \
            "configs/pypi.csv urllib3" "configs/flask.csv nope"; do
    set -- $args
    echo "\$ ./run.sh --config $1 --mode reverse --target $2"
    ./run.sh --config "$1" --mode reverse --target "$2"
    echo
done
