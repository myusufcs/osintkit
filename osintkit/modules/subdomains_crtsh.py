"""Subdomain dari Certificate Transparency Log (crt.sh) — gratis, tanpa key."""
from __future__ import annotations

from ..core import http
from ..core.registry import Module
from . import f

MAX_SHOW = 120


class CrtSh(Module):
    NAME = "crtsh"
    DESC = "Subdomain dari Certificate Transparency (crt.sh)"
    ACCEPTS = {"domain", "url"}

    def run(self, target, kinds, ctx):
        dom = ctx["domain"] or target
        data = http.get_json(f"https://crt.sh/?q=%25.{dom}&output=json", timeout=45)
        if not isinstance(data, list):
            return [f("Subdomain (crt.sh)", "Status", "tidak ada jawaban / rate-limited")]

        subs: set[str] = set()
        issuers: set[str] = set()
        for row in data:
            for name in (row.get("name_value") or "").split("\n"):
                n = name.strip().lower().lstrip("*.")
                if n.endswith(dom) and "@" not in n:
                    subs.add(n)
            if row.get("issuer_name"):
                issuers.add(row["issuer_name"][:90])

        out = [f("Subdomain (crt.sh)", "Total unik", len(subs))]
        for s in sorted(subs)[:MAX_SHOW]:
            out.append(f("Subdomain (crt.sh)", s, s, f"https://{s}"))
        if len(subs) > MAX_SHOW:
            out.append(f("Subdomain (crt.sh)", "(dipotong)",
                         f"{len(subs) - MAX_SHOW} lagi tidak ditampilkan"))
        for i in sorted(issuers)[:10]:
            out.append(f("Subdomain (crt.sh)", "Penerbit sertifikat", i))
        return out
