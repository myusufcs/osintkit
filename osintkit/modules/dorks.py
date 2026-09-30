"""Pembuat Google Dork + tautan mesin pencari (bukan scraper)."""
from __future__ import annotations

from urllib.parse import quote_plus

from ..core.registry import Module
from . import f

DORK_TEMPLATES = [
    ("Dokumen bocor", 'site:{d} (ext:pdf OR ext:xls OR ext:xlsx OR ext:doc OR ext:docx OR ext:ppt OR ext:pptx)'),
    ("File konfigurasi", 'site:{d} (ext:conf OR ext:config OR ext:ini OR ext:env OR ext:yaml OR ext:yml OR ext:json OR ext:bak)'),
    ("Kredensial/kunci", 'site:{d} ("password" OR "api_key" OR "apikey" OR "secret" OR "token") filetype:txt'),
    ("Halaman login/admin", 'site:{d} (inurl:login OR inurl:admin OR inurl:dashboard OR intitle:"index of")'),
    ("Direktori terbuka", 'site:{d} intitle:"index of"'),
    ("Error/debug", 'site:{d} ("sql syntax" OR "stack trace" OR "Warning:" OR "Fatal error")'),
    ("Subdomain", 'site:*.{d}'),
    ("Email terkait", '"{d}" "@{d}" OR email'),
    ("Panel DB", 'site:{d} (inurl:phpmyadmin OR inurl:adminer OR inurl:"/sql")'),
    ("Git terekspos", 'site:{d} inurl:.git'),
]

ENGINES = {
    "Google": "https://www.google.com/search?q=",
    "Bing": "https://www.bing.com/search?q=",
    "DuckDuckGo": "https://duckduckgo.com/?q=",
}


class Dorks(Module):
    NAME = "dorks"
    DESC = "Google Dork siap pakai + tautan pencarian"
    ACCEPTS = {"domain", "url"}

    def run(self, target, kinds, ctx):
        dom = ctx["domain"] or target
        out = []
        for label, tpl in DORK_TEMPLATES:
            q = tpl.format(d=dom)
            link = ENGINES["Google"] + quote_plus(q)
            out.append(f("Dork", label, q, link))
        for name, base in ENGINES.items():
            out.append(f("Dork — mesin pencari", name, "semua halaman terindeks",
                         base + quote_plus(f"site:{dom}")))
        return out
