"""urlscan.io — riwayat scan publik sebuah domain/IP (gratis, tanpa key)."""
from __future__ import annotations

from ..core import http
from ..core.registry import Module
from . import f


class UrlScan(Module):
    NAME = "urlscan"
    DESC = "Riwayat scan publik urlscan.io (IP, ASN, server, verdict)"
    ACCEPTS = {"domain", "ip", "url"}

    def run(self, target, kinds, ctx):
        if "ip" in kinds:
            q = f"ip:{target}"
        else:
            q = f"domain:{ctx.get('domain') or target}"
        d = http.get_json("https://urlscan.io/api/v1/search/",
                          params={"q": q, "size": 15}, timeout=30)
        if not isinstance(d, dict):
            return [f("urlscan.io", "Status", "tidak ada jawaban / rate-limited")]
        results = d.get("results") or []
        out = [f("urlscan.io", "Total hasil", d.get("total", 0))]
        ips, servers, asns = set(), set(), set()
        for r in results:
            page = (r.get("page") or {})
            if page.get("ip"):
                ips.add(page["ip"])
            if page.get("server"):
                servers.add(page["server"])
            if page.get("asnname"):
                asns.add(f"{page.get('asn')} {page.get('asnname')}")
            out.append(f("urlscan.io — scan", page.get("url") or r.get("task", {}).get("url"),
                         f"IP {page.get('ip')} | {page.get('server') or ''}".strip(),
                         r.get("result")))
        for ip in sorted(ips):
            out.append(f("urlscan.io — IP terlihat", ip, ip))
        for s in sorted(servers):
            out.append(f("urlscan.io — server", s, s))
        for a in sorted(asns):
            out.append(f("urlscan.io — ASN", a, a))
        return out
