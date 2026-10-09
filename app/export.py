"""Read Abdul's Obsidian vault and build one snapshot for the To-Do 360 UI.

Read-only. Nothing in the vault is written here. The engine (`.llm-wiki/engine/wiki.py`)
stays the only writer of vault state; decisions flow back through `decisions.py`.

Sources (all inside the vault):
  Wiki/.state/todos.json                       every todo with id, owner, tag, status, meeting
  Read AI Transcribe Notes/Processed - *.md    read views (frontmatter: meeting-id, airtable-record, ...)
  Read AI Transcribe Notes/Raw/Raw - *.md      raw transcripts (frontmatter: report-url, platform, start, ...)
  Read AI Transcribe Notes/log.md              skip / defer lines (capture failures)
  Wiki/.inbox/done/wispr-*.json                Wispr share links
  .lint/last_run.json                          lint findings (structure checks)
"""
import datetime as dt
import glob
import json
import os
import re

NOTES = "Read AI Transcribe Notes"
AIRTABLE_ROW = "https://airtable.com/app1H4gm8lva6gbbA/tbl7vuh1inQ2yGX5O/%s"
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
LOG_HEAD = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] (\w+) \| (.+)$")


def parse_ordinal(s):
    """'October 8th, 2026' -> date, or None."""
    m = re.match(r"\s*([A-Z][a-z]+) (\d{1,2})(?:st|nd|rd|th)?, (\d{4})", s or "")
    if not m or m.group(1) not in MONTHS:
        return None
    return dt.date(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))


def plain(text):
    """Wiki links to their display text: [[m/Tericsoft/Abdul Rahman Janoo|Abdul]] -> Abdul."""
    return LINK_RE.sub(lambda m: m.group(2) or m.group(1).split("/")[-1], text or "").strip()


def short_title(title):
    """'m/Tericsoft/Abdul Rahman Janoo' -> 'Abdul Rahman Janoo'; '' for none."""
    return (title or "").split("/")[-1]


def frontmatter(text):
    """Minimal YAML frontmatter reader: scalars and '- item' lists. Enough for these notes."""
    m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return {}, text
    fm, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^\s+- ", line) and key:
            if not isinstance(fm.get(key), list):
                fm[key] = []
            fm[key].append(line.split("- ", 1)[1].strip().strip('"'))
            continue
        km = re.match(r"^([\w-]+):\s*(.*)$", line)
        if km:
            key, val = km.group(1), km.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                fm[key] = [x.strip().strip('"') for x in val[1:-1].split(",") if x.strip()]
            else:
                fm[key] = val.strip('"') if val else ""
    return fm, text[m.end():]


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


class Vault:
    def __init__(self, root):
        self.root = root

    def p(self, *parts):
        return os.path.join(self.root, *parts)

    def rel(self, path):
        return os.path.relpath(path, self.root)


def load_raw(v):
    """meeting-id -> raw note info."""
    out = {}
    for path in glob.glob(v.p(NOTES, "Raw", "Raw - *.md")):
        text = read(path) or ""
        fm, body = frontmatter(text)
        mid = fm.get("meeting-id")
        if not mid:
            continue
        parts = fm.get("participants") or []
        out[mid] = {
            "raw_file": v.rel(path),
            "raw_title": os.path.basename(path)[:-3],
            "title": fm.get("title") or "",
            "source": fm.get("source") or "",
            "date": fm.get("date") or "",
            "start": fm.get("start") or "",
            "end": fm.get("end") or "",
            "platform": fm.get("platform") or "",
            "report_url": fm.get("report-url") or "",
            "complete": str(fm.get("complete", "")).lower() == "true",
            "participants": parts if isinstance(parts, list) else [parts],
            "words": len(body.split()),
        }
    return out


def load_processed(v):
    """meeting-id -> processed read view info."""
    out = {}
    for path in glob.glob(v.p(NOTES, "Processed - *.md")):
        text = read(path) or ""
        fm, body = frontmatter(text)
        mid = fm.get("meeting-id") or ""
        h1 = re.search(r"^# (.+)$", body, re.M)
        heading = plain(re.sub(r",\s*\[\[[^\]]+\]\]\s*$", "", h1.group(1))) if h1 else os.path.basename(path)[11:-3]
        takeaway = []
        tm = re.search(r"^## Takeaway\s*\n(.*?)(?=^#|\Z)", body, re.S | re.M)
        if tm:
            takeaway = [plain(l[2:]) for l in tm.group(1).splitlines() if l.startswith("- ")][:4]
        context = ""
        cm = re.search(r"^- (\d{1,2}:\d{2} IST.*)$", body, re.M)
        if cm:
            context = plain(cm.group(1))
        rec = fm.get("airtable-record") or ""
        out[mid or path] = {
            "meeting_id": mid,
            "note_file": v.rel(path),
            "note_title": os.path.basename(path)[:-3],
            "heading": heading,
            "source": fm.get("source") or "",
            "date": fm.get("date") or "",
            "airtable": rec if re.match(r"^rec[A-Za-z0-9]{14}$", rec) else "",
            "report_url": fm.get("report-url") or "",
            "tags": [t for t in (fm.get("tags") or []) if t not in ("meeting", "readai", "wisprflow")],
            "context": context,
            "takeaway": takeaway,
            "open_boxes": len(re.findall(r"^\s*- \[ \]", body, re.M)),
            "done_boxes": len(re.findall(r"^\s*- \[[xX]\]", body, re.M)),
        }
    return out


def load_log(v):
    """Skip and defer entries, newest state per meeting title wins."""
    text = read(v.p(NOTES, "log.md")) or ""
    events = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = LOG_HEAD.match(line)
        if not m or m.group(2) not in ("skip", "defer", "ingest"):
            continue
        detail = lines[i + 1][2:] if i + 1 < len(lines) and lines[i + 1].startswith("- ") else ""
        idm = re.search(r"`(wispr:[0-9a-f-]+|01[0-9A-Z]{24})`", detail)
        events.append({"date": m.group(1), "op": m.group(2), "title": m.group(3).strip(),
                       "detail": plain(detail), "meeting_id": idm.group(1) if idm else ""})
    return events


def load_wispr_links(v):
    out = {}
    for path in glob.glob(v.p("Wiki", ".inbox", "done", "wispr-*.json")) + glob.glob(v.p("Wiki", ".inbox", "wispr-*.json")):
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for d in data if isinstance(data, list) else [data]:
            if isinstance(d, dict) and d.get("id") and d.get("share_link"):
                out["wispr:" + d["id"]] = d["share_link"]
    return out


def load_lint(v):
    try:
        data = json.load(open(v.p(".lint", "last_run.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return []
    keep = ("structure", "case-variant", "registry")
    return [{"check": f.get("check"), "subject": f.get("subject"), "detail": f.get("detail"),
             "severity": f.get("severity")} for f in data if f.get("check") in keep and not f.get("fixed")]


def build(vault_root, today=None):
    v = Vault(vault_root)
    today = today or dt.date.today()
    todos_doc = json.load(open(v.p("Wiki", ".state", "todos.json"), encoding="utf-8"))
    raw = load_raw(v)
    processed = load_processed(v)
    wispr = load_wispr_links(v)
    log = load_log(v)

    meetings = {}
    for key, pr in processed.items():
        mid = pr["meeting_id"] or key
        r = raw.get(mid, {})
        meetings[mid] = {
            "id": mid,
            "title": pr["heading"],
            "source_title": r.get("title") or "",
            "source": "wisprflow" if mid.startswith("wispr:") or "wispr" in pr["source"].lower() else "readai",
            "date": pr["date"] or r.get("date", ""),
            "start": r.get("start", ""),
            "platform": r.get("platform", ""),
            "participants": r.get("participants", []),
            "status": "captured",
            "note_file": pr["note_file"],
            "raw_file": r.get("raw_file", ""),
            "airtable": pr["airtable"],
            "airtable_url": AIRTABLE_ROW % pr["airtable"] if pr["airtable"] else "",
            "report_url": pr["report_url"] or r.get("report_url", "") or (
                "https://app.read.ai/analytics/meetings/%s" % mid if re.match(r"^01[0-9A-Z]{24}$", mid) else ""),
            "wispr_url": wispr.get(mid, ""),
            "tags": pr["tags"],
            "context": pr["context"],
            "takeaway": pr["takeaway"],
            "reason": "",
        }
    for mid, r in raw.items():
        if mid in meetings:
            continue
        meetings[mid] = {
            "id": mid, "title": r["title"], "source_title": r["title"],
            "source": "wisprflow" if mid.startswith("wispr:") else "readai",
            "date": r["date"], "start": r["start"], "platform": r["platform"],
            "participants": r["participants"], "status": "not_extracted",
            "note_file": "", "raw_file": r["raw_file"], "airtable": "", "airtable_url": "",
            "report_url": r["report_url"], "wispr_url": wispr.get(mid, ""), "tags": [],
            "context": "", "takeaway": [],
            "reason": "Raw transcript landed (%d words) but no read view yet" % r["words"],
        }
    # skip / defer lines: capture failures. Keyed by id when the log names one, else by title+date.
    captured_titles = {(m["source_title"] or m["title"]).strip().lower() for m in meetings.values()}
    for e in log:
        if e["op"] not in ("skip", "defer"):
            continue
        mid = e["meeting_id"] or "log:%s:%s" % (e["date"], e["title"])
        if mid in meetings and meetings[mid]["status"] in ("captured", "not_extracted"):
            continue
        if not e["meeting_id"] and e["title"].strip().lower() in captured_titles:
            continue
        reason = e["detail"].split(": ", 1)[-1] if ": " in e["detail"] else e["detail"]
        meetings[mid] = {
            "id": mid, "title": e["title"], "source_title": e["title"],
            "source": "wisprflow" if mid.startswith("wispr:") or "Wispr" in e["detail"] else "readai",
            "date": e["date"], "start": "", "platform": "", "participants": [],
            "status": "skipped" if e["op"] == "skip" else "deferred",
            "note_file": "", "raw_file": "", "airtable": "", "airtable_url": "",
            "report_url": "https://app.read.ai/analytics/meetings/%s" % mid if re.match(r"^01[0-9A-Z]{24}$", mid) else "",
            "wispr_url": wispr.get(mid, ""), "tags": [], "context": "", "takeaway": [],
            "reason": reason or e["op"],
        }

    todos = []
    for t in todos_doc.get("todos", []):
        created = parse_ordinal(t.get("created"))
        closed = t.get("closed_by") or {}
        todos.append({
            "id": t.get("id"),
            "text": plain(t.get("text")),
            "owner": short_title(t.get("owner")),
            "owner_title": t.get("owner") or "",
            "tag": t.get("tag") or "",
            "tag_short": short_title(t.get("tag")),
            "status": t.get("status"),
            "created": created.isoformat() if created else "",
            "age_days": (today - created).days if created else None,
            "meeting_id": t.get("meeting") or "",
            "source_note": t.get("source") or "",
            "closed": {"date": closed.get("date", ""), "tier": closed.get("tier", ""),
                       "evidence": plain(closed.get("evidence", "")), "reason": plain(closed.get("reason", ""))} if closed else None,
        })
    # seeded todos carry only their source note: link them to that note's meeting
    note_to_meeting = {m["note_file"].rsplit("/", 1)[-1][:-3]: mid for mid, m in meetings.items() if m["note_file"]}
    for t in todos:
        if not t["meeting_id"] and t["source_note"] in note_to_meeting:
            t["meeting_id"] = note_to_meeting[t["source_note"]]
    by_meeting = {}
    for t in todos:
        if t["meeting_id"]:
            by_meeting.setdefault(t["meeting_id"], []).append(t["id"])
    for mid, m in meetings.items():
        m["todo_ids"] = by_meeting.get(mid, [])

    return {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "today": today.isoformat(),
        "vault": os.path.basename(os.path.normpath(vault_root)),
        "meetings": sorted(meetings.values(), key=lambda m: (m["date"], m["start"]), reverse=True),
        "todos": todos,
        "lint": load_lint(v),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from config import vault_path
    snap = build(vault_path())
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in snap.items()}, indent=1))
