# private-project

A pattern (and a Claude skill implementing it) for a private, recurring conversation about
something sensitive — family health, finances, custody notes, therapy, job search, anything —
that never touches the assistant's own chat history, but still keeps a real record.

## The problem this solves

Assistants' disposable-chat modes (Claude's incognito chats, Gemini's Temporary Chat, ChatGPT's
Temporary Chat) are genuinely private: not saved to history, not used for training. But they're
also unrecoverable — close the tab and everything in that conversation is gone for good, and
that mode has no memory of past sessions to build on.

This pattern works around that by making a **Google Drive folder** the actual record instead of
chat history. The disposable chat becomes just a window onto it; the folder persists — private
by default, and shareable with one or more trusted people if and however the owner chooses, all
through Drive's own sharing controls.

## Platforms

The pattern itself is described once, model-agnostically, in [`protocol.md`](protocol.md).
Each assistant has its own adapter implementing it:

| Platform | Status | Where |
|---|---|---|
| Claude | Working, this is the original implementation | [`SKILL.md`](SKILL.md), [`templates/`](templates/), [`install.md`](install.md) |
| Gemini | Built, two mechanics unverified — see caveats | [`gemini/`](gemini/) |
| ChatGPT | Scoped, not built — needs either an unverified capability bet or new OAuth infrastructure | [`chatgpt/SCOPE.md`](chatgpt/SCOPE.md) |

The rest of this README covers the Claude adapter specifically. For Gemini or ChatGPT, start at
`protocol.md`, then read the relevant adapter folder.

## Setup prompt (Claude)

Paste this into Claude (chat, Claude Code, or Cowork):

```
I want to set up a private project using the skill at
https://github.com/nickbenes/private-project. It's for <describe your domain, e.g.
"tracking my family's health history" or "financial planning with my partner">.
```

Claude will interview you briefly (domain, whether anyone else will be involved — and if so,
their first names, so sessions can greet the right person — what persona/expertise it should
take on, any extra folders you want) and then generate:

- A Google Drive folder — private by default — with a `Sessions/` folder (one subfolder per
  session, holding incremental and final logs/transcripts) and a living reference doc for your
  domain
- `startup_instructions.txt` — read at the start of every session after the first. Includes the
  collaborator list, so if more than one person uses the project, each session opens by asking
  "is this Alice or Bob?" instead of guessing
- `onboarding_prompt.txt` — read only on the very first session, walks you through populating
  the reference doc
- A short copy-paste snippet — the only thing anyone using this project needs to remember to
  kick off a session

See [SKILL.md](SKILL.md) for exactly how it builds these out, and [install.md](install.md) for
what happens on first run.

## Why Drive and not something fancier

No new infra to run, works from any device, and it's a format (plain text files in folders) that
you (and anyone you optionally share it with) can open, read, and edit by hand if the model is
ever wrong or unavailable. The whole point is that the record shouldn't depend on Claude being
there.

## Privacy notes

Incognito chats aren't saved to chat history or used for training, but they are retained by
Anthropic for a limited window (currently ~30 days) for safety/legal purposes, and they can't be
reopened once closed. This skill is built around those real properties, not an idealized version
of them — see the "Privacy facts to get right" section in [SKILL.md](SKILL.md).

Sharing the Drive folder is entirely optional and entirely up to the owner. It can stay private
to just you, be shared with one other person, a small group, or "anyone with the link" — that's
managed through Drive's normal sharing dialog, not by this skill.

## Adapting this for your own domain

The three templates in `templates/` use `{{PLACEHOLDER}}` substitution for domain name, persona,
extra folders, and check-in cadence. You don't need to edit them directly — describing your
domain to Claude when you invoke the skill is enough. Edit them directly only if you want to
change the pattern itself (e.g. a different default check-in interval).

## Known limitations

- Requires a Google Drive connector/plugin authorized for the account running the chat
- Claude's Drive access from a chat can create files but can't edit or delete them — every save
  is a new timestamped file rather than an update, which is why the folder layout is organized
  the way it is (see `templates/folder_structure.md`)
- The check-in cadence is a prompt-level instruction, not an enforced mechanism — the model can
  still miss a check-in, especially in very long sessions
- This skill doesn't manage Drive sharing permissions for you; if you want to share the folder,
  do that the normal way through Drive once it's created
