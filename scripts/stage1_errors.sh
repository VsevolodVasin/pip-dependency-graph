#!/usr/bin/env bash
cd "$(dirname "$0")/.."
for f in configs/nope.csv configs/errors/*.csv; do
    echo "\$ ./run.sh --config $f"
    ./run.sh --config "$f"
    echo
done
