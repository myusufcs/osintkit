"""Pipeline scan bersama: dipakai oleh CLI dan Web UI."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from . import detect, registry, report
from .runner import run_modules


def prepare_target(target: str) -> tuple[str, set[str]]:
    p = Path(target).expanduser()
    if p.is_file():
        return str(p), {"image"}
    return detect.normalize(target)


def scan(target: str, *, only=None, skip=None, active: bool = False,
         workers: int = 6, outdir: str | Path | None = None,
         formats=None, progress=None) -> dict:
    """Jalankan recon dan (opsional) tulis laporan. Kembalikan dict hasil."""
    core, kinds = prepare_target(target)
    registry.load_all()
    classes = registry.select(kinds, only, skip)

    meta = {
        "target": core,
        "original": target,
        "kinds": sorted(kinds),
        "started": dt.datetime.now().isoformat(timespec="seconds"),
        "active": active,
    }
    ctx = {"domain": detect.domain_of(core, kinds), "active": active,
           "target": core, "kinds": kinds}

    findings, status = run_modules(classes, core, kinds, ctx,
                                   workers=workers, progress=progress)

    files: list[str] = []
    if outdir:
        files = [str(p) for p in report.write(Path(outdir).expanduser(), meta,
                                              findings, status,
                                              formats or ["md", "html", "json"])]
    return {"meta": meta, "findings": findings, "status": status, "files": files,
            "modules": [c.NAME for c in classes]}
