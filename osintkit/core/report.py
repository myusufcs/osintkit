"""Penyusun laporan: Markdown, HTML, JSON."""
from __future__ import annotations

import datetime as dt
import html
import json
import re
from collections import defaultdict
from pathlib import Path


def _esc(v) -> str:
    if v is None:
        return ""
    return str(v)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def group(findings: list[dict]) -> dict[str, list[dict]]:
    g: dict[str, list[dict]] = defaultdict(list)
    for f in findings:
        g[f.get("section") or "Umum"].append(f)
    return dict(sorted(g.items()))


def to_json(meta: dict, findings: list[dict], status: list[dict]) -> str:
    return json.dumps({
        "meta": meta,
        "modules": status,
        "sections": group(findings),
        "findings": findings,
    }, indent=2, ensure_ascii=False, default=str)


def to_markdown(meta: dict, findings: list[dict], status: list[dict]) -> str:
    L: list[str] = []
    L.append(f"# Laporan OSINT — `{meta['target']}`")
    L.append("")
    L.append(f"- **Tipe target**: {', '.join(sorted(meta['kinds']))}")
    L.append(f"- **Waktu**: {meta['started']}")
    L.append(f"- **Modul jalan**: {sum(1 for s in status if s['state'] == 'ok')}"
             f" | dilewati: {sum(1 for s in status if s['state'] == 'skip')}"
             f" | error: {sum(1 for s in status if s['state'] == 'error')}")
    L.append("")

    g = group(findings)
    if not g:
        L.append("_Tidak ada temuan._")
    for section, items in g.items():
        L.append(f"## {section}")
        L.append("")
        L.append("| Key | Value | Sumber |")
        L.append("|---|---|---|")
        for it in items:
            val = _esc(it.get("value")).replace("\n", " ").replace("|", "\\|")
            src = _esc(it.get("source"))
            if src.startswith("http"):
                src = f"[link]({src})"
            L.append(f"| {_esc(it.get('key'))} | {val} | {src} |")
        L.append("")

    L.append("## Status modul")
    L.append("")
    L.append("| Modul | Status | Jumlah | Catatan |")
    L.append("|---|---|---|---|")
    for s in status:
        L.append(f"| {s['module']} | {s['state']} | {s.get('count', 0)} | "
                 f"{_esc(s.get('detail'))[:120]} |")
    L.append("")
    L.append("> Hasil OSINT hanya untuk aset yang Anda miliki / engagement berizin.")
    return "\n".join(L)


def to_html(meta: dict, findings: list[dict], status: list[dict]) -> str:
    g = group(findings)
    nav = "".join(f"<a href='#{_slug(s)}'>{html.escape(s)}</a>" for s in g)
    body = []
    for section, items in g.items():
        rows = "".join(
            "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(_esc(it.get("key"))),
                html.escape(_esc(it.get("value"))),
                (f"<a href='{html.escape(_esc(it.get('source')))}' target='_blank'>link</a>"
                 if _esc(it.get("source")).startswith("http")
                 else html.escape(_esc(it.get("source")))),
            ) for it in items)
        body.append(f"<h2 id='{_slug(section)}'>{html.escape(section)}</h2>"
                    f"<table><thead><tr><th>Key</th><th>Value</th><th>Sumber</th></tr></thead>"
                    f"<tbody>{rows}</tbody></table>")
    st_rows = "".join(
        f"<tr><td>{html.escape(s['module'])}</td><td class='st-{s['state']}'>{s['state']}</td>"
        f"<td>{s.get('count', 0)}</td><td>{html.escape(_esc(s.get('detail'))[:160])}</td></tr>"
        for s in status)
    return f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8">
<title>OSINT — {html.escape(meta['target'])}</title>
<style>
 body{{font:14px/1.5 system-ui,sans-serif;margin:0;background:#0f1115;color:#e6e6e6}}
 header{{padding:20px 28px;background:#161a21;border-bottom:1px solid #242a33}}
 h1{{margin:0 0 6px;font-size:20px}} .meta{{color:#8b93a1;font-size:13px}}
 nav{{display:flex;gap:12px;flex-wrap:wrap;margin-top:12px}}
 nav a{{color:#7dd3fc;text-decoration:none;font-size:13px}}
 main{{padding:20px 28px}} h2{{font-size:15px;margin:22px 0 8px;color:#a7f3d0}}
 table{{width:100%;border-collapse:collapse;margin-bottom:8px}}
 th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid #242a33;vertical-align:top}}
 th{{color:#8b93a1;font-weight:600;font-size:12px;text-transform:uppercase}}
 a{{color:#7dd3fc}} .st-ok{{color:#86efac}} .st-skip{{color:#fbbf24}} .st-error{{color:#f87171}}
</style></head><body>
<header><h1>Laporan OSINT — {html.escape(meta['target'])}</h1>
<div class="meta">Tipe: {', '.join(sorted(meta['kinds']))} &middot; {html.escape(meta['started'])}</div>
<nav>{nav}</nav></header>
<main>{''.join(body)}
<h2 id="status-modul">Status modul</h2>
<table><thead><tr><th>Modul</th><th>Status</th><th>Jumlah</th><th>Catatan</th></tr></thead>
<tbody>{st_rows}</tbody></table>
<p class="meta">Hasil OSINT hanya untuk aset yang Anda miliki / engagement berizin.</p>
</main></body></html>"""


def write(outdir: Path, meta: dict, findings: list[dict], status: list[dict],
          formats: list[str]) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = f"{_slug(meta['target']) or 'target'}-{stamp}"
    written: list[Path] = []
    if "json" in formats:
        p = outdir / f"{base}.json"
        p.write_text(to_json(meta, findings, status), encoding="utf-8")
        written.append(p)
    if "md" in formats:
        p = outdir / f"{base}.md"
        p.write_text(to_markdown(meta, findings, status), encoding="utf-8")
        written.append(p)
    if "html" in formats:
        p = outdir / f"{base}.html"
        p.write_text(to_html(meta, findings, status), encoding="utf-8")
        written.append(p)
    return written
