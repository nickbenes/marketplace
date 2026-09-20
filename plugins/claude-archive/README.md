# claude-archive

Archive your Claude chat history to local Markdown/JSON files, sorted
chronologically. Two archivers, for two different sources, sharing one output
shape:

| | [`archive_api.py`](#archiving-claudeai-chats) | [`archive_code_session.py`](#archiving-claude-code-sessions) |
|---|---|---|
| Source | claude.ai (web) chats | Claude Code (CLI/desktop) sessions |
| How | Claude.ai's internal JSON API, via a real browser | Local JSONL transcripts Claude Code already writes to disk |
| Extra install | [browser-harness](https://github.com/browser-use/browser-harness) | none — stdlib only |
| Needs | Chrome open, logged into claude.ai | nothing — reads local files on the same machine |

## Archiving claude.ai chats

Every conversation, every project's knowledge base, and your saved memory, pulled
from Claude.ai's own internal JSON API (the one the web client itself calls) rather
than a browser-extension export, so you get:

- Every chat, fully paginated (not just what's rendered in the sidebar)
- Real per-message and per-chat timestamps (not scraped/guessed)
- Clean conversation text (no sidebar/nav noise)
- Text attachments inlined automatically (Claude already extracts their text)
- Code-execution output files (images, generated PDFs rendered as page previews) downloaded
- Every project's name, description, custom instructions, and knowledge-base files
- Your account-level "memory" (Settings → Capabilities)

### Setup prompt

Paste this into Claude Code or Claude Desktop — no cloning, installing, or terminal
commands needed on your end first:

```text
I want to archive all my Claude chat history. Please use the latest skill from
https://github.com/nickbenes/claude-archive to do that.
```

The agent will clone this repo, install its one dependency (`browser-harness`) if
missing, ask where you want the archive saved, and run it — see
[install.md](install.md) for exactly what it'll do on first run.

### How it works

Claude.ai puts a Cloudflare bot check in front of its API, so plain `requests`/`curl`
calls get a 403 even with a valid session cookie. This script instead runs the exact
same `fetch()` calls *from inside your already-logged-in Chrome tab*, using
[browser-harness](https://github.com/browser-use/browser-harness) as the bridge — same-origin,
real browser TLS fingerprint, no bot check triggered. No login flow, no headless
browser to configure: it just uses whatever Chrome session you already have open.

### Prerequisites

1. **Python 3.8+** (stdlib only — no pip installs needed for this script itself)
2. **[browser-harness](https://github.com/browser-use/browser-harness)** installed and on your `$PATH`.
   Follow that repo's README (it has an LLM-installable setup prompt), or just use
   the setup prompt above and let Claude handle it.
3. **Chrome open and logged into claude.ai** — any tab, doesn't need to be the active one.

### Usage

If you used the setup prompt above, you're done — Claude ran this for you. To run
it yourself directly:

```bash
python3 archive_api.py --output ~/claude-archive
```

Options:

- `--output PATH` — where to write the archive (default: `~/claude-archive`)
- `--max N` — only process the first N chats (useful for a quick test run)

A full run of ~125 chats (with attachments/files) takes about 2-3 minutes.

### Output structure

```
claude-archive/
├── _memory.md                          # Your Settings → Capabilities memory
├── _projects/
│   └── <Project Name>/
│       ├── metadata.json               # name, description, custom instructions
│       └── <knowledge-file>.html        # each project doc, full content
└── 20260701_132222_Chat_title/
    ├── conversation.md                  # full chat, real timestamps per message
    ├── metadata.json                    # chat id, url, created/updated_at
    ├── attachments/                     # text files you uploaded (extracted text)
    │   └── some_file.txt
    └── files/                           # images/previews generated during the chat
        └── preview_0.png.webp
```

Folder names are prefixed `YYYYMMDD_HHMMSS_`, so a plain alphabetical sort of the
archive directory is also a chronological sort. Chats with no discoverable creation
timestamp (shouldn't normally happen) fall back to an `undated_` prefix.

### Known limitations

- **Requires a real, logged-in browser session** — this can't run on a headless
  server with no browser at all. It rides your existing Chrome session, so if you're
  not logged into claude.ai in some open Chrome tab, it has nothing to authenticate with.
- **Uses Claude.ai's internal API**, which is undocumented and could change without
  notice. If a run starts failing across the board, that's the first thing to check.
- **Multiple accounts**: it archives whichever account is logged into the browser tab
  browser-harness attaches to — independent of any other Claude account/session on
  the same machine (e.g. your Claude Code CLI login). See "Multiple accounts" below.
- Binary (non-image) attachments beyond what Claude's own text extraction covers
  aren't separately downloaded — only `extracted_content` text and code-execution
  image previews are pulled today.

### Multiple accounts / different email than Claude Code

The script authenticates purely off the browser's session cookie — it has no idea
what account your Claude Code CLI itself is logged in as, and doesn't need to. If you
want to archive a different Claude.ai account than the one Claude Code uses:

1. Open (or switch to) a Chrome profile/tab logged into that account at claude.ai
2. Point `browser-harness` at that Chrome instance (see its README for how it selects
   a running Chrome)
3. Run the script as normal — it'll pick up whatever account is in that tab

### Alternative: no browser-harness install, using Claude_in_Chrome instead

If you don't want to install `browser-harness` but you do have Anthropic's
**Claude in Chrome** extension connected (its browser-automation tools include one
that executes arbitrary JS in a page, equivalent to what this script needs),
you can skip installing anything and instead ask Claude directly:

> Using the Claude in Chrome extension, please archive my Claude.ai chats using the
> same internal-API approach as https://github.com/nickbenes/claude-archive
> (fetch `/api/organizations/{org_id}/chat_conversations` etc. from inside my logged-in
> tab via the JS-execution tool) — save the output to <your chosen folder>.

**Trade-off to know before choosing this path**: `archive_api.py` is a standalone
script — once started, it runs unattended with no LLM involved per chat, which is
why archiving 125 chats takes about 2-3 minutes. Claude_in_Chrome, by contrast, is
only callable *by Claude, inside a live conversation* — there's no way to script it
to run in the background. Going this route means Claude makes one tool call per
chat, in real time, inside your conversation: noticeably slower, consumes context/
tokens proportional to how many chats you have, and can't be kicked off and walked
away from the way the script can. It's the right choice if you'd rather not install
anything; the script is the right choice for a large history or if you want to
re-run archives periodically without babysitting a conversation.

## Archiving Claude Code sessions

Archives a Claude Code (CLI or desktop app) conversation — including this repo's
own development history, or any other session on the machine — using local files
only. No browser, no API, no `browser-harness`: Claude Code already writes every
session to disk as a JSONL transcript under `~/.claude/projects/<project>/<session-id>.jsonl`,
one line per event, already timestamped. `archive_code_session.py` just parses that.

This only works for sessions that ran **on the machine you run it from** — the
transcripts are local files, not something fetched from a server.

### Usage

Browse what's available first — no need to know a session id or file path up front:

```bash
python3 archive_code_session.py --list
```

Narrow by a substring of the title:

```bash
python3 archive_code_session.py --list --title "GitHub setup"
```

Then archive by title (auto-resolves if exactly one session matches; otherwise
prints the candidates so you can disambiguate):

```bash
python3 archive_code_session.py --title "GitHub setup" --output ~/claude-archive
```

Or point directly at a known transcript file:

```bash
python3 archive_code_session.py --session ~/.claude/projects/<project>/<session-id>.jsonl --output ~/claude-archive
```

### Output structure

```
claude-archive/
└── 20260823_192838_Private-project_skill_GitHub_setup/
    ├── conversation.md        # clean user/assistant text, timestamped to the minute
    ├── thinking.md            # extended thinking + tool calls/results — the detail
    │                          # behind the desktop app's collapsed "Ran N commands"
    ├── metadata.json          # session id, title, start/end, message/tool-call counts, models
    └── attachments/           # images you pasted into the conversation (decoded from
        └── image_001.png      # the transcript's inline base64), only created if any exist
```

Folder names are prefixed with the session's start time (`YYYYMMDD_HHMMSS_`), same
convention as the claude.ai archiver, so both flavors sort together chronologically
in the same archive directory.

A session's title comes from whatever custom title Claude Code has recorded for it;
if none was set, the first real line of text from the first user message is used
instead (an image-only first message falls through past the placeholder to real
text further in, or to the session id if there genuinely isn't any).

### Known limitations

- **Local only** — this reads files already on disk; it cannot fetch a session that
  ran on a different machine.
- **No resume/incremental mode** — a long-running session (like this repo's own
  development history) can be re-archived any time; each run re-parses the whole
  transcript and overwrites that session's folder, it doesn't append to a prior
  export.
- **Very large sessions produce very large `thinking.md` files** — tool inputs/
  outputs are truncated at 4000 characters each to keep things readable, but a
  session with hundreds of tool calls can still produce a multi-hundred-KB file.
  Tested up to 1449 messages / 529 tool calls without issue, just a large file.
- Tool results that are themselves images (e.g. a screenshot returned by a browser
  tool) are noted as `[image result]` in `thinking.md` rather than extracted —
  only images sent as actual user message content are saved to `attachments/`.

## Using this as a Claude Code skill

Install it as a plugin from the marketplace this repo also hosts:

```
/plugin marketplace add nickbenes/claude-archive
/plugin install claude-archive@claude-archive-marketplace
```

See [skills/archive-claude-chats/SKILL.md](skills/archive-claude-chats/SKILL.md) for
the skill itself, invocable as `/claude-archive:archive-claude-chats` once installed.
