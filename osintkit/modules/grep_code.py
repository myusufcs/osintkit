"""Pencarian string di repositori publik (grep.app)."""
from __future__ import annotations

from ..core import http
from ..core.registry import Module
from . import f


class GrepApp(Module):
    NAME = "grepapp"
    DESC = "Cari string di GitHub/GitLab/Bitbucket (grep.app) — kebocoran kunci/kode"
    ACCEPTS = {"domain", "email", "username"}

    def run(self, target, kinds, ctx):
        d = http.get_json("https://grep.app/api/search",
                          params={"q": target}, timeout=30)
        if not isinstance(d, dict):
            return [f("Kode publik (grep.app)", "Status", "tidak ada jawaban")]

        facets = (d.get("facets") or {})
        count = (facets.get("count") or {})
        total = count.get("value") if isinstance(count, dict) else count
        out = [f("Kode publik (grep.app)", "Total hasil", total if total is not None else "?")]

        hits = ((d.get("hits") or {}).get("hits") or [])
        for h in hits[:15]:
            repo = (h.get("repo") or {}).get("raw")
            path = (h.get("path") or {}).get("raw")
            snippet = " ".join(str((h.get("content") or {}).get("snippet", ""))
                               .replace("<mark>", "").replace("</mark>", "").split())[:140]
            out.append(f("Kode publik (grep.app)", f"{repo}:{path}",
                         snippet, f"https://github.com/{repo}/blob/HEAD/{path}"))
        return out
