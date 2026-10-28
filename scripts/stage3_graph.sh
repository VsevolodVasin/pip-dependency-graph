#!/usr/bin/env bash
cd "$(dirname "$0")/.."
for f in configs/test.csv configs/test_cycle.csv configs/test_self.csv \
         configs/test_depth.csv configs/test_complex.csv \
         configs/errors/test_*.csv; do
    echo "\$ ./run.sh --config $f"
    ./run.sh --config "$f"
    echo
done
