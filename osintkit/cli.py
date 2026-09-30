"""CLI osintkit. Contoh:

    python3 -m osintkit scan example.com
    python3 -m osintkit scan "user@example.com" --format md,html
    python3 -m osintkit scan johndoe --only username,github_user
    python3 -m osintkit scan ./foto.jpg
    python3 -m osintkit web --port 8787
    python3 -m osintkit modules
"""
from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from .core import registry
from .core.pipeline import scan

DEFAULT_FORMATS = ["md", "html", "json"]


def _split(val: str | None) -> list[str] | None:
    return [s.strip() for s in val.split(",") if s.strip()] if val else None


def cmd_modules(_args) -> int:
    registry.load_all()
    rows = registry.describe()
    print(f"{'MODUL':<18}{'TARGET':<26}{'STATUS':<11}DESKRIPSI")
    for name, accepts, desc, missing in rows:
        print(f"{name:<18}{accepts:<26}{'butuh key' if missing else 'gratis':<11}{desc}")
    gr = sum(1 for r in rows if not r[3])
    print(f"\nTotal {len(rows)} modul — {gr} gratis tanpa API key, {len(rows) - gr} opsional (butuh key).")
    return 0


def cmd_scan(args) -> int:
    target = args.target.strip()
    if not target:
        print("target kosong", file=sys.stderr)
        return 2

    def progress(name: str, st: dict) -> None:
        if args.quiet:
            return
        print(f"  [{st['state']:>5}] {name:<18} {st.get('count', 0):>4} temuan "
              f"{st.get('detail', '')}", file=sys.stderr)

    res = scan(target,
               only=_split(args.only),
               skip=_split(args.skip),
               active=args.active,
               workers=args.workers,
               outdir=Path(args.out).expanduser(),
               formats=_split(args.format) or DEFAULT_FORMATS,
               progress=progress)

    meta = res["meta"]
    print("-" * 60, file=sys.stderr)
    print(f"target : {meta['target']}", file=sys.stderr)
    print(f"tipe   : {', '.join(meta['kinds'])}", file=sys.stderr)
    print(f"modul  : {len(res['modules'])}", file=sys.stderr)
    print(f"temuan : {len(res['findings'])}", file=sys.stderr)
    for p in res["files"]:
        print(f"  -> {p}", file=sys.stderr)

    if args.open:
        for p in res["files"]:
            if p.endswith(".html"):
                webbrowser.open(Path(p).as_uri())
    return 0


def cmd_web(args) -> int:
    from .webui import serve
    return serve(host=args.host, port=args.port, open_browser=args.open)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="osintkit",
        description="Toolkit OSINT all-in-one (hanya untuk aset sendiri / engagement berizin)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="jalankan recon untuk satu target")
    s.add_argument("target", help="domain / url / ip / email / username / nomor / file gambar")
    s.add_argument("--only", help="modul yang dijalankan (dipisah koma)")
    s.add_argument("--skip", help="modul yang dilewati (dipisah koma)")
    s.add_argument("--active", action="store_true",
                   help="izinkan modul yang menyentuh target langsung")
    s.add_argument("--out", default="~/osintkit-reports", help="folder laporan")
    s.add_argument("--format", help="md,html,json (default: ketiganya)")
    s.add_argument("--workers", type=int, default=6)
    s.add_argument("--quiet", action="store_true")
    s.add_argument("--open", action="store_true", help="buka laporan HTML di browser")

    w = sub.add_parser("web", help="jalankan Web UI")
    w.add_argument("--host", default="127.0.0.1")
    w.add_argument("--port", type=int, default=8787)
    w.add_argument("--open", action="store_true", help="buka browser otomatis")

    sub.add_parser("modules", help="daftar modul yang tersedia")

    args = ap.parse_args(argv)
    if args.cmd == "modules":
        return cmd_modules(args)
    if args.cmd == "web":
        return cmd_web(args)
    return cmd_scan(args)


if __name__ == "__main__":
    raise SystemExit(main())
