"""Profil HTTP: status, redirect, header keamanan, teknologi, judul halaman."""
from __future__ import annotations

import re

from ..core import http
from ..core.registry import Module
from . import f

SEC_HEADERS = ["strict-transport-security", "content-security-policy", "x-frame-options",
               "x-content-type-options", "referrer-policy", "permissions-policy"]
TECH_HINTS = {
    "server": "Server",
    "x-powered-by": "X-Powered-By",
    "x-generator": "Generator",
    "x-aspnet-version": "ASP.NET",
    "x-drupal-cache": "Drupal",
    "cf-ray": "Cloudflare",
    "x-vercel-id": "Vercel",
    "x-amz-cf-id": "AWS CloudFront",
    "x-github-request-id": "GitHub Pages",
    "x-shopify-stage": "Shopify",
    "x-wix-request-id": "Wix",
}
RE_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


class HttpInfo(Module):
    NAME = "http"
    DESC = "Status HTTP, redirect, header keamanan, teknologi, judul halaman"
    ACCEPTS = {"domain", "url"}
    ACTIVE = True

    def run(self, target, kinds, ctx):
        host = ctx["domain"] or target
        out = []
        for scheme in ("https", "http"):
            r = http.get(f"{scheme}://{host}", timeout=20, allow_redirects=True)
            if r is None:
                out.append(f("HTTP", scheme, "tidak bisa dihubungi"))
                continue
            out.append(f("HTTP", f"{scheme} status", r.status_code))
            out.append(f("HTTP", f"{scheme} URL akhir", r.url))
            if scheme == "http" and r.url.startswith("https://"):
                out.append(f("HTTP", "Redirect ke HTTPS", "ya (bagus)"))
            h = {k.lower(): v for k, v in r.headers.items()}
            for k, label in TECH_HINTS.items():
                if k in h:
                    out.append(f("Teknologi", label, h[k][:120]))
            missing = [s for s in SEC_HEADERS if s not in h]
            for s in SEC_HEADERS:
                out.append(f("Header keamanan", s,
                             h.get(s, "— TIDAK ADA —")[:120]))
            if missing:
                out.append(f("Header keamanan", "Kesimpulan",
                             f"{len(missing)} header hilang: {', '.join(missing)}"))
            m = RE_TITLE.search(r.text or "")
            if m:
                out.append(f("HTTP", "Judul halaman",
                             re.sub(r"\s+", " ", m.group(1)).strip()[:160]))
            out.append(f("HTTP", "Ukuran HTML", f"{len(r.text or '')} byte"))
        return out
