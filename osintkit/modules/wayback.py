"""Riwayat URL dari Wayback Machine (CDX API) — gratis, tanpa key."""
from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from ..core import http
from ..core.registry import Module
from . import f

MAX_SHOW = 40


class Wayback(Module):
    NAME = "wayback"
    DESC = "URL historis (Wayback Machine) + path yang sering muncul"
    ACCEPTS = {"domain", "url"}

    def run(self, target, kinds, ctx):
        dom = ctx["domain"] or target
        data = http.get_json(
            "https://web.archive.org/cdx/search/cdx",
            params={"url": f"{dom}/*", "output": "json", "limit": "800",
                    "collapse": "urlkey", "fl": "original,timestamp,statuscode,mimetype"},
            timeout=45)
        if not isinstance(data, list) or len(data) < 2:
            return [f("Wayback", "Status", "tidak ada arsip / rate-limited")]

        rows = data[1:]
        out = [f("Wayback", "Total URL terarsip (sampel)", len(rows))]
        paths = Counter()
        exts = Counter()
        for row in rows:
            url = row[0]
            p = urlparse(url)
            paths[p.path or "/"] += 1
            if "." in (p.path.rsplit("/", 1)[-1] or ""):
                exts[p.path.rsplit(".", 1)[-1].lower()] += 1

        for path, n in paths.most_common(MAX_SHOW):
            out.append(f("Wayback — path", f"{n}x", path,
                         f"https://web.archive.org/web/*/{dom}{path}"))
        for ext, n in exts.most_common(12):
            out.append(f("Wayback — ekstensi", "." + ext, n))
        for row in rows[:15]:
            out.append(f("Wayback — contoh URL", row[1], row[0], row[0]))
        return out
