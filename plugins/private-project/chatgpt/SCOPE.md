# private-project for ChatGPT — scoping notes, not yet built

This adapter would implement [`../protocol.md`](../protocol.md) on ChatGPT. It's scoped here
rather than built because, unlike Gemini, ChatGPT has no first-party way to read/write an
arbitrary Google Drive folder from a plain chat — getting there means building and maintaining a
small integration, not just adapting a prompt.

## What ChatGPT has, as of this writing

- **Temporary Chat** — not saved to history, not used for personalization, still follows custom
  instructions if enabled. Confirmed to work together with Custom GPTs, but that combination is
  currently **app-only, not available in the browser** — a real constraint on who can use this
  reliably (verify current status before relying on it; this kind of platform gap tends to close
  over time).
- **Custom GPTs** — the persistent-instructions container, roughly analogous to a Claude Project
  or Gemini Gem. Holds the equivalent of `startup_instructions.txt`/`onboarding_prompt.txt` as
  its configured instructions.
- **Google Drive connector** — as of a mid-2026 update, ChatGPT's Google app integration gained
  write actions (create/edit Docs, Sheets, Slides), not just read. Availability differs by plan:
  Free has no app connections; Pro can self-serve connect; Business has it on by default (admin
  can restrict); Enterprise/Edu requires admin opt-in. This is a meaningfully different
  deployment story than Claude's or Gemini's — a Business/Enterprise user might be blocked by
  their own admin, not by anything this project controls.
- The write actions are described in terms of Docs/Sheets/Slides specifically — whether plain
  `.txt` files and folder creation (what this protocol actually needs) are supported the same
  way is unconfirmed and should be tested directly, not assumed from the Docs/Sheets framing.

## What building this adapter would actually require

1. **Decide the file-I/O approach.** Two options:
   - Use the built-in Google Drive connector if it turns out to support plain-text file and
     folder creation in an arbitrary folder (cheapest — no OAuth work, but capability unverified
     and plan-gated as above).
   - Build a Custom GPT **Action**: an OpenAPI schema describing the Drive API's
     `files.create`/`files.list` endpoints, plus OAuth 2.0 client setup (a registered Google
     Cloud project, consent screen, and the Action's auth config pointed at it). This is real
     setup work and something to maintain, not a one-time prompt change.
2. **Write the Custom GPT instructions**, adapting `../gemini/templates/gem_instructions.template.txt`
   the same way that file was adapted from the Claude version — same collaborator/session-flow
   logic, ChatGPT-specific privacy facts (verify Temporary Chat's actual retention window; don't
   copy Gemini's 72-hour or Claude's ~30-day figures without checking ChatGPT's own docs).
3. **Decide how to handle the app-only Temporary-Chat-with-Custom-GPT limitation** — e.g. document
   it plainly so browser users know to switch to the app, or provide a paste-in fallback (like
   the Gemini adapter's fallback for its own open question) for whoever's stuck on browser.
4. **Test file/folder creation directly** against the connector (or the Action, if built) before
   writing this up as working — don't ship privacy-adjacent instructions based on unverified
   capability claims.

## Recommendation

Don't start this until there's an actual need for it (i.e., someone who wants to run this on
ChatGPT specifically). The Gemini adapter was worth building now because it needed little beyond
adapting the instruction text; this one needs either a capability bet (untested Drive connector)
or new infrastructure (a registered OAuth Action), and that's better scoped against a real user
than spec'd speculatively.
