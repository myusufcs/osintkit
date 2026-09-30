"""Shodan InternetDB — port/CVE tanpa API key (gratis)."""
from __future__ import annotations

import socket

from ..core import http
from ..core.registry import Module
from . import f


def _resolve(host: str) -> str | None:
    try:
        return socket.gethostbyname(host)
    except Exception:                     # noqa: BLE001
        return None


class InternetDB(Module):
    NAME = "internetdb"
    DESC = "Port, hostname, CVE dari Shodan InternetDB (GRATIS, tanpa API key)"
    ACCEPTS = {"ip", "domain", "url"}
    ACTIVE = True

    def run(self, target, kinds, ctx):
        ip = target if "ip" in kinds else _resolve(ctx.get("domain") or target)
        if not ip:
            return [f("InternetDB", "Resolve", "gagal resolve domain")]

        d = http.get_json(f"https://internetdb.shodan.io/{ip}", timeout=25)
        if not isinstance(d, dict):
            return [f("InternetDB", ip, "tidak ada data")]
        if d.get("detail"):
            return [f("InternetDB", ip, f"tidak ada data ({d['detail']})")]

        out = [f("InternetDB", "IP", ip)]
        ports = d.get("ports") or []
        out.append(f("InternetDB", "Port terbuka",
                     ", ".join(str(p) for p in ports) or "(tidak ada)"))
        for p in ports[:30]:
            out.append(f("InternetDB — port", f"tcp/{p}", "terbuka",
                         f"https://www.shodan.io/host/{ip}"))
        for h in (d.get("hostnames") or [])[:20]:
            out.append(f("InternetDB — hostname", h, h))
        for c in (d.get("cpes") or [])[:20]:
            out.append(f("InternetDB — CPE", c, c))
        for t in (d.get("tags") or []):
            out.append(f("InternetDB — tag", t, t))
        vulns = d.get("vulns") or []
        out.append(f("InternetDB", "Jumlah CVE", len(vulns)))
        for v in vulns[:20]:
            out.append(f("InternetDB — CVE", v, "terdeteksi",
                         f"https://nvd.nist.gov/vuln/detail/{v}"))
        return out
