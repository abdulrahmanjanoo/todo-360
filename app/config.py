"""Paths. The vault is the data source; this project only keeps Abdul's decisions."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.environ.get("TODO360_DATA") or os.path.join(ROOT, "_data")  # tests point this at a temp folder
DEFAULT_VAULT = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/Obsidian Notes")


def settings():
    try:
        with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def vault_path():
    """TODO360_VAULT env wins, then config.json, then the iCloud default."""
    p = os.environ.get("TODO360_VAULT") or settings().get("vault") or DEFAULT_VAULT
    return os.path.expanduser(p)


def vault_name():
    return settings().get("vault_name") or os.path.basename(os.path.normpath(vault_path()))


def port():
    return int(os.environ.get("TODO360_PORT") or settings().get("port") or 8360)


def owner_me():
    return settings().get("me") or "Abdul Rahman Janoo"
