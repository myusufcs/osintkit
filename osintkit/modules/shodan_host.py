"""Shodan: port & service yang terekspos (butuh SHODAN_API_KEY)."""
from __future__ import annotations

import os
import socket

from ..core import http
from ..core.registry import Module
from . import f


class ShodanHost(Module):
    NAME = "shodan"
    DESC = "Port/service terekspos via Shodan — butuh SHODAN_API_KEY"
    ACCEPTS = {"ip", "domain", "url"}
    KEY_ENV = "SHODAN_API_KEY"

    def run(self, target, kinds, ctx):
        ip = target if "ip" in kinds else None
        if not ip:
            host = ctx.get("domain") or target
            try:
                ip = socket.gethostbyname(host)
            except Exception:                       # noqa: BLE001
                return []
        key = os.environ["SHODAN_API_KEY"]
        d = http.get_json(f"https://api.shodan.io/shodan/host/{ip}",
                          params={"key": key}, timeout=30)
        if not isinstance(d, dict) or d.get("error"):
            return [f("Shodan", ip, f"tidak ada data ({d.get('error') if isinstance(d, dict) else 'n/a'})")]
        out = [
            f("Shodan", "IP", ip),
            f("Shodan", "Organisasi", d.get("org")),
            f("Shodan", "ISP", d.get("isp")),
            f("Shodan", "Negara", d.get("country_name")),
            f("Shodan", "OS", d.get("os")),
            f("Shodan", "Hostname", ", ".join(d.get("hostnames") or [])),
            f("Shodan", "Port terbuka", ", ".join(str(p) for p in (d.get("ports") or []))),
        ]
        for p in (d.get("ports") or [])[:30]:
            out.append(f("Shodan — port", f"tcp/{p}", f"https://www.shodan.io/host/{ip}"))
        for cve in (d.get("vulns") or {})[:15]:
            out.append(f("Shodan — CVE", cve, "terdeteksi", f"https://nvd.nist.gov/vuln/detail/{cve}"))
        return [o for o in out if o["value"]]
