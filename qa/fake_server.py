"""Start To-Do 360 on a throwaway vault for the browser tests.

    python3 qa/fake_server.py [port]      prints the URL, serves until killed

The vault is the same fixture the unit tests use (tests/test_app.py), copied into a temp folder,
plus a few extra to-dos so the lists have something to show. Decisions go to a temp folder too.
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "app"))

import test_app  # noqa: E402

tmp = tempfile.mkdtemp(prefix="todo360-qa-")
vault = os.path.join(tmp, "Obsidian Notes")
test_app.make_vault(vault)
# a few more to-dos on Abdul: one revenue, one plain, one stale
extra = [
    {"id": "T-0101", "text": "[[m/Tericsoft/Abdul Rahman Janoo|Abdul]] to send Pradip the pricing proposal for the pilot",
     "owner": "m/Tericsoft/Abdul Rahman Janoo", "tag": "p/Lead/Nippon/OCR", "status": "open", "created": "October 8th, 2026",
     "meeting": "01M4DTSVYXQQM0DXNVJ2QH3EXT", "closed_by": None},
    {"id": "T-0102", "text": "[[m/Tericsoft/Abdul Rahman Janoo|Abdul]] to review the call recordings",
     "owner": "m/Tericsoft/Abdul Rahman Janoo", "tag": "", "status": "open", "created": "October 7th, 2026",
     "meeting": "01M4DTSVYXQQM0DXNVJ2QH3EXT", "closed_by": None},
    {"id": "T-0103", "text": "[[m/Tericsoft/Abdul Rahman Janoo|Abdul]] to confirm the 20 lakh budget with Arihant",
     "owner": "m/Tericsoft/Abdul Rahman Janoo", "tag": "Area/Sales/Pipeline", "status": "open", "created": "August 1st, 2026",
     "meeting": "01M4DTSVYXQQM0DXNVJ2QH3EXT", "closed_by": None},
]
p = os.path.join(vault, "Wiki", ".state", "todos.json")
doc = json.load(open(p))
doc["todos"] += extra
json.dump(doc, open(p, "w"))

os.environ["TODO360_VAULT"] = vault
os.environ["TODO360_DATA"] = os.path.join(tmp, "data")
os.environ["TODO360_PORT"] = sys.argv[1] if len(sys.argv) > 1 else "8361"
sys.argv = [sys.argv[0], "--no-browser"]
import server  # noqa: E402

server.main()
