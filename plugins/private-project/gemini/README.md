# private-project for Gemini

Implements [`../protocol.md`](../protocol.md) on Gemini. Read the protocol doc first — this file
only covers what's Gemini-specific.

## Two things to verify before you rely on this

This adapter is written from current public documentation, not from hands-on testing against
your account. Confirm both of these yourself before treating a session as actually private and
actually durable:

1. **Temporary Chat + Gems.** Gemini's Temporary Chat mode isn't saved to history and isn't used
   for personalization. Whether it can be opened *while a Gem's custom instructions are active*
   is not clearly documented as of this writing. If your account won't let you combine them,
   fall back to pasting the contents of `templates/gem_instructions.template.txt` directly into
   a Temporary Chat as your first message instead of saving it as a Gem — you lose the one-click
   convenience of a saved Gem, but keep the privacy mode.
2. **File creation from the chat itself, not just Drive's side panel.** Google's own "Gemini in
   Drive" side panel can create Docs/Sheets/Slides and folders. It's not confirmed here whether
   the general Gemini chat interface (gemini.google.com, in Temporary Chat mode) has that same
   create-file ability, or whether it's limited to reading/searching files you already have.
   If chat-side creation isn't available, the workaround is: the assistant tells you exactly what
   to save and where, and you create the file by hand (or via the Drive side panel) — the
   protocol's file/folder conventions don't change either way, only who does the saving.

## Retention specifics for Gemini (verify against current Google docs, not this file)

At the time this was written, Gemini's Temporary Chat is described as persisting for 72 hours
before being deleted, rather than Claude's ~30-day safety/legal retention window. Don't repeat
either number to a user without checking Google's current support docs first — these windows
change.

## Setup

1. Decide whether you're doing this as a Gem (if Temporary Chat + Gems works on your account) or
   as a pasted first message (if not).
2. Fill in `templates/gem_instructions.template.txt` the same way the Claude adapter fills in
   `startup_instructions.txt` — see the interview questions in `../SKILL.md`, which apply
   unchanged regardless of platform.
3. Fill in `templates/onboarding_prompt.template.txt` the same way.
4. Create the Drive folder structure from `../protocol.md` by hand, or via Gemini in Drive's
   side panel if you have Workspace extensions enabled.
5. Save both filled-in files into the folder root.
6. Give whoever's using this the snippet below, adapted with the real folder URL.

## Snippet

```
This is for {{DOMAIN}}. Open a Temporary Chat[, using the {{DOMAIN}} Gem if that combination
works for you]. Reference the startup_instructions.txt file in this Google Drive folder:
{{DRIVE_FOLDER_URL}}. Load it and follow those guidelines for this conversation.
```
