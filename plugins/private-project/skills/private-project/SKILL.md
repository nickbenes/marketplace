---
name: private-project
description: Set up a private, ongoing project (family health, finances, kids, therapy notes, job search, or anything sensitive) that runs through incognito chats and stores its real history in a Google Drive folder instead of Claude's chat history. Use this whenever the user wants a recurring private conversation with Claude on a sensitive topic, wants to optionally share that private context with one or more trusted people, or asks to set up something like "a private way to track X." Also use when the user references an existing private-project folder and wants to update its instructions, add a new subfolder, or troubleshoot the incognito workflow.
---

# Private Project

A pattern for running a recurring, sensitive conversation with Claude (health, finances, kids,
therapy, legal matters, job search, anything) that:

- Never lands in Claude chat history or model training, by running in **incognito chats**
- Still has a durable, searchable record — because incognito chats can't be reopened once closed
- Can optionally be shared with one or more trusted people (a spouse, a partner, a co-parent, a
  small team) via Google Drive's own sharing controls — sharing is entirely optional and
  managed by the folder's owner, who can keep it fully private, share it with one other person,
  or share it more broadly

The trick: incognito mode gives privacy, but zero memory. This skill fixes the memory problem by
making a **Google Drive folder** the actual record, and giving the model a short paste-in
snippet that points to it. The chat becomes disposable; the folder is what persists — private by
default, and shared with anyone the owner chooses, if they choose to.

## When to use this skill

Trigger this whenever the user describes wanting:
- A private/incognito way to discuss something sensitive with Claude, especially something recurring
- To optionally share that private context with one or more trusted people (not public) —
  or to keep it entirely private to themselves
- Concern about kids, health, finances, legal, therapy, or similarly sensitive subject matter
- "Set up a project like X but private" where X might reference this pattern

Do **not** use this for a normal Claude Project (those are already private to the user's account
and don't need the incognito workaround) — this skill is specifically for content the user does
not want to touch chat history at all, whether or not they end up sharing the Drive folder with
anyone else.

## What you're building, in order

1. **A domain** — a short, non-identifying label for what this project is about (e.g. "family
   health," "finances," "custody notes"). Ask the user for this if it's not obvious. Avoid asking
   for or writing down specific diagnoses or specific dollar figures in anything you generate —
   those belong in the Drive files the user fills in themselves, not in your questions or
   confirmations back to them. Collaborator first names are the one exception (see below) — they
   need to be recorded so sessions can identify who they're talking to.

2. **A Google Drive folder**, private by default, created by the user (or by Claude if a Drive
   connector is available and authorized). Claude's Drive access from a chat can create new
   files and folders but can't edit or delete existing ones, so the layout is built around
   "every save is a new timestamped file," not overwrites:
   - `Sessions/` — one subfolder per session (named with a start timestamp + short slug),
     each holding incremental log/transcript saves plus a final log/transcript if the session
     reaches a clean end
   - `<Domain> Details/` — the living reference (e.g. medications, account numbers, custody
     schedule), where each update is a new dated file and the most recent one is current

   See [`../../templates/folder_structure.md`](../../templates/folder_structure.md) for the exact
   layout, naming scheme, and rationale.

3. **`startup_instructions.txt`** in the root of that folder — read this by the model at the
   start of every session after the first. See
   [`../../templates/startup_instructions.template.txt`](../../templates/startup_instructions.template.txt).
   Fill in the `{{DOMAIN}}`, `{{PERSONA}}`, and `{{COLLABORATORS}}` placeholders based on the
   interview below. `{{COLLABORATORS}}` is the recorded list of first names of everyone who might
   use this project — it's what lets a new session ask "is this Alice or Bob?" instead of
   guessing.

4. **`onboarding_prompt.txt`** in the root — read only on the very first session, walks the user
   through a persona check-in and then populates the details doc. See
   [`../../templates/onboarding_prompt.template.txt`](../../templates/onboarding_prompt.template.txt).

5. **A short paste-in snippet** — the only thing the second person (spouse/partner) actually
   needs to remember. See
   [`../../templates/snippet.template.txt`](../../templates/snippet.template.txt). Keep this to
   2-3 sentences: what the project is called, the folder URL, and which file to load.

## Interview before drafting

Ask (conversationally, not as a form-dump):
- What's the domain / what should this project be called?
- Will anyone else use this alongside the user — no one, one other person, or a small group?
  If so, get each person's first name (not a full legal name, just what they go by) and record
  the list as `{{COLLABORATORS}}` in `startup_instructions.txt`. This is the one piece of
  identifying information this skill does store, because it's what lets a session greet the
  right person and ask "is this Alice or Bob?" when more than one collaborator is listed. Whether
  and how the folder actually gets shared with them is still entirely up to the user via Drive's
  own sharing controls — recording someone's name here doesn't share anything by itself.
- What persona/expertise should the model take on for this domain? (e.g. functional medicine
  expert, fee-only fiduciary financial planner, no persona at all — just a careful note-taker)
- Any domain-specific folders beyond the two standing ones (Sessions/ and the details folder)?
  (e.g. finances might want a "Statements" folder; custody notes might want an "Incident Log")
- How often should the model proactively check in to offer saving progress? Default: every ~5
  exchanges, because incognito chats vanish permanently if the window closes.

## Privacy facts to get right

When explaining incognito chats to the user (especially in the onboarding file), be accurate,
not maximal. As of this writing:
- Incognito chats aren't saved to chat history or used for model training
- They ARE retained by Anthropic for a limited window (currently ~30 days) for safety/legal
  purposes — "not saved to history" is not the same as "not retained at all"
- They cannot be reopened once closed — closing the tab loses everything not saved elsewhere
- Incognito mode isn't available inside Claude Projects
- If Claude has Drive access in the chat, it can still read/write the folder from inside an
  incognito session, whether or not that folder is shared with anyone else

Don't claim stronger privacy guarantees than this. If the user asks and you're not certain
current behavior still matches, search Anthropic's support docs rather than assert from memory.

## Building the files

Once the interview is done, generate the three files from the templates (substituting the
domain, persona, any extra folders, and check-in cadence), and generate the snippet. If the user
has Drive access available in this session, offer to create the folder structure and upload the
files directly. If not (e.g. voice mode, no connector), hand them the file contents to paste in
themselves along with the folder structure to create by hand.

Always give the user the finished snippet as a standalone, copy-pasteable block at the end —
that's the only artifact anyone using this project needs day-to-day, including anyone the
folder later gets shared with.

## After first use

If the user reports back that the check-in cadence is annoying, too sparse, or that they want
additional folders, edit `startup_instructions.txt` (or `onboarding_prompt.txt` if onboarding
hasn't happened yet) directly in Drive rather than starting over — these files are meant to be
living documents.
