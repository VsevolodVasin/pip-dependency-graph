#!/usr/bin/env bash
# Этап 5: описание графа на Graphviz DOT и картинки в images/.
cd "$(dirname "$0")/.."
mkdir -p images
echo "\$ ./run.sh --config configs/test_complex.csv --mode dot"
./run.sh --config configs/test_complex.csv --mode dot
echo
for name in pypi flask six test_complex; do
    echo "\$ ./run.sh --config configs/$name.csv --output images/$name.svg"
    ./run.sh --config "configs/$name.csv" --output "images/$name.svg"
    echo
done
echo "\$ ./run.sh --config configs/test_reverse_complex.csv --mode reverse --output images/test_reverse_complex.svg"
./run.sh --config configs/test_reverse_complex.csv --mode reverse \
    --output images/test_reverse_complex.svg
echo
echo "\$ ./run.sh --config configs/flask.csv --mode reverse --target markupsafe --output images/flask_reverse_markupsafe.svg"
./run.sh --config configs/flask.csv --mode reverse --target markupsafe \
    --output images/flask_reverse_markupsafe.svg
echo
echo "\$ ./run.sh --config configs/test_complex.csv --show"
./run.sh --config configs/test_complex.csv --show
echo
for out in images/graph.jpg nodir/graph.png; do
    echo "\$ ./run.sh --config configs/test.csv --output $out"
    ./run.sh --config configs/test.csv --output "$out"
    echo
done
