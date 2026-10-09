# Janoo To-Do 360

See every to-do and meeting from the Obsidian LLM wiki, confirm what happened, and close what is done.

1. Double-click `Open To-Do 360.command` (or run `python3 app/server.py`).
2. The browser opens on http://127.0.0.1:8360.
3. Tap the circle to mark a to-do done, or Snooze, Not mine, Keep. Press **Apply to vault** to close the done ones in Obsidian.
4. To-dos that look like revenue carry a green **#revenue** tag; the **Money** toggle on To-dos shows only those.
   Use **Revenue** / **Not revenue** on a row to correct the tag.

Self-test: `qa/run.sh` (unit tests + browser tests on a throwaway vault).

The vault path is in `config.json`. Agent instructions are in `CLAUDE.md`.
