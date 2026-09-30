"""DNS records & kalender zona (pakai `dig` lokal)."""
from __future__ import annotations

import shutil
import subprocess

from ..core.registry import Module
from . import f

TYPES = ["A", "AAAA", "MX", "TXT", "NS", "SOA", "CAA"]


def dig(name: str, rtype: str) -> list[str]:
    if not shutil.which("dig"):
        return []
    try:
        p = subprocess.run(["dig", "+time=3", "+tries=1", "+short", name, rtype],
                           capture_output=True, text=True, timeout=12)
    except Exception:                     # noqa: BLE001
        return []
    return [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]


class DnsRecords(Module):
    NAME = "dns"
    DESC = "Catatan DNS (A/AAAA/MX/TXT/NS/SOA/CAA)"
    ACCEPTS = {"domain", "url"}

    def run(self, target, kinds, ctx):
        dom = ctx["domain"] or target
        out = []
        for t in TYPES:
            for v in dig(dom, t):
                out.append(f("DNS", t, v, f"https://dns.google/query?name={dom}&type={t}"))
        for v in dig("www." + dom, "CNAME"):
            out.append(f("DNS", "CNAME (www)", v))
        return out


class ZoneTransfer(Module):
    NAME = "zonetransfer"
    DESC = "Cek AXFR (zone transfer) terbuka — AKTIF, hanya untuk domain sendiri"
    ACCEPTS = {"domain", "url"}
    ACTIVE = True

    def run(self, target, kinds, ctx):
        if not ctx.get("active") or not shutil.which("dig"):
            return []
        dom = ctx["domain"] or target
        ns = dig(dom, "NS")
        out = []
        for server in ns[:4]:
            try:
                p = subprocess.run(["dig", "+time=4", "+tries=1", "AXFR", dom, "@" + server],
                                   capture_output=True, text=True, timeout=15)
            except Exception:             # noqa: BLE001
                continue
            lines = [ln for ln in p.stdout.splitlines() if ln and not ln.startswith(";")]
            if lines:
                out.append(f("DNS", f"AXFR via {server}",
                             f"TERBUKA — {len(lines)} record (segera tutup!)"))
            else:
                out.append(f("DNS", f"AXFR via {server}", "ditolak (bagus)"))
        return out
