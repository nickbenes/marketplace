# The private-project protocol

This describes the pattern itself, independent of which AI assistant runs it. Read this first;
then read the adapter for whichever assistant you're actually using — [`claude/`](claude/),
[`gemini/`](gemini/), or [`chatgpt/`](chatgpt/) (scoped, not yet built) — for the platform-specific
mechanics.

## The idea

Run a recurring, sensitive conversation (family health, finances, custody notes, therapy, job
search, anything) in whatever "don't save this to my history" mode the assistant offers, and use
a **Google Drive folder you own** as the durable record instead of the assistant's own memory.
The disposable-chat mode gives privacy; the Drive folder gives continuity. Sharing the folder
with a partner, co-parent, or small group is optional and handled entirely by Drive's own
sharing controls — this protocol never manages permissions itself.

This only requires two things from a host assistant:
1. Some mode that doesn't save the conversation to persistent chat history or use it for training
   (temporary/incognito/private chat — naming and retention specifics vary; see each adapter).
2. Some way to read and write plain-text files in a Google Drive folder from within that mode.

Everything else below is just conventions for organizing those files — no code, no assistant-
specific APIs.

## Folder structure

```
<Domain Name>/                          [private by default; sharing is optional]
├── startup_instructions.txt
├── onboarding_prompt.txt
├── Sessions/
│   └── YYYY-MM-DD_HHMM_<short-slug>/   # one subfolder per session, named at session start
│       ├── incremental/
│       │   ├── YYYY-MM-DD_HHMM_log.txt          # one pair per safety check-in
│       │   └── YYYY-MM-DD_HHMM_transcript.txt
│       ├── session_log_final.txt        # written only if the session reaches a clean end
│       └── transcript_final.txt
└── <Domain> Details/
    └── YYYY-MM-DD_HHMM_details.txt      # each update is a new file; most recent = current
```

Add extra subfolders only if the domain calls for them (e.g. a finances project might add
`Statements/`; a custody-notes project might add `Incident Log/`). Keep the two standing folders
(`Sessions/` and the details folder) regardless of domain.

**Append-only by default.** Some assistants' Drive access can create files but not edit or
delete existing ones (true for Claude's connector as of this writing; verify for whatever
assistant you're adapting). Even where in-place edits are technically possible, treat every save
as a new timestamped file — it's simpler to reason about, avoids silent overwrites, and works
identically across assistants regardless of their actual edit capability. The most recently
dated file in a folder is always the current version; older ones are history, not conflicts.

## The two instruction files

- **`startup_instructions.txt`** — read at the start of every session after the first. Contains
  the domain, the persona the assistant should take on, the collaborator list (see below), the
  folder structure, and the session flow described below.
- **`onboarding_prompt.txt`** — read only on the very first session. Walks the user through a
  privacy/setup explanation, a persona check-in, and populating the details folder for the first
  time. After that first session, it's never read again (though it stays in the folder as a
  record of how onboarding went).

Both are plain text with `{{PLACEHOLDER}}` substitutions filled in once at setup time — domain,
persona, collaborator list, extra folders, check-in cadence, and details-gathering fields. See
an adapter's `templates/` folder for the actual placeholder set, since it varies slightly by
platform (e.g. Gemini's privacy-facts placeholder differs from Claude's).

## Collaborators

Record the first name of everyone who might show up to a session, gathered once at setup. This
is the one piece of identifying information this protocol deliberately stores — everything else
(diagnoses, account numbers, custody specifics) belongs only in the details files the user fills
in themselves, never in the instruction files or in anything the assistant generates back to the
user during setup.

The reason to store first names: it lets a session identify who it's talking to instead of
guessing from writing style, which matters once a folder is shared with more than one person.

## Session flow

1. **Very first session ever** → load `onboarding_prompt.txt` instead of the rest of this list.
2. **Who's here** — if more than one collaborator is on record, ask which of them you're
   speaking with before anything else (e.g. "Hi — is this Alice or Bob?"). If exactly one
   collaborator is on record, greet them by name without asking.
3. Note the session start time and ask what they'd like to focus on today.
4. As soon as the topic is reasonably clear (typically after the first user message), create
   this session's subfolder under `Sessions/`, named with the start timestamp and a short slug.
5. During the session, reference the most recent file in the details folder for context. If new
   relevant information comes up, save an updated details file as a new timestamped file.
6. **Safety check-ins** — because a closed disposable-mode chat generally cannot be reopened or
   recovered, check in roughly every N exchanges (set at setup time, default ~5) and offer to
   save an incremental log + transcript into this session's `incremental/` folder. Do this
   proactively; don't wait for the user to remember.
7. At the end of the session (or whenever the user wants to stop and doesn't expect to resume
   immediately), summarize highlights, note the end time, and save `session_log_final.txt` and
   `transcript_final.txt`.

## Privacy facts — verify per platform, don't assume

Every assistant's disposable-chat mode has different actual guarantees. Before explaining this
to a user, confirm current behavior for the specific platform rather than asserting from
training data or copying another platform's facts — retention windows, training-data exclusion,
and reopenability all vary and change over time. At minimum, get right for the target platform:
- Is it actually excluded from chat history and from being used for model training?
- Is it retained internally for some window (safety/legal) even though it's not in visible
  history? For how long?
- Can it be reopened once closed, or is it gone for good?
- Can the assistant's temporary/incognito mode be combined with whatever persistent-instructions
  feature that platform uses (Claude Projects, Gemini Gems, ChatGPT Custom GPTs)? Several
  platforms restrict this combination, which affects how the adapter has to be invoked.

Don't claim stronger privacy guarantees than what's actually verified. State facts, not vibes,
and say "unverified — check current docs" rather than guessing when unsure.

## What varies by platform (belongs in the adapter, not here)

- The exact name and mechanics of the disposable-chat mode.
- Whether/how persistent custom instructions (a "project," "Gem," or "Custom GPT") can be
  combined with that mode, and what to do if they can't.
- How the assistant actually reads/writes the Drive folder — a first-party connector, a
  Workspace-native integration, or a custom Action requiring OAuth setup.
- Whether file creation only, or also in-place editing, is available.
- The current, verified privacy facts for that specific platform.
