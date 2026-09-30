"""Registrasi domain/IP lewat RDAP (gratis, tanpa API key)."""
from __future__ import annotations

from ..core import http
from ..core.registry import Module
from . import f


class RdapWhois(Module):
    NAME = "rdap"
    DESC = "Data registrasi domain/IP (RDAP): registrar, tanggal, nameserver, status"
    ACCEPTS = {"domain", "url", "ip"}

    def run(self, target, kinds, ctx):
        q = ctx.get("domain") or target
        kind = "ip" if "ip" in kinds else "domain"
        data = http.get_json(f"https://rdap.org/{kind}/{q}", timeout=25)
        if not isinstance(data, dict):
            return [f("Registrasi", "RDAP", "tidak ada jawaban / tidak didukung")]

        out = [f("Registrasi", "Handle", data.get("handle"))]
        for ev in data.get("events", []) or []:
            out.append(f("Registrasi", f"Tanggal ({ev.get('eventAction')})",
                         ev.get("eventDate")))
        for ent in data.get("entities", []) or []:
            roles = ",".join(ent.get("roles", []) or [])
            name = None
            for v in (ent.get("vcardArray") or [None, []])[1]:
                if v and v[0] == "fn":
                    name = v[3]
            if name:
                out.append(f("Registrasi", f"Entitas ({roles})", name))
        for ns in data.get("nameservers", []) or []:
            out.append(f("Registrasi", "Nameserver", ns.get("ldhName")))
        for st in data.get("status", []) or []:
            out.append(f("Registrasi", "Status", st))
        for remark in data.get("remarks", []) or []:
            txt = " ".join(remark.get("description", []) or [])[:200]
            if txt:
                out.append(f("Registrasi", "Catatan", txt))
        return [o for o in out if o["value"]]
