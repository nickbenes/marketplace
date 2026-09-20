# Folder structure to propose

Claude's Google Drive access from a Claude.ai chat (including incognito chats) can create new
files and folders, but cannot edit or delete existing ones. Every "save" has to be a new file,
never an overwrite. The structure below is designed around that constraint.

```
<Domain Name>/                          [private by default; sharing is optional — see below]
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

Add extra subfolders only if the domain calls for them (confirm with the user first) —
e.g. a finances project might add `Statements/`, a custody-notes project might add
`Incident Log/`. Keep the two standing folders above (`Sessions/` and the details folder)
regardless of domain.

## Why per-session subfolders, not flat dated files

A session can be paused and resumed, and incognito chats can't be reopened once closed, so a
single session may need several incremental saves before (or instead of) a final one. Grouping
each session's incremental and final files together, instead of two flat folders of
same-day files, keeps a paused/resumed session's full history in one place and makes it obvious
which incremental files a given final save superseded.

## Naming the session subfolder

Create it as soon as the topic is reasonably clear — typically right after the first user
message — using the session start timestamp plus a short 3-5 word slug describing the topic
(e.g. `2026-07-22_1730_kids-vaccine-questions`). The folder can't be renamed later, so the slug
doesn't need to be perfect; the timestamp is what actually matters for sorting and identifying
the session. If the topic isn't clear yet, use a generic slug like `general` rather than waiting.

## Reading the "current" state

Because the details folder accumulates a new file per update rather than editing one in place,
always treat the most recently dated file in that folder as current when starting a session.
Older files aren't wrong, just superseded — leave them as history rather than treating them as
conflicting information.

## Sharing (fully optional)

None of this requires sharing the folder at all — the owner can keep it entirely private. If
they do want to share it, Google Drive's own sharing controls handle everything: private to the
owner, shared with one other person, shared with a small group, or "anyone with the link." This
skill doesn't manage permissions — point the user to Drive's normal share dialog once the folder
exists, and let them decide.
