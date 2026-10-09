# Janoo To-Do 360, agent guide

A personal desk over Abdul's Obsidian LLM wiki. The vault is the live data source; this app shows every
to-do and meeting the daily Read AI / Wispr Flow run produced, lets Abdul decide on each one, and pushes
"done" back into the vault through the wiki engine. Sibling of Claude Health 360 and Claude Personal Finance.

**Resume here:** read `BUILD_HANDOFF.md` (what exists, open items, next steps), then run the app.

## Run
- `python3 app/server.py` opens http://127.0.0.1:8360 (or double-click `Open To-Do 360.command`).
- Vault path: `config.json` → `vault` (default: iCloud `Obsidian Notes`), or env `TODO360_VAULT`.
- Gate: `qa/run.sh` = Python unit tests (`python3 -m unittest discover -s tests`) + Playwright browser specs
  (`qa/app.spec.js`, system Chrome, against `qa/fake_server.py` on a throwaway vault). Must stay green before
  every commit; add a unit test for new data behaviour and a browser spec for new UI behaviour.
- Design review: `TODO360_URL=http://127.0.0.1:8362 node qa/shots.js <dir>` screenshots every screen (dark,
  light, phone) for the critic round. Procedure (same as Health 360): builder → screenshots → a Jobs/Ive critic
  agent with the 15-point checklist + an actor agent playing Abdul → fix → repeat until the critic says ship.

## Hard rules
- **Read-only on the vault, except through the engine.** `app/export.py` only reads. The only vault
  writes are in `app/decisions.py → apply()`: tick `- [ ] T-xxxx` lines in notes (never under `Raw/`),
  then `wiki.py sync`; fallback `wiki.py close`. Never edit `todos.json`, `log.md`, INDEX or git directly.
- **Raw transcripts are never edited.** Ground truth.
- **Decisions live here**, in `_data/decisions.json` (done, snooze, not_mine, keep; meeting happened / did not).
  The vault snapshot is never stored in this repo; it is rebuilt from the vault on every load.
- **Standard library only** (Python 3.9+, vanilla JS). No build step, no npm.
- **Never invent data.** Missing link = the UI shows it disabled; missing date = "—".
- **No em-dashes** in UI copy, docs or commits.
- **Every element is a link** (Abdul's standing feedback): a meeting opens its drawer, a to-do shows its
  meeting, a gap opens the note in Obsidian.

## Map
- `app/export.py`   vault → snapshot (meetings, todos, lint gaps). Parsers for frontmatter, log, ordinals.
- `app/money.py`    the revenue lens: `classify(text, tag)` → `#revenue` (derived, never written to the vault).
- `app/decisions.py` Abdul's decisions store (todo actions, meeting confirmations, money overrides) and the apply-to-vault step.
- `app/server.py`   localhost server: `/api/snapshot`, `/api/note`, `/api/decision`, `/api/apply`.
- `app/static/index.html` the whole UI (hash routes `#/` Focus · `#/todos` · `#/meetings` · `#/gaps`, `#/meeting/<id>` sheet).
  Design system = Apple Health's, token-for-token with Janoo Health 360 (`shared_ui.py` there): iOS system colours,
  Dynamic Type at Large, inset-grouped cards, one hue per card, Apple date voice (Today / Yesterday / weekday / 6 Oct).
- `qa/` the gate: `run.sh`, `app.spec.js`, `fake_server.py`, `shots.js`, `playwright.config.js`.
- Vault side: `.llm-wiki/runbook.md`, `.llm-wiki/engine/wiki.py`, `Wiki/.state/todos.json`.

## Git practice
Feature → tests green → commit with a plain scoped message. **No Co-Authored-By or AI attribution
in commit messages** (Abdul's hard rule). Remote: `github.com/abdulrahmanjanoo/todo-360`, branch `main`. Keep it private.
