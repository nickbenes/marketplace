#!/usr/bin/env python3
"""
Claude.ai chat archiver — API-based rewrite.

Uses the internal Claude.ai JSON API (the same one the web client calls) instead of
scraping rendered pages. Runs the actual HTTP fetch() calls from inside your logged-in
Chrome tab via browser-harness's CDP `js()` bridge — Cloudflare blocks raw out-of-browser
requests even with a valid session cookie, but same-origin fetch() from the page itself
passes through fine.

No ai-chat-exporter extension dependency. No per-chat page navigation (fixes the
TimeoutError flakiness from the old script). Full pagination (fixes the 31-vs-125 chat
undercount). Real created_at timestamps from the API (fixes "undated_" folders).
"""

import base64
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


def run_js(expression: str, timeout: int = 60) -> str:
    """Execute a JS expression in the user's logged-in Chrome tab via browser-harness.

    The expression is base64-encoded before being handed to the subprocess so that
    backticks, quotes, and template-literal `${...}` interpolations in the JS (or in
    chat message text embedded in the JS) can never collide with Python's own string
    delimiters.
    """
    encoded = base64.b64encode(expression.encode("utf-8")).decode("ascii")
    code = f"""
import base64
expr = base64.b64decode("{encoded}").decode("utf-8")
result = js(expr)
print(result)
"""
    result = subprocess.run(
        ["browser-harness"], input=code, capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        raise RuntimeError(f"browser-harness failed: {result.stderr}")
    return result.stdout.strip()


def get_org_id() -> str:
    out = run_js(
        "document.cookie.split('; ').find(c => c.startsWith('lastActiveOrg=')).split('=')[1]"
    )
    return out.strip()


def list_all_chats(org_id: str) -> List[Dict]:
    """Fetch the complete, paginated list of conversations."""
    js_code = f"""
(async () => {{
    let all = [];
    let offset = 0;
    const limit = 100;
    while (true) {{
        const resp = await fetch(`/api/organizations/{org_id}/chat_conversations?limit=${{limit}}&offset=${{offset}}`, {{
            headers: {{"Accept": "application/json"}}
        }});
        const data = await resp.json();
        all = all.concat(data.map(c => ({{uuid: c.uuid, name: c.name, created_at: c.created_at, updated_at: c.updated_at}})));
        if (data.length < limit) break;
        offset += limit;
    }}
    return JSON.stringify(all);
}})()
"""
    out = run_js(js_code, timeout=60)
    return json.loads(out)


def fetch_chat_detail(org_id: str, chat_uuid: str, timeout: int = 120) -> Dict:
    """Fetch one conversation with full message tree, clean markdown, and inline
    attachment/artifact content (text extracted inline, binary files as base64)."""
    js_code = f"""
(async () => {{
    async function fetchBase64(path) {{
        const r = await fetch(path);
        if (!r.ok) return null;
        const buf = await r.arrayBuffer();
        const bytes = new Uint8Array(buf);
        let binary = '';
        for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
        return {{ b64: btoa(binary), contentType: r.headers.get('content-type') }};
    }}

    const resp = await fetch(`/api/organizations/{org_id}/chat_conversations/{chat_uuid}?tree=True&rendering_mode=raw&render_all_tools=true`, {{
        headers: {{"Accept": "application/json"}}
    }});
    const data = await resp.json();
    const lines = [];
    lines.push(`# ${{data.name || 'Untitled'}}`);
    lines.push('');
    lines.push(`**Created:** ${{data.created_at}}`);
    lines.push(`**Updated:** ${{data.updated_at}}`);
    lines.push(`**URL:** https://claude.ai/chat/${{data.uuid}}`);
    lines.push('');
    const attachments = [];
    const files = [];
    for (const m of data.chat_messages) {{
        lines.push(`## ${{m.sender === 'human' ? 'User' : 'Assistant'}} — ${{m.created_at}}`);
        lines.push('');
        lines.push(m.text || '');
        lines.push('');
        for (const f of (m.files || [])) {{
            const fuuid = f.file_uuid || f.uuid;
            const dl = await fetchBase64(`/api/{org_id}/files/${{fuuid}}/preview`);
            files.push({{
                uuid: fuuid, file_name: f.file_name, kind: f.file_kind,
                created_at: f.created_at,
                content_b64: dl ? dl.b64 : null,
                content_type: dl ? dl.contentType : null
            }});
        }}
        for (const a of (m.attachments || [])) {{
            attachments.push({{
                uuid: a.id || a.uuid, file_name: a.file_name, file_type: a.file_type,
                extracted_content: a.extracted_content || null
            }});
        }}
    }}
    return JSON.stringify({{
        uuid: data.uuid,
        name: data.name,
        created_at: data.created_at,
        updated_at: data.updated_at,
        markdown: lines.join('\\n'),
        attachments: attachments,
        files: files
    }});
}})()
"""
    out = run_js(js_code, timeout=timeout)
    return json.loads(out)


def fetch_org_memory(org_id: str) -> Optional[str]:
    js_code = f"""
(async () => {{
    const r = await fetch(`/api/organizations/{org_id}/memory`, {{headers: {{"Accept": "application/json"}}}});
    if (!r.ok) return JSON.stringify(null);
    const d = await r.json();
    return JSON.stringify(d.memory || null);
}})()
"""
    out = run_js(js_code, timeout=30)
    return json.loads(out)


def fetch_all_projects(org_id: str) -> List[Dict]:
    """Fetch project list plus each project's docs (knowledge base files)."""
    js_code = f"""
(async () => {{
    const rp = await fetch(`/api/organizations/{org_id}/projects?limit=200`, {{headers: {{"Accept": "application/json"}}}});
    const projects = await rp.json();
    const out = [];
    for (const p of projects) {{
        const rd = await fetch(`/api/organizations/{org_id}/projects/${{p.uuid}}/docs`, {{headers: {{"Accept": "application/json"}}}});
        const docs = rd.ok ? await rd.json() : [];
        out.push({{
            uuid: p.uuid,
            name: p.name,
            description: p.description,
            prompt_template: p.prompt_template,
            created_at: p.created_at,
            updated_at: p.updated_at,
            docs: docs.map(d => ({{file_name: d.file_name, content: d.content, created_at: d.created_at}}))
        }});
    }}
    return JSON.stringify(out);
}})()
"""
    out = run_js(js_code, timeout=120)
    return json.loads(out)


def sanitize_name(name: str, max_len: int = 80) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name or 'untitled')
    name = re.sub(r'\s+', '_', name.strip())
    name = name.rstrip('._- ')
    return name[:max_len] if name else 'untitled'


def parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except ValueError:
        return None


def ext_from_content_type(content_type: Optional[str]) -> str:
    mapping = {
        "image/png": ".png", "image/webp": ".webp", "image/jpeg": ".jpg",
        "application/pdf": ".pdf", "text/plain": ".txt", "text/html": ".html",
    }
    return mapping.get(content_type or "", ".bin")


def save_chat_files(folder: Path, detail: Dict):
    attachments = detail.get('attachments', [])
    files = detail.get('files', [])

    if attachments:
        adir = folder / "attachments"
        adir.mkdir(exist_ok=True)
        for a in attachments:
            content = a.get('extracted_content')
            if content is None:
                continue
            name = sanitize_name(a.get('file_name') or a['uuid'], 60)
            (adir / f"{name}.txt").write_text(content, encoding='utf-8')

    if files:
        fdir = folder / "files"
        fdir.mkdir(exist_ok=True)
        for f in files:
            b64 = f.get('content_b64')
            if not b64:
                continue
            name = sanitize_name(f.get('file_name') or f['uuid'], 60)
            ext = ext_from_content_type(f.get('content_type'))
            if not name.endswith(ext):
                name += ext
            (fdir / name).write_bytes(base64.b64decode(b64))


def archive_projects(archive_root: Path, org_id: str):
    print("Fetching projects...")
    projects = fetch_all_projects(org_id)
    print(f"Found {len(projects)} projects")

    pdir = archive_root / "_projects"
    pdir.mkdir(parents=True, exist_ok=True)
    for p in projects:
        pfolder = pdir / sanitize_name(p['name'], 60)
        pfolder.mkdir(parents=True, exist_ok=True)
        metadata = {k: v for k, v in p.items() if k != 'docs'}
        (pfolder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        for doc in p.get('docs', []):
            name = sanitize_name(doc.get('file_name') or 'doc', 60)
            if not name.lower().endswith(('.html', '.htm', '.txt', '.md')):
                name += '.html'
            (pfolder / name).write_text(doc.get('content') or '', encoding='utf-8')


def save_one_chat(archive_root: Path, org_id: str, chat: Dict) -> Optional[Path]:
    """Fetch and save a single chat, with retry-on-timeout. Returns the folder
    written, or None if all attempts failed."""
    title = chat['name'] or 'untitled'
    detail = None
    last_err = None
    for attempt in range(3):
        try:
            detail = fetch_chat_detail(org_id, chat['uuid'], timeout=120 + attempt * 60)
            break
        except Exception as e:
            last_err = e
    if detail is None:
        print(f"  FAILED after 3 attempts: {last_err}")
        return None

    created = parse_iso(detail.get('created_at'))
    safe_title = sanitize_name(detail.get('name') or title)
    prefix = created.strftime('%Y%m%d_%H%M%S') if created else 'undated'
    folder = archive_root / f"{prefix}_{safe_title}"
    folder.mkdir(parents=True, exist_ok=True)

    (folder / "conversation.md").write_text(detail['markdown'], encoding='utf-8')
    save_chat_files(folder, detail)

    metadata = {
        "title": detail.get('name'),
        "chat_id": detail.get('uuid'),
        "url": f"https://claude.ai/chat/{detail.get('uuid')}",
        "created_at": detail.get('created_at'),
        "updated_at": detail.get('updated_at'),
        "attachments": [{"file_name": a.get("file_name"), "file_type": a.get("file_type")} for a in detail.get('attachments', [])],
        "files": [{"file_name": f.get("file_name"), "kind": f.get("kind"), "downloaded": bool(f.get("content_b64"))} for f in detail.get('files', [])],
    }
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    return folder


def archive_all(archive_root: Path, max_chats: Optional[int] = None):
    archive_root.mkdir(parents=True, exist_ok=True)

    print("Fetching org id...")
    org_id = get_org_id()
    print(f"Org: {org_id}")

    print("Fetching general memory...")
    memory = fetch_org_memory(org_id)
    if memory:
        (archive_root / "_memory.md").write_text(memory, encoding='utf-8')

    archive_projects(archive_root, org_id)

    print("Fetching full paginated chat list...")
    chats = list_all_chats(org_id)
    print(f"Found {len(chats)} total chats")

    if max_chats:
        chats = chats[:max_chats]

    successful, failed = 0, 0
    for i, chat in enumerate(chats, 1):
        print(f"[{i}/{len(chats)}] {chat['name'] or 'untitled'}")
        folder = save_one_chat(archive_root, org_id, chat)
        if folder is None:
            failed += 1
        else:
            successful += 1
        if i % 5 == 0:
            print(f"  -- progress: {successful} ok, {failed} failed --")

    print(f"\nDone. {successful} succeeded, {failed} failed. Archive at {archive_root}")


def archive_by_title(archive_root: Path, title_substr: str) -> Path:
    """Find a chat by a substring of its title and archive just that one."""
    archive_root.mkdir(parents=True, exist_ok=True)

    print("Fetching org id...")
    org_id = get_org_id()

    print("Fetching full paginated chat list...")
    chats = list_all_chats(org_id)

    needle = title_substr.lower()
    matches = [c for c in chats if needle in (c.get('name') or '').lower()]

    if not matches:
        raise SystemExit(f"No chat title matched {title_substr!r} out of {len(chats)} chats. "
                          f"Try a shorter substring, or check the exact title on claude.ai.")
    if len(matches) > 1:
        print(f"{len(matches)} chats matched {title_substr!r}:")
        for m in matches:
            print(f"  {m['uuid'][:8]}  {m.get('created_at', '?')}  {m['name']}")
        raise SystemExit("Narrow the --title substring so exactly one chat matches.")

    chat = matches[0]
    print(f"Archiving: {chat['name']}")
    folder = save_one_chat(archive_root, org_id, chat)
    if folder is None:
        raise SystemExit("Archive failed after 3 attempts — see error above.")
    print(f"Archived to: {folder}")
    return folder


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Archive Claude.ai chats via internal API")
    parser.add_argument("--output", type=Path, default=Path.home() / "claude-archive",
                         help="Directory to write the archive to (default: ~/claude-archive)")
    parser.add_argument("--max", type=int, default=None, help="Only process the first N chats")
    parser.add_argument("--title", type=str, default=None,
                         help="Archive only the one chat whose title contains this substring "
                              "(case-insensitive), instead of the full account")
    args = parser.parse_args()

    if args.title:
        archive_by_title(args.output, args.title)
    else:
        archive_all(args.output, max_chats=args.max)


if __name__ == "__main__":
    main()
