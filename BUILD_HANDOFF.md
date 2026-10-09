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
- **Gate**: `qa/run.sh` (15 unit tests + 13 Playwright specs). Critic/actor rounds recorded below.

### Review rounds (9 Oct 2026, builder → shots → Jobs/Ive critic + actor playing Abdul → fix)
- **Critic round 1**, "not yet, one short round away", 12 defects: light-mode controls invisible (`--fill` equalled the
  page colour; now iOS tertiarySystemFill), four always-visible action chips per row, "Abdul Rahman Janoo to" on every
  row, Focus listing all 36 meetings, phone overflow and mid-word wraps, revenue said three times per row in the Money
  view, 24-hour "19:41 IST" beside "8:43 AM", Gaps lint rows as file paths, three Focus cards sharing one link,
  Highlights not tappable, sheet leading with the Meeting ID, phone app bar stacked three rows. All applied.
- **Actor round 1** (Playwright through 7 scenes): the #revenue pill silently switched Owner to Everyone, the tag's
  reason lived only in a tooltip, no "back to automatic" state, no feedback on confirming a meeting, HR / our-own-cost
  items tagged (12 lakh offer, cancel a subscription, intern agreements) and a cost sent to a client missed. All applied:
  pill keeps the owner filter, reason printed inline, three states (Revenue / Not revenue / Reset to automatic),
  "Saved" toast, NEGATIVE patterns in `money.py`, "cost to client" pattern.
- **Critic round 2**, "not yet, one short round away", 9 defects: hidden actions still reserved ~300px per row,
  sheet override hover-hidden, same to-do leading two Focus lists, "by you  You" adjacency, phone control row clipping,
  disabled Apply as the only phone header control, lint sublines as log output, metric cards all stamped with the
  vault-read time. All applied (actions overlay on hover, phone rows show them in flow; lint rows in plain words with
  the date; per-metric trailing labels). Builder caught one more from the capture: the hidden overlay masked long
  titles; now the whole trail is hidden until hover.
- **Actor round 2**: "tagging believable, nine of nine; I would use this tomorrow morning on the laptop; on the phone
  once the targets and controls are fixed" (both then applied). Still asks for: snooze choices, revenue grouped by
  account with rupee value, a stale view.
- **Critic round 3**, "not yet", 7: phone separators lost to a `position:static` override, four chips per phone row
  again, hover overlay covering long titles, reason word floating unanchored in Money views, noun labels on the tag
  actions, vault clock on the Revenue highlight, "should clear on a later run". All applied (one "···" chip per row,
  glyph before the reason, "Tag as revenue / Remove tag / Use automatic").
- **Critic round 4**, "not yet", 4: sheet override hidden by a higher-specificity trail rule, desktop hover reflowing
  long rows, chip and trail unstyled on wide touch screens (iPad), chip and circle under 44pt. All applied as **one
  rule set keyed on input, not width**: every non-link row = title + subline + a 44pt "···" chip at the right (visible
  on hover with a pointer, always on touch); the actions open under the row on tap; the sheet's rows keep their
  control visible; the circle gets a 44pt hit area.
- **Critic round 5: VERDICT ship.** "This is the Apple Health of to-dos: the Summary reads like Health's, the lists read
  like Reminders, the money story is told once per screen and never shouts." Two non-blocking notes, both applied:
  phone spec and captures run with touch emulation (`hasTouch`, `isMobile`) so the chip is really exercised; the
  opened action strip aligns with the title column (`grid-column:2/-1`).
- **Lessons for next time** (same as Health 360's): the capture is the truth, not the CSS (two regressions were only
  visible in a screenshot); a desktop browser at phone width is not a phone (`hover:hover` stays true without touch
  emulation); hiding with `opacity:0` still reserves layout; specificity of `.a .b:not(.c) .d` (0,4,0) beats a
  shorter exception, so write the exception longer.

## Data notes
- Seeded to-dos (no `meeting` field) are linked to a meeting through their `source` note.
- Wispr share links only exist for meetings whose raw JSON is still in `Wiki/.inbox/done/`.
  Fix upstream: have `wiki.py land` write `share-link:` into Wispr raw frontmatter.
- Skip/defer rows come from `log.md`; their date is the log date, not the meeting date.

## Open items, in order
1. Abdul tries it for a few days; tune Focus to what he actually clicks. Watch the `#revenue` overrides he makes:
   every "Not revenue" / "Revenue" is a labelled example for tightening `money.py`.
2. Snooze with choices (Tomorrow / Next week / pick a date); bulk actions (select many, mark done / not mine),
   keyboard triage (j/k, d, s, n).
2b. Revenue by account (KCS, ACL, Orient, Nippon, Everest) with the rupee figure when the transcript named one;
   an account page = its to-dos + meetings. Upstream idea: let the daily wiki run write `#revenue` into the note
   itself so the tag exists in Obsidian too (Abdul's "extra hashtag" wording may have meant that).
3. Feed decisions to the daily routine: `not_mine` and `keep` as hints, meeting "did not happen"
   as a flag for the next lint.
4. "Stale" view: open to-dos with no mention for 30 days (needs last-mention data from the engine).
5. Airtable Tasks sync for the to-dos Abdul keeps (optional, ask first).
6. Done 9 Oct 2026: pushed to `github.com/abdulrahmanjanoo/todo-360` (created public; CLAUDE.md asks for private).
