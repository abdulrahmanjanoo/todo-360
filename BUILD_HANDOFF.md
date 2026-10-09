# Build handoff

Started 9 Oct 2026 from a Cowork session, to continue in Claude Code.

## Why
The daily wiki run creates more to-dos than Abdul can review (932 open on 9 Oct, 488 on him,
about 1 in 4 older than 30 days). He wants one place to see what was captured, what is missing, and to act.

## What exists (v0.1)
- Live read of the vault on every load (cached 20 s; Refresh forces a re-read).
- **Focus**: counts (open on me, new this week, older than 30 days, meetings to confirm, capture gaps),
  new to-dos on me from the last 7 days, this week's meetings.
- **To-dos**: filter by owner (me / Tericsoft team / external / no owner / everyone), state, search;
  grouped by meeting, newest first. Actions: Done, Snooze 7d, Not mine, Keep (click again to undo).
- **Meetings**: every captured, skipped, deferred and not-processed meeting, with state pill.
  Drawer: did it happen (yes/no), links (Read AI report, Wispr notes, Airtable row, note and raw in
  Obsidian via `obsidian://`), meeting ID, participants, context, takeaway, its to-dos,
  and the note or raw transcript rendered inline.
- **Gaps**: waiting meetings, captured without Airtable, notes failing lint structure checks,
  capture failures, to-dos with no owner.
- **Apply to vault**: closes every to-do marked Done through the engine (tick + `wiki.py sync`).

## v0.2 (9 Oct 2026): revenue lens + Apple Health design system
- **Why:** Abdul: "add an extra hashtag where you see a revenue opportunity… a money-related filter… so I prioritise
  tasks that generate revenue", and "emulate the Apple design experience, the approach we used for the health app:
  a critic, Steve Jobs, an actor and the developer".
- **`#revenue` tag** (`app/money.py`): weighted keyword classifier. Strong commercial terms (proposal, price, quote,
  invoice, payment, contract, SOW, PO, renewal, budget, fee, retainer, rate card / per-unit price, lakh / crore /
  currency, commercials, MSA, discount, negotiation, tender, billing, margin, costing, subscription) score 2;
  deal-stage words (pilot, POC, prospect, opportunity, deal, lead, pipeline, scope, partnership, demo, NDA,
  customer) and tags `p/Lead/*`, `Area/Sales/*`, `p/Partner/*` score 1; a to-do needs ≥ 2 **and** at least one
  strong term or sales tag. On 9 Oct: 290 of 932 open to-dos. A meeting is tagged when its title has a money word,
  its note scores ≥ 4, or at least half (≥ 2) of its to-dos are money: 169 of 298 meetings, 22 of this week's 36.
  Abdul overrides any verdict from the row ("Revenue" / "Not revenue") or the meeting sheet; overrides live in
  `_data/decisions.json → money`. Never written to the vault.
- **Money filter**: To-dos tab toggle (green when on), deep link `#/todos?owner=me&money=1`; Meetings tab has a
  "Revenue" state; every `#revenue` pill is a link to the filtered list. Focus opens with the Revenue card.
- **Apple design system**: tokens copied from Health 360's `shared_ui.py`. Focus = Summary pattern (Large Title,
  six pinned metric cards each a link, two Highlights sentences, three short lists). Reminders-style circle marks
  done; a row you just decided stays visible until you change filters. Row actions appear on hover (always on
  touch). Owner shows as "You", the "Name to …" prefix is trimmed in display, `untagged` and "(Transcript
  Takeaways)" are hidden. Sheet for a meeting: confirm, revenue, links (missing ones disabled), details, to-dos, note.
- **Gate**: `qa/run.sh` (12 unit tests + 9 Playwright specs). Critic/actor rounds recorded below.

## Data notes
- Seeded to-dos (no `meeting` field) are linked to a meeting through their `source` note.
- Wispr share links only exist for meetings whose raw JSON is still in `Wiki/.inbox/done/`.
  Fix upstream: have `wiki.py land` write `share-link:` into Wispr raw frontmatter.
- Skip/defer rows come from `log.md`; their date is the log date, not the meeting date.

## Open items, in order
1. Abdul tries it for a few days; tune Focus to what he actually clicks.
2. Bulk actions (select many, mark done / not mine), keyboard triage (j/k, d, s, n).
3. Feed decisions to the daily routine: `not_mine` and `keep` as hints, meeting "did not happen"
   as a flag for the next lint.
4. "Stale" view: open to-dos with no mention for 30 days (needs last-mention data from the engine).
5. Airtable Tasks sync for the to-dos Abdul keeps (optional, ask first).
6. Done 9 Oct 2026: pushed to `github.com/abdulrahmanjanoo/todo-360` (created public; CLAUDE.md asks for private).
