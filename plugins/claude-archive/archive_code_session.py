#!/usr/bin/env python3
"""
Archive a Claude Code session transcript to the same folder structure as the
claude.ai archiver (archive_api.py): conversation.md, metadata.json, plus a
thinking.md for extended-thinking/tool-call detail and an attachments/ folder
for any embedded user-provided images.

Claude Code stores each session as a JSONL transcript under
~/.claude/projects/<sanitized-cwd>/<session-id>.jsonl — one line per event,
already timestamped. No browser, no API calls, no external dependency: this
just parses that file directly.
"""

import argparse
import base64
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional


def sanitize_name(name: str, max_len: int = 80) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name or 'untitled')
    name = re.sub(r'\s+', '_', name.strip())
    name = name.rstrip('._- ')
    return name[:max_len] if name else 'untitled'


def load_entries(jsonl_path: Path):
    entries = []
    with open(jsonl_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def get_title(entries, fallback: str) -> str:
    for e in entries:
        if e.get('type') == 'custom-title' and e.get('customTitle'):
            return e['customTitle']
    return fallback


def resolve_title(entries, msg_entries, session_id: str) -> str:
    """Custom title if the user set one; otherwise the first line of the first
    user message; otherwise the session id. Shared by both the archiver and
    --list so a session's derived name is consistent between them."""
    title = get_title(entries, fallback=None)
    if title:
        return title
    for e in msg_entries:
        if e['message'].get('role') != 'user':
            continue
        content = e['message'].get('content')
        # Only real text counts for a derived title — an image-only first
        # message (no accompanying caption) falls through to the id instead
        # of using the "[image attached]" placeholder as a folder name.
        if isinstance(content, str) and content.strip():
            return content.strip().splitlines()[0][:70]
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text' and c.get('text', '').strip():
                    return c['text'].strip().splitlines()[0][:70]
    return f"Claude Code session {session_id[:8]}"


def fmt_minute(ts: Optional[str]) -> str:
    if not ts:
        return 'unknown-time'
    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    return dt.strftime('%Y-%m-%d %H:%M')


def text_from_content(content) -> str:
    """Clean, human-readable text only — used for conversation.md."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if not isinstance(c, dict):
                continue
            t = c.get('type')
            if t == 'text':
                parts.append(c.get('text', ''))
            elif t == 'image':
                parts.append('*[image attached — see attachments/]*')
            # tool_use / tool_result / thinking are intentionally omitted here;
            # they go in thinking.md instead so conversation.md stays readable.
        return '\n\n'.join(p for p in parts if p)
    return ''


def tool_result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get('type') == 'text':
                parts.append(c.get('text', ''))
            elif isinstance(c, dict) and c.get('type') == 'image':
                parts.append('[image result]')
        return '\n'.join(parts)
    return str(content)


def build_archive(jsonl_path: Path, archive_root: Path) -> Path:
    entries = load_entries(jsonl_path)
    session_id = jsonl_path.stem

    msg_entries = [e for e in entries if e.get('type') in ('user', 'assistant')]
    if not msg_entries:
        raise RuntimeError("No user/assistant messages found in this session")

    timestamps = [e['timestamp'] for e in msg_entries if e.get('timestamp')]
    started_at = min(timestamps) if timestamps else None
    ended_at = max(timestamps) if timestamps else None

    title = resolve_title(entries, msg_entries, session_id)
    safe_title = sanitize_name(title)

    if started_at:
        dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        prefix = dt.strftime('%Y%m%d_%H%M%S')
    else:
        prefix = 'undated'

    folder = archive_root / f"{prefix}_{safe_title}"
    folder.mkdir(parents=True, exist_ok=True)

    convo_lines = [f"# {title}", ""]
    if started_at:
        convo_lines.append(f"**Started:** {started_at}")
    if ended_at:
        convo_lines.append(f"**Ended:** {ended_at}")
    convo_lines.append(f"**Source:** Claude Code session `{session_id}`")
    cwd = next((e['cwd'] for e in entries if e.get('cwd')), 'unknown')
    convo_lines.append(f"**Working directory:** {cwd}")
    convo_lines.append("")

    think_lines = [
        f"# Full thought process — {title}",
        "",
        "Extended thinking and tool calls (commands run, files read/written, their "
        "output), in order. This mirrors what the Claude Code desktop app shows "
        "when you expand a collapsed \"Ran N commands\" block. See conversation.md "
        "for just the plain-language back-and-forth.",
        "",
    ]

    image_count = 0
    tool_use_count = 0
    models = set()

    for e in msg_entries:
        msg = e['message']
        role = msg.get('role')
        label = 'User' if role == 'user' else 'Assistant'
        ts = fmt_minute(e.get('timestamp'))
        content = msg.get('content')

        header = f"## [Context summary from earlier session] — {ts}" if e.get('isCompactSummary') else f"## {label} — {ts}"
        convo_lines.append(header)
        convo_lines.append("")
        text = text_from_content(content)
        if text.strip():
            convo_lines.append(text)
        convo_lines.append("")

        think_lines.append(f"## {label} — {ts}")
        think_lines.append("")

        if isinstance(content, list):
            for c in content:
                if not isinstance(c, dict):
                    continue
                ctype = c.get('type')
                if ctype == 'thinking':
                    think_lines.append("**Thinking:**")
                    think_lines.append("")
                    think_lines.append(c.get('thinking', ''))
                    think_lines.append("")
                elif ctype == 'tool_use':
                    tool_use_count += 1
                    think_lines.append(f"**Tool call: {c.get('name')}**")
                    think_lines.append("```json")
                    think_lines.append(json.dumps(c.get('input', {}), indent=2)[:4000])
                    think_lines.append("```")
                    think_lines.append("")
                elif ctype == 'tool_result':
                    result_text = tool_result_text(c.get('content'))
                    if len(result_text) > 4000:
                        result_text = result_text[:4000] + "\n... [truncated]"
                    think_lines.append("**Tool result:**")
                    think_lines.append("```")
                    think_lines.append(result_text)
                    think_lines.append("```")
                    think_lines.append("")
                elif ctype == 'image':
                    image_count += 1
                    src = c.get('source', {})
                    data = src.get('data')
                    media_type = src.get('media_type', 'image/png')
                    ext = media_type.split('/')[-1]
                    if data:
                        adir = folder / "attachments"
                        adir.mkdir(exist_ok=True)
                        img_name = f"image_{image_count:03d}.{ext}"
                        (adir / img_name).write_bytes(base64.b64decode(data))
                        think_lines.append(f"*[image saved to attachments/{img_name}]*")
                        think_lines.append("")
                # 'text' blocks are already captured in conversation.md

        think_lines.append("")

        if isinstance(msg.get('model'), str):
            models.add(msg['model'])

    (folder / "conversation.md").write_text("\n".join(convo_lines), encoding='utf-8')
    (folder / "thinking.md").write_text("\n".join(think_lines), encoding='utf-8')

    metadata = {
        "title": title,
        "session_id": session_id,
        "source_file": str(jsonl_path),
        "started_at": started_at,
        "ended_at": ended_at,
        "message_count": len(msg_entries),
        "tool_call_count": tool_use_count,
        "image_attachment_count": image_count,
        "models": sorted(models),
    }
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding='utf-8')

    return folder


DEFAULT_PROJECTS_ROOT = Path.home() / ".claude" / "projects"


def find_all_sessions(projects_root: Path) -> list:
    """Scan every session transcript under ~/.claude/projects/*/*.jsonl.

    Claude Code sanitizes the working directory into the project folder name
    (e.g. ~/dev becomes -home-nickbenes-dev), which isn't reliably reversible,
    so we read each session's own 'cwd' field instead of guessing from the
    folder name.
    """
    sessions = []
    for jsonl_path in sorted(projects_root.glob("*/*.jsonl")):
        try:
            entries = load_entries(jsonl_path)
        except (json.JSONDecodeError, OSError):
            continue

        msg_entries = [e for e in entries if e.get('type') in ('user', 'assistant')]
        if not msg_entries:
            continue

        timestamps = [e['timestamp'] for e in msg_entries if e.get('timestamp')]
        started_at = min(timestamps) if timestamps else None
        ended_at = max(timestamps) if timestamps else None
        cwd = next((e['cwd'] for e in entries if e.get('cwd')), '?')

        title = resolve_title(entries, msg_entries, jsonl_path.stem)

        sessions.append({
            "path": jsonl_path,
            "session_id": jsonl_path.stem,
            "title": title,
            "cwd": cwd,
            "started_at": started_at,
            "ended_at": ended_at,
            "message_count": len(msg_entries),
        })

    sessions.sort(key=lambda s: s['ended_at'] or '', reverse=True)
    return sessions


def print_session_list(sessions: list):
    for s in sessions:
        when = fmt_minute(s['ended_at']) if s['ended_at'] else 'unknown'
        print(f"{s['session_id'][:8]}  {when}  ({s['message_count']:>4} msgs)  {s['cwd']}")
        print(f"          {s['title']}")


def main():
    parser = argparse.ArgumentParser(description="Archive a Claude Code session transcript")
    parser.add_argument("--session", type=Path, help="Path to a specific session's .jsonl transcript file")
    parser.add_argument("--title", type=str, help="Find a session by a substring of its title (case-insensitive) instead of passing --session directly")
    parser.add_argument("--list", action="store_true", help="List all discoverable sessions (optionally narrowed by --title) and exit, without archiving anything")
    parser.add_argument("--projects-root", type=Path, default=DEFAULT_PROJECTS_ROOT, help="Override the Claude Code projects directory (default: ~/.claude/projects)")
    parser.add_argument("--output", type=Path, help="Archive root directory to write the session folder into (required unless --list)")
    args = parser.parse_args()

    if args.list:
        sessions = find_all_sessions(args.projects_root)
        if args.title:
            sessions = [s for s in sessions if args.title.lower() in s['title'].lower()]
        if not sessions:
            print("No matching sessions found.")
            return
        print_session_list(sessions)
        return

    session_path = args.session
    if session_path is None:
        if not args.title:
            parser.error("Pass --session <path>, --title <substring>, or --list")
        matches = [s for s in find_all_sessions(args.projects_root) if args.title.lower() in s['title'].lower()]
        if not matches:
            parser.error(f"No session title matched {args.title!r}. Try --list --title {args.title!r} first.")
        if len(matches) > 1:
            print(f"{len(matches)} sessions matched {args.title!r} — pick one with --session:")
            print_session_list(matches)
            raise SystemExit(1)
        session_path = matches[0]['path']

    if args.output is None:
        parser.error("--output is required (unless using --list)")

    folder = build_archive(session_path, args.output)
    print(f"Archived to: {folder}")


if __name__ == "__main__":
    main()
