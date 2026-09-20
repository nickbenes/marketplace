# What happens on first run

1. **Interview.** Claude asks a handful of questions: what to call the project, whether anyone
   else will use it alongside you, what persona/expertise the model should take on, whether you
   want any folders beyond the two standing ones (`Sessions/` and the details folder), and how
   often it should check in to offer saving progress (default every 5 exchanges).

2. **Drive folder.** If a Google Drive connector is available and authorized in the session,
   Claude creates the root folder — private by default — and its subfolders directly. If not,
   it gives you the exact folder structure to create by hand (see
   `templates/folder_structure.md`).

3. **Two files written into the root of the folder:**
   - `startup_instructions.txt` — generated from `templates/startup_instructions.template.txt`
   - `onboarding_prompt.txt` — generated from `templates/onboarding_prompt.template.txt`

4. **A snippet, generated from `templates/snippet.template.txt`**, with the real folder URL
   filled in. This is the only thing you paste into a new incognito chat to start a session.

5. **Nothing is pushed anywhere automatically.** This skill only touches your own Google Drive
   (and only if you've authorized that connector) — it never writes to this repo or anywhere
   else.

## Sharing (optional)

The folder doesn't need to be shared with anyone — it's private to you by default. If you do
want to share it, that's a normal Drive share (Drive's own share dialog), entirely up to you:
with one other person, a small group, or "anyone with the link." Whoever you share it with only
ever needs the snippet from step 4 — they don't need this repo, this skill, or any setup of
their own beyond pasting that snippet into a new incognito chat.

## Updating an existing private project

If you already have one of these set up and want to change the check-in cadence, add a folder,
or adjust the persona, just ask Claude to edit `startup_instructions.txt` (or
`onboarding_prompt.txt` if you haven't onboarded yet) directly in Drive — no need to start over.
