#!/usr/bin/env bash
cd "$(dirname "$0")/.."
for f in config.csv configs/pypi.csv configs/test.csv; do
    echo "\$ ./run.sh --config $f"
    ./run.sh --config "$f"
    echo
done
