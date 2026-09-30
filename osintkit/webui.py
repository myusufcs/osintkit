"""Web UI osintkit — stdlib http.server, tanpa dependensi tambahan.

    python3 -m osintkit web --port 8787
"""
from __future__ import annotations

import html
import json
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .core import registry
from .core.pipeline import scan

OUTROOT = Path.home() / "osintkit-reports" / "_web"
JOBS: dict[str, dict] = {}
LOCK = threading.Lock()

CSS = """
:root{color-scheme:dark}
*{box-sizing:border-box}
body{font:14px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#0f1115;color:#e6e6e6}
a{color:#7dd3fc}
header{padding:18px 26px;background:#161a21;border-bottom:1px solid #242a33;display:flex;align-items:baseline;gap:14px}
header h1{margin:0;font-size:18px}
header .tag{color:#8b93a1;font-size:12px}
main{padding:22px 26px;max-width:1100px}
form{background:#161a21;border:1px solid #242a33;border-radius:10px;padding:18px;margin-bottom:22px}
label{display:block;font-size:12px;color:#8b93a1;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
input[type=text]{width:100%;padding:11px 12px;background:#0f1115;border:1px solid #2c3542;border-radius:7px;color:#e6e6e6;font-size:14px}
input[type=text]:focus{outline:none;border-color:#3b82f6}
.row{display:flex;gap:12px;margin-top:12px;flex-wrap:wrap;align-items:center}
button{padding:10px 18px;border-radius:7px;border:1px solid #2c3542;background:#1d4ed8;color:#fff;font-weight:600;cursor:pointer}
button:hover{background:#2563eb}
button.ghost{background:transparent;color:#c9d1d9}
.chip{display:inline-block;padding:3px 9px;border-radius:999px;background:#1c2430;border:1px solid #2c3542;font-size:12px;margin:2px 4px 2px 0}
h2{font-size:15px;color:#a7f3d0;margin:20px 0 8px}
table{width:100%;border-collapse:collapse;margin-bottom:10px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #242a33;vertical-align:top}
th{color:#8b93a1;font-size:11px;text-transform:uppercase}
.st-ok{color:#86efac}.st-skip{color:#fbbf24}.st-error{color:#f87171}
.meta{color:#8b93a1;font-size:12px}
.big{font-size:26px;font-weight:700;color:#a7f3d0}
.pulse{animation:p 1.2s infinite}@keyframes p{50%{opacity:.35}}
"""


def page(title: str, body: str, refresh: int | None = None) -> bytes:
    meta = f'<meta http-equiv="refresh" content="{refresh}">' if refresh else ""
    return f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">{meta}
<title>{html.escape(title)}</title><style>{CSS}</style></head>
<body><header><h1>⛩️ osintkit</h1><span class="tag">OSINT all-in-one — untuk aset sendiri / engagement berizin</span></header>
<main>{body}</main></body></html>""".encode()


def index_body() -> str:
    registry.load_all()
    chips = "".join(
        f'<span class="chip" title="{html.escape(desc)}">{html.escape(name)}'
        f'{" ⚠" if missing else ""}</span>'
        for name, _acc, desc, missing in registry.describe())
    return f"""<form method="post" action="/scan">
  <label for="target">Target</label>
  <input type="text" id="target" name="target" autofocus
         placeholder="example.com · 8.8.8.8 · nama@email.com · username · +62812xxx · /path/gambar.jpg">
  <div class="row">
    <input type="text" name="only" placeholder="modul tertentu (opsional, mis: dns,tls,http)" style="flex:1">
    <label style="margin:0"><input type="checkbox" name="active" value="1"> aktif</label>
    <button type="submit">Scan</button>
  </div>
</form>
<h2>Modul tersedia ({len(registry.describe())})</h2>
<p class="meta">⚠ = butuh API key opsional (otomatis dilewati kalau tidak ada).</p>
<div>{chips}</div>"""


def job_body(job: dict) -> tuple[str, int | None]:
    if job["state"] == "running":
        logs = "".join(f'<div class="meta">[{html.escape(s["state"])}] '
                       f'{html.escape(s["module"])} — {s.get("count", 0)} temuan</div>'
                       for s in job["status"])
        return (f'<p class="big pulse">Sedang memindai…</p>'
                f'<p class="meta">target: {html.escape(job["target"])}</p>{logs}'), 2
    if job["state"] == "error":
        return (f'<p class="big" style="color:#f87171">Gagal</p>'
                f'<pre>{html.escape(job.get("error", ""))}</pre>'
                f'<p><a href="/">← kembali</a></p>'), None

    st_rows = "".join(
        f'<tr><td>{html.escape(s["module"])}</td><td class="st-{s["state"]}">{s["state"]}</td>'
        f'<td>{s.get("count", 0)}</td><td class="meta">{html.escape(str(s.get("detail") or ""))[:120]}</td></tr>'
        for s in job["status"])
    return (f'<p class="big">{len(job["findings"])} temuan</p>'
            f'<p class="meta">target: {html.escape(job["target"])} · '
            f'{html.escape(job["started"])} · {len(job["modules"])} modul</p>'
            f'<div class="row"><a href="/report/{job["id"]}"><button>Lihat laporan lengkap</button></a>'
            f'<a href="/"><button class="ghost">Scan lagi</button></a></div>'
            f'<h2>Status modul</h2><table><thead><tr><th>Modul</th><th>Status</th>'
            f'<th>Temuan</th><th>Catatan</th></tr></thead><tbody>{st_rows}</tbody></table>'), None


def _run_job(job_id: str, target: str, only: list[str] | None, active: bool) -> None:
    job = JOBS[job_id]

    def progress(name: str, st: dict) -> None:
        job["status"].append(st)

    try:
        res = scan(target, only=only, active=active, workers=6,
                   outdir=OUTROOT / job_id, formats=["html", "json", "md"],
                   progress=progress)
        with LOCK:
            job.update(state="done", findings=res["findings"],
                       status=res["status"], modules=res["modules"],
                       files=res["files"])
    except Exception as e:                          # noqa: BLE001
        with LOCK:
            job.update(state="error", error=f"{type(e).__name__}: {e}")


class Handler(BaseHTTPRequestHandler):
    server_version = "osintkit"

    def log_message(self, fmt, *args):              # ringkas
        print(f"[web] {self.address_string()} {fmt % args}")

    def _send(self, body: bytes, code: int = 200, ctype: str = "text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):                                # noqa: N802
        u = urlparse(self.path)
        p = u.path.rstrip("/") or "/"

        if p == "/":
            return self._send(page("osintkit", index_body()))
        if p == "/api/modules":
            registry.load_all()
            data = [{"module": n, "accepts": a, "desc": d, "needs_key": m}
                    for n, a, d, m in registry.describe()]
            return self._send(json.dumps(data, indent=2).encode(), ctype="application/json")
        if p == "/api/scan":
            q = parse_qs(u.query)
            target = (q.get("target") or [""])[0].strip()
            if not target:
                return self._send(b'{"error":"target kosong"}', 400, "application/json")
            only = [s for s in (q.get("only") or [""])[0].split(",") if s]
            res = scan(target, only=only or None,
                       active=bool(q.get("active")), outdir=OUTROOT / "_api")
            return self._send(json.dumps(
                {"meta": res["meta"], "files": res["files"],
                 "modules": res["status"], "sections_count": len(res["findings"]),
                 "findings": res["findings"]}, indent=2, default=str).encode(),
                ctype="application/json")
        if p.startswith("/job/"):
            jid = p.split("/")[-1]
            job = JOBS.get(jid)
            if not job:
                return self._send(page("404", "<p>Job tidak ditemukan. <a href='/'>kembali</a></p>"), 404)
            body, refresh = job_body(job)
            return self._send(page(f"scan {jid}", body, refresh))
        if p.startswith("/report/"):
            jid = p.split("/")[-1]
            job = JOBS.get(jid)
            if not job or not job.get("files"):
                return self._send(page("404", "<p>Laporan belum siap.</p>"), 404)
            for f in job["files"]:
                if f.endswith(".html"):
                    return self._send(Path(f).read_bytes())
            return self._send(page("404", "<p>Tidak ada laporan HTML.</p>"), 404)
        return self._send(page("404", "<p>Tidak ditemukan. <a href='/'>kembali</a></p>"), 404)

    def do_POST(self):                               # noqa: N802
        if urlparse(self.path).path.rstrip("/") != "/scan":
            return self._send(page("404", "<p>Tidak ditemukan.</p>"), 404)
        n = int(self.headers.get("Content-Length") or 0)
        form = parse_qs(self.rfile.read(n).decode("utf-8", "replace"))
        target = (form.get("target") or [""])[0].strip()
        if not target:
            return self._send(page("osintkit", "<p>Target kosong.</p><p><a href='/'>← kembali</a></p>"), 400)
        only = [s for s in (form.get("only") or [""])[0].split(",") if s]
        active = bool(form.get("active"))

        jid = uuid.uuid4().hex[:12]
        JOBS[jid] = {"id": jid, "target": target, "state": "running",
                     "status": [], "findings": [], "modules": [],
                     "files": [], "started": "", "error": ""}
        threading.Thread(target=_run_job, args=(jid, target, only or None, active),
                         daemon=True).start()
        self.send_response(303)
        self.send_header("Location", f"/job/{jid}")
        self.send_header("Content-Length", "0")
        self.end_headers()


def serve(host: str = "127.0.0.1", port: int = 8787, open_browser: bool = False) -> int:
    OUTROOT.mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/"
    print(f"osintkit web → {url}  (Ctrl+C untuk berhenti)", flush=True)
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nberhenti.")
    finally:
        srv.server_close()
    return 0
