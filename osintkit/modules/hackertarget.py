"""HackerTarget API — sumber gratis tanpa key (hostsearch, reverse IP)."""
from __future__ import annotations

import socket

from ..core import http
from ..core.registry import Module
from . import f

BASE = "https://api.hackertarget.com"


def _text(url: str, params: dict) -> list[str]:
    r = http.get(url, params=params, timeout=30)
    if r is None or r.status_code != 200:
        return []
    body = (r.text or "").strip()
    if not body or body.lower().startswith("error"):
        return []
    return [ln.strip() for ln in body.splitlines() if ln.strip()]


class HackerTargetHosts(Module):
    NAME = "ht_subdomains"
    DESC = "Subdomain dari HackerTarget hostsearch (gratis, tanpa key)"
    ACCEPTS = {"domain", "url"}

    def run(self, target, kinds, ctx):
        dom = ctx.get("domain") or target
        lines = _text(f"{BASE}/hostsearch/", {"q": dom})
        if not lines:
            return [f("HackerTarget — subdomain", "Status", "tidak ada hasil / limit")]
        out = [f("HackerTarget — subdomain", "Total host", len(lines))]
        for ln in lines[:100]:
            parts = ln.split(",")
            host = parts[0].strip()
            ip = parts[1].strip() if len(parts) > 1 else ""
            out.append(f("HackerTarget — subdomain", host, ip or "—", f"https://{host}"))
        return out


class HackerTargetReverseIP(Module):
    NAME = "ht_reverseip"
    DESC = "Domain lain yang berbagi IP yang sama (reverse IP lookup)"
    ACCEPTS = {"ip", "domain", "url"}
    ACTIVE = True

    def run(self, target, kinds, ctx):
        ip = target if "ip" in kinds else None
        if not ip:
            try:
                ip = socket.gethostbyname(ctx.get("domain") or target)
            except Exception:                 # noqa: BLE001
                return []
        lines = _text(f"{BASE}/reverseiplookup/", {"q": ip})
        lines = [ln for ln in lines if "." in ln and " " not in ln]
        if not lines:
            return [f("Reverse IP", ip, "tidak ada domain lain terdeteksi")]
        out = [f("Reverse IP", "IP", ip),
               f("Reverse IP", "Jumlah domain lain", len(lines))]
        for d in lines[:60]:
            out.append(f("Reverse IP", d, d, f"https://{d}"))
        return out
