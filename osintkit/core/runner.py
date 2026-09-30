"""Runner: jalankan modul paralel, tangkap error per-modul."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def run_modules(classes: list[type], target: str, kinds: set[str],
                ctx: dict, workers: int = 6, progress=None):
    """Kembalikan (findings, status) — status berisi ringkasan per modul."""
    findings: list[dict] = []
    status: list[dict] = []

    def one(cls):
        ok, reason = cls().available()
        if not ok:
            return {"module": cls.NAME, "state": "skip", "detail": reason, "count": 0}, []
        t0 = time.time()
        try:
            res = cls().run(target, kinds, ctx) or []
            for r in res:
                r.setdefault("module", cls.NAME)
            return ({"module": cls.NAME, "state": "ok", "detail": "",
                     "count": len(res), "secs": round(time.time() - t0, 2)}, res)
        except Exception as e:                       # noqa: BLE001
            return ({"module": cls.NAME, "state": "error",
                     "detail": f"{type(e).__name__}: {e}", "count": 0,
                     "secs": round(time.time() - t0, 2)}, [])

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(one, c): c for c in classes}
        for fut in as_completed(futs):
            cls = futs[fut]
            try:
                st, res = fut.result()
            except Exception as e:                   # noqa: BLE001
                st, res = ({"module": cls.NAME, "state": "error",
                            "detail": str(e), "count": 0}, [])
            findings.extend(res)
            status.append(st)
            if progress:
                progress(cls.NAME, st)

    status.sort(key=lambda s: s["module"])
    return findings, status


def collect(findings_by_module: dict) -> list[dict]:
    out = []
    for v in findings_by_module.values():
        out.extend(v)
    return out
