---
name: claude-archive-install
description: Clone claude-archive, install its one dependency (browser-harness), and run a test archive. Use once per machine.
---

# claude-archive install

Use once. For repeat/day-to-day use after this, read `SKILL.md`.

**Only needed for `archive_api.py` (claude.ai web chats).** The other script in
this repo, `archive_code_session.py` (Claude Code session transcripts), needs
none of this — no `browser-harness`, no browser at all, just Python stdlib and
the local `~/.claude/projects/` transcripts Claude Code already writes. If the
user only wants that one, skip straight to `python3 archive_code_session.py --list`
after cloning.

## Fast path

```bash
git clone https://github.com/nickbenes/claude-archive.git ~/claude-archive-skill
cd ~/claude-archive-skill

which browser-harness || echo "NEEDS_INSTALL"
```

If `browser-harness` is missing, install it per
https://github.com/browser-use/browser-harness/blob/main/install.md (short version:
`uv tool install --python 3.12 --upgrade --force browser-harness`), then confirm it
can reach a real browser:

```bash
browser-harness <<'PY'
print(page_info())
PY
```

If that prints page info, browser-harness is working. If it errors, follow
browser-harness's own install.md troubleshooting (usually: open
`chrome://inspect/#remote-debugging` and tick the checkbox).

Confirm the user has a Chrome tab open and logged into claude.ai — any tab, doesn't
need to be focused.

Ask the user where they want their archive saved (do not assume a path — a
reasonable default to suggest is `~/claude-archive`). Then run a small test first:

```bash
python3 archive_api.py --output <chosen-path> --max 3
```

Check the 3 output folders look right (real timestamps in folder names, clean
`conversation.md` content, no sidebar/nav noise) before running the full archive:

```bash
python3 archive_api.py --output <chosen-path>
```

A full run over ~100-150 chats typically takes 2-4 minutes.

## If it fails

- **`browser-harness: command not found`** — the install above didn't put it on
  `$PATH`; check `uv tool list` / the shell's PATH, or re-run the browser-harness
  install.md steps.
- **Every chat fails immediately** — browser-harness itself can't reach a real
  browser. Test with `browser-harness <<< 'print(page_info())'` in isolation before
  assuming this script is broken.
- **A handful of chats fail with a `TimeoutError`** — normal and already retried
  automatically (3 attempts, increasing timeout) inside the script; usually
  chats with unusually many attached files/images. Safe to ignore or re-run just
  those afterward.
- **Output looks like a full page dump (sidebar nav, "New chat", "Recents", etc.)**
  — that would mean the internal API calls are failing silently and something is
  falling back to old behavior; this shouldn't happen with the current script, but
  if seen, stop and report it rather than continuing — see README.md's
  "Known limitations" for what changed and why.
