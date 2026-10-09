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
6. Push to a private GitHub repo `abdulrahmanjanoo/todo-360`.
