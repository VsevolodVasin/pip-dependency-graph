#!/usr/bin/env bash
cd "$(dirname "$0")/.."
for f in configs/pypi.csv configs/flask.csv configs/six.csv \
         configs/errors/no_version.csv configs/errors/bad_host.csv; do
    echo "\$ ./run.sh --config $f"
    ./run.sh --config "$f"
    echo
done
