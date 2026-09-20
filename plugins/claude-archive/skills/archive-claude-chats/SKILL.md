---
name: archive-claude-chats
description: Archive Claude chat history to local Markdown/JSON, sorted chronologically. Covers both claude.ai (web) chats — via the internal JSON API — and Claude Code (CLI/desktop) sessions — via their local JSONL transcripts. Use when the user wants to back up, consolidate, search, or migrate any Claude conversation history, projects, memory, or this-repo's-own development history.
---

# archive-claude-chats

Two independent archivers sharing one output shape (`conversation.md` +
`metadata.json`, timestamp-prefixed folders that sort chronologically together).
See [README.md](../../README.md) for the full technical writeup — this file is the
condensed skill entry point. Figure out which one the user means before running
anything: "my Claude chats" / "claude.ai" → `archive_api.py`; "this conversation" /
"Claude Code session" / "our chat history in this terminal" → `archive_code_session.py`.

## Archiving claude.ai chats (`archive_api.py`)

Uses Claude.ai's internal JSON API (not a browser extension or page-scrape), via
[browser-harness](https://github.com/browser-use/browser-harness) as the
authenticated-browser bridge.

**First time using this on a machine?** Read [install.md](../../install.md) instead —
it covers cloning the repo and installing `browser-harness`. This section assumes
that's already done.

### Before running (quick checks, not first-time setup)

1. `which browser-harness` succeeds. If not, this is actually first-time setup —
   go to [install.md](../../install.md).
2. The user's Chrome has a tab logged into claude.ai (any tab; doesn't need to be
   focused). If archiving a *different* Claude.ai account than whatever the
   current Claude Code session is authenticated as, that's fine — this script only
   reads the browser's session cookie, never the CLI's own credentials.

### Running it

```bash
python3 archive_api.py --output <destination-folder> [--max N]
```

Ask the user where they want the archive written — do not assume
`~/gdrive/ObsidianVault/` or any other personal path. A sensible default is
`~/claude-archive`, but confirm rather than guessing, since this is a new directory
creation the user will want to know about in advance.

Use `--max 3` first for any new user/setup to confirm the pipeline works (session
cookie valid, browser-harness reachable) before running the full archive, since a
full run can take a few minutes and there's no resume-from-partial-run support yet.

### What it produces

See [README.md](../../README.md#output-structure) for the full directory layout. In short:
one timestamp-prefixed folder per chat (sorts chronologically by name), a
`_projects/` folder with each project's metadata and knowledge files, and a
`_memory.md` with the account's Settings → Capabilities memory.

### Troubleshooting

- **A chat fails with a `TimeoutError` traceback from browser-harness**: the script
  already retries each chat up to 3 times with increasing timeouts. If a chat still
  fails after that, it's usually one with an unusually large number of attached
  files/images — safe to re-run just that chat afterward rather than the whole
  archive (see the retry pattern in ../../README.md).
- **Everything fails immediately**: check that `browser-harness` can actually reach
  a running, logged-in Chrome (`browser-harness <<< 'print(page_info())'` as a smoke
  test) before assuming the archive script itself is broken.
- **Only some chats show up**: the internal API occasionally changes; if pagination
  looks broken, re-check the `chat_conversations?limit=&offset=` shape against
  what the network tab shows for a real `/recents` page load.

## Archiving Claude Code sessions (`archive_code_session.py`)

Reads the JSONL transcript Claude Code already writes locally to
`~/.claude/projects/<project>/<session-id>.jsonl` — no install, no browser, no
network call, and it works for archiving the *current* conversation too (this repo's
own development history was archived with this script, from inside the session
that built it). Only works for sessions run on the machine you're on now.

### Running it

Don't ask the user to hunt down a session id — resolve by title instead:

```bash
python3 archive_code_session.py --list                                   # browse everything
python3 archive_code_session.py --list --title "some substring"          # narrow first
python3 archive_code_session.py --title "some substring" --output <dir>  # archive directly
```

`--title` auto-resolves if exactly one session matches; if several do, it prints
the candidates (id, last-active time, message count, working directory, title) so
you can either refine the substring or pass the exact file via `--session <path>`.

If the user means *this very conversation*, the running session's own transcript
path is derivable — check `cwd` matches and pick the most-recently-modified file
under that project's `~/.claude/projects/<project>/` directory, or just ask Claude
Code for its own session id if unsure, rather than guessing from `--list` output
that may include other sessions in the same project.

### What it produces

See [README.md](../../README.md#output-structure-1) for the full layout. In short: one
timestamp-prefixed folder per session with `conversation.md` (clean, timestamped
to the minute), `thinking.md` (extended thinking + tool calls/results — the detail
behind the desktop app's collapsed "Ran N commands"), `metadata.json`, and an
`attachments/` folder if the session had any pasted images.

### Troubleshooting

- **`--title` matches nothing**: run `--list` with no filter to see actual titles —
  untitled sessions are shown by a derived title (first line of the first user
  message), which may not match what you'd guess.
- **`--title` matches several sessions**: expected when a title is generic or
  reused; either tighten the substring or pass `--session <path>` from the printed
  candidate list directly.
- **Very large sessions** (hundreds of tool calls) produce a correspondingly large
  `thinking.md` — this is expected, not a bug; tool inputs/outputs are already
  truncated at 4000 characters each to keep it from growing unbounded.
