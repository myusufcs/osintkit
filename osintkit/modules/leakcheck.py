"""LeakCheck (API publik) — indikasi kebocoran email, tanpa API key."""
from __future__ import annotations

from ..core import http
from ..core.registry import Module
from . import f


class LeakCheck(Module):
    NAME = "leakcheck"
    DESC = "Indikasi kebocoran data untuk email (leakcheck.io, publik/gratis)"
    ACCEPTS = {"email"}

    def run(self, target, kinds, ctx):
        email = target.strip().lower()
        d = http.get_json("https://leakcheck.io/api/public",
                          params={"check": email}, timeout=25)
        if not isinstance(d, dict):
            return [f("Kebocoran (leakcheck)", "Status", "tidak ada jawaban")]
        if not d.get("success"):
            return [f("Kebocoran (leakcheck)", "Status",
                      d.get("error") or d.get("reason") or "gagal")]
        if not d.get("found"):
            return [f("Kebocoran (leakcheck)", email, "tidak ditemukan di kebocoran publik")]
        out = [f("Kebocoran (leakcheck)", "Email", email),
               f("Kebocoran (leakcheck)", "Jumlah baris bocor", d.get("found")),
               f("Kebocoran (leakcheck)", "Jenis data terekspos",
                 ", ".join(d.get("fields") or []) or "—")]
        for s in (d.get("sources") or [])[:20]:
            name = s.get("name") if isinstance(s, dict) else str(s)
            date = s.get("date") if isinstance(s, dict) else None
            out.append(f("Kebocoran (leakcheck)", name, date or ""))
        return out
