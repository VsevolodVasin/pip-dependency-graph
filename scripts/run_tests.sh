#!/usr/bin/env bash
cd "$(dirname "$0")/.."
PYTHONPATH=src exec python3 -m unittest discover -s tests -v
