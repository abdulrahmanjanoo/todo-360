"""Abdul's decisions, kept in this project, applied to the vault only on request.

Store: _data/decisions.json
  todos:    {T-id: {action: done|snooze|not_mine|keep, until?, note?, at, applied?}}
  meetings: {meeting-id: {confirmed: happened|did_not_happen, note?, at}}
  money:    {T-id or meeting-id: {verdict: yes|no, at}}   Abdul's override of the #revenue tag

Applying a `done`:
  1. tick `- [ ] T-xxxx` -> `- [x] T-xxxx` wherever the vault shows that todo, then
  2. run the engine's `wiki.py sync`, which closes ticked todos as "manual" (Abdul's tick wins).
  A todo with no tickable line falls back to `wiki.py close --tier high`.
The engine stays the only writer of todos.json, the log and git commits.
"""
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
import threading

from config import DATA, vault_path

PATH = os.path.join(DATA, "decisions.json")
_lock = threading.Lock()
TODO_ACTIONS = {"done", "snooze", "not_mine", "keep", "clear"}
MEETING_ACTIONS = {"happened", "did_not_happen", "clear"}
MONEY_ACTIONS = {"yes", "no", "clear"}


def load():
    try:
        with open(PATH, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    d.setdefault("todos", {})
    d.setdefault("meetings", {})
    d.setdefault("money", {})
    return d


def save(d):
    os.makedirs(DATA, exist_ok=True)
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, PATH)


def now():
    return dt.datetime.now().isoformat(timespec="seconds")


def record(kind, item_id, action, until=None, note=None):
    if not re.match(r"^[A-Za-z0-9:_.\-]{1,80}$", item_id or ""):
        raise ValueError("bad id")
    with _lock:
        d = load()
        if kind == "todo":
            if action not in TODO_ACTIONS:
                raise ValueError("bad action")
            if action == "clear":
                d["todos"].pop(item_id, None)
            else:
                entry = {"action": action, "at": now()}
                if action == "snooze":
                    entry["until"] = until or (dt.date.today() + dt.timedelta(days=7)).isoformat()
                if note:
                    entry["note"] = note[:500]
                d["todos"][item_id] = entry
        elif kind == "meeting":
            if action not in MEETING_ACTIONS:
                raise ValueError("bad action")
            if action == "clear":
                d["meetings"].pop(item_id, None)
            else:
                d["meetings"][item_id] = {"confirmed": action, "at": now(), **({"note": note[:500]} if note else {})}
        elif kind == "money":
            if action not in MONEY_ACTIONS:
                raise ValueError("bad action")
            if action == "clear":
                d["money"].pop(item_id, None)
            else:
                d["money"][item_id] = {"verdict": action, "at": now()}
        else:
            raise ValueError("bad kind")
        save(d)
        return d


def _tick(vault, tid):
    """Tick every open checkbox line for this T-id. Returns files changed."""
    pat = re.compile(r"^(\s*- )\[ \]( %s\b)" % re.escape(tid), re.M)
    changed = []
    roots = ["m", "p", "Area", "Read AI Transcribe Notes"]
    for r in roots:
        for path in glob.glob(os.path.join(vault, r, "**", "*.md"), recursive=True):
            if "/Raw/" in path:
                continue  # raw transcripts are never edited
            try:
                text = open(path, encoding="utf-8").read()
            except OSError:
                continue
            new, n = pat.subn(r"\1[x]\2", text)
            if n:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
                changed.append(os.path.relpath(path, vault))
    return changed


def _engine(vault, *args):
    eng = os.path.join(vault, ".llm-wiki", "engine", "wiki.py")
    r = subprocess.run([sys.executable, eng, "--vault", vault, *args], capture_output=True, text=True, timeout=170)
    return (r.stdout + r.stderr).strip()


def apply(dry_run=False):
    """Push pending `done` decisions into the vault through the engine."""
    vault = vault_path()
    out = []
    with _lock:
        d = load()
        todos = {t["id"]: t for t in json.load(open(os.path.join(vault, "Wiki", ".state", "todos.json"), encoding="utf-8"))["todos"]}
        pending = [tid for tid, e in d["todos"].items() if e.get("action") == "done" and not e.get("applied")]
        if not pending:
            return {"applied": [], "log": ["Nothing to apply."]}
        fallback, ticked = [], []
        for tid in pending:
            t = todos.get(tid)
            if not t:
                out.append("%s: not in todos.json, skipped" % tid)
                continue
            if t.get("status") != "open":
                out.append("%s: already %s in the vault" % (tid, t.get("status")))
                d["todos"][tid]["applied"] = now()
                continue
            if dry_run:
                out.append("%s: would close" % tid)
                continue
            files = _tick(vault, tid)
            if files:
                ticked.append(tid)
                out.append("%s: ticked in %s" % (tid, ", ".join(files[:3])))
            else:
                fallback.append(tid)
        if dry_run:
            return {"applied": [], "log": out}
        if ticked:
            out.append(_engine(vault, "sync"))
        for tid in fallback:
            out.append(_engine(vault, "close", tid, "--tier", "high",
                               "--source", "Abdul in To-Do 360, %s" % dt.date.today().isoformat(),
                               "--reason", "Marked done by Abdul"))
        after = {t["id"]: t for t in json.load(open(os.path.join(vault, "Wiki", ".state", "todos.json"), encoding="utf-8"))["todos"]}
        applied = []
        for tid in pending:
            if after.get(tid, {}).get("status") != "open":
                d["todos"][tid]["applied"] = now()
                applied.append(tid)
        save(d)
    return {"applied": applied, "log": [l for l in out if l]}


if __name__ == "__main__":
    print(json.dumps(apply(dry_run="--dry-run" in sys.argv), indent=1))
