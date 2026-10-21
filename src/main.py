import argparse
import sys

from config import ConfigError, load_config


def parse_args():
    p = argparse.ArgumentParser(description="Визуализатор графа зависимостей pip-пакетов")
    p.add_argument("--config", default="config.csv", help="путь к CSV-конфигу")
    return p.parse_args()


def print_config(cfg):
    for key, value in cfg.items():
        if isinstance(value, bool):
            value = str(value).lower()
        print(f"{key}={value}")


def run():
    args = parse_args()
    try:
        cfg = load_config(args.config)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print_config(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(run())
