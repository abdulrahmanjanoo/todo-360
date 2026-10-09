"""Run: python3 -m unittest discover -s tests   (from the project root)

Uses a tiny fake vault in a temp folder, so it never touches the real one.
"""
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

PROCESSED = """---
type: processed-transcript
source: Read AI
date: 2026-10-08
meeting-id: 01M4DTSVYXQQM0DXNVJ2QH3EXT
airtable-record: recS1uMAsYcR3jiI0
raw: "[[Raw - Pansoft - October 8th, 2026]]"
tags: [meeting, readai, partnerships]
---

# Pansoft partnership intro call, [[October 8th, 2026]]

- 18:51 IST, Teams. Intro call with [[m/Pansoft/Giridharan Balakumar|Giridharan]].

## Insights
- **What happened.** Talked.

## Takeaway
- No deal yet.

### Action plan
- [ ] T-1299 [[m/Pansoft/Giridharan Balakumar|Giridharan]] to send the brochure
"""
RAW = """---
type: raw-transcript
source: Read AI
date: 2026-10-08
meeting-id: 01M4DTSVYXQQM0DXNVJ2QH3EXT
title: "Tericsoft x Pansoft Meeting"
start: "18:51 IST"
platform: teams
participants:
  - "Rehan Surya (attended)"
report-url: https://app.read.ai/analytics/meetings/01M4DTSVYXQQM0DXNVJ2QH3EXT
complete: true
---

**Rehan Surya** (18:51): Hello there.
"""
LOG = """# Log

## [2026-10-09] skip | Tericsoft x Prem Cargo Meeting
- Read AI `01M4DQC6977RCF9YJJEEM9ZEWF`. Tericsoft x Prem Cargo Meeting, October 8th, 2026: empty capture (8 words)

## [2026-10-09] defer | Bank Loan Guy
- Wispr Flow `wispr:1244d25c-7fd8-42bc-8add-4177fef6cb2a`. Bank Loan Guy, October 7th, 2026: not processed at source yet
"""
TODOS = {"seeded": "x", "note": "x", "todos": [
    {"id": "T-1299", "text": "[[m/Pansoft/Giridharan Balakumar]] to send the brochure", "owner": "m/Pansoft/Giridharan Balakumar",
     "tag": "Area/Sales/Partnerships", "status": "open", "created": "October 8th, 2026",
     "source": "Processed - Pansoft partnership intro call - October 8th, 2026", "meeting": "01M4DTSVYXQQM0DXNVJ2QH3EXT", "closed_by": None},
    {"id": "T-0006", "text": "[[m/Tericsoft/Abdul Rahman Janoo|Abdul]] to send the deck", "owner": "m/Tericsoft/Abdul Rahman Janoo",
     "tag": "p/Client/ACL/VoiceBot", "status": "open", "created": "September 8th, 2026",
     "source": "Processed - Pansoft partnership intro call - October 8th, 2026", "closed_by": None},
]}


def make_vault(root):
    n = os.path.join(root, "Read AI Transcribe Notes")
    os.makedirs(os.path.join(n, "Raw"))
    os.makedirs(os.path.join(root, "Wiki", ".state"))
    open(os.path.join(n, "Processed - Pansoft partnership intro call - October 8th, 2026.md"), "w").write(PROCESSED)
    open(os.path.join(n, "Raw", "Raw - Pansoft - October 8th, 2026.md"), "w").write(RAW)
    open(os.path.join(n, "log.md"), "w").write(LOG)
    json.dump(TODOS, open(os.path.join(root, "Wiki", ".state", "todos.json"), "w"))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.vault = os.path.join(self.tmp, "Obsidian Notes")
        make_vault(self.vault)
        os.environ["TODO360_VAULT"] = self.vault

    def tearDown(self):
        shutil.rmtree(self.tmp)


class ExportTest(Base):
    def test_snapshot(self):
        import export
        s = export.build(self.vault, today=dt.date(2026, 10, 9))
        by = {m["id"]: m for m in s["meetings"]}
        m = by["01M4DTSVYXQQM0DXNVJ2QH3EXT"]
        self.assertEqual(m["status"], "captured")
        self.assertEqual(m["title"], "Pansoft partnership intro call")
        self.assertEqual(m["airtable"], "recS1uMAsYcR3jiI0")
        self.assertTrue(m["raw_file"].endswith("Raw - Pansoft - October 8th, 2026.md"))
        self.assertEqual(m["takeaway"], ["No deal yet."])
        self.assertEqual(set(m["todo_ids"]), {"T-1299", "T-0006"})  # seeded todo linked by source note
        self.assertEqual(by["01M4DQC6977RCF9YJJEEM9ZEWF"]["status"], "skipped")
        self.assertEqual(by["wispr:1244d25c-7fd8-42bc-8add-4177fef6cb2a"]["status"], "deferred")
        t = {t["id"]: t for t in s["todos"]}
        self.assertEqual(t["T-0006"]["text"], "Abdul to send the deck")
        self.assertEqual(t["T-0006"]["age_days"], 31)
        self.assertEqual(t["T-1299"]["owner"], "Giridharan Balakumar")

    def test_ordinal(self):
        import export
        self.assertEqual(export.parse_ordinal("October 22nd, 2026"), dt.date(2026, 10, 22))
        self.assertIsNone(export.parse_ordinal("someday"))


class DecisionsTest(Base):
    def setUp(self):
        super().setUp()
        import decisions
        self.d = decisions
        self.d.PATH = os.path.join(self.tmp, "decisions.json")

    def test_record_and_clear(self):
        d = self.d.record("todo", "T-1299", "snooze")
        self.assertEqual(d["todos"]["T-1299"]["action"], "snooze")
        self.assertIn("until", d["todos"]["T-1299"])
        d = self.d.record("todo", "T-1299", "clear")
        self.assertNotIn("T-1299", d["todos"])
        d = self.d.record("meeting", "wispr:abc-1", "happened")
        self.assertEqual(d["meetings"]["wispr:abc-1"]["confirmed"], "happened")

    def test_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            self.d.record("todo", "../etc", "done")
        with self.assertRaises(ValueError):
            self.d.record("todo", "T-1", "delete_everything")

    def test_tick_never_touches_raw(self):
        raw_path = os.path.join(self.vault, "Read AI Transcribe Notes", "Raw", "x.md")
        open(raw_path, "w").write("- [ ] T-1299 should stay\n")
        changed = self.d._tick(self.vault, "T-1299")
        self.assertEqual(len(changed), 1)
        self.assertIn("- [x] T-1299", open(os.path.join(self.vault, changed[0])).read())
        self.assertIn("- [ ] T-1299", open(raw_path).read())

    def test_dry_run(self):
        self.d.record("todo", "T-1299", "done")
        r = self.d.apply(dry_run=True)
        self.assertEqual(r["log"], ["T-1299: would close"])


class ServerTest(Base):
    def test_safe_note(self):
        import server
        self.assertIsNotNone(server.safe_note("Read AI Transcribe Notes/Raw/Raw - Pansoft - October 8th, 2026.md"))
        self.assertIsNone(server.safe_note("../../etc/passwd"))
        self.assertIsNone(server.safe_note("Wiki/.state/todos.json"))


if __name__ == "__main__":
    unittest.main()
