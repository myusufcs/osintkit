"""Email: cek Gravatar (gratis) + kebocoran via HaveIBeenPwned (butuh API key)."""
from __future__ import annotations

import hashlib

from ..core import http
from ..core.registry import Module
from . import f


class EmailGravatar(Module):
    NAME = "gravatar"
    DESC = "Cek apakah email punya Gravatar (indikasi akun aktif)"
    ACCEPTS = {"email"}

    def run(self, target, kinds, ctx):
        email = target.strip().lower()
        h = hashlib.md5(email.encode()).hexdigest()
        url = f"https://gravatar.com/avatar/{h}?d=404&s=200"
        r = http.get(url, timeout=15, allow_redirects=False)
        if r is None:
            return [f("Email", "Gravatar", "tidak bisa dicek", url)]
        if r.status_code == 200:
            return [f("Email", "Gravatar", "ADA — email terdaftar di Gravatar", url),
                    f("Email", "Hash MD5", h)]
        return [f("Email", "Gravatar", "tidak ada"), f("Email", "Hash MD5", h)]


class EmailBreach(Module):
    NAME = "hibp"
    DESC = "Kebocoran data (HaveIBeenPwned) — butuh HIBP_API_KEY"
    ACCEPTS = {"email"}
    KEY_ENV = "HIBP_API_KEY"

    def run(self, target, kinds, ctx):
        import os
        key = os.environ["HIBP_API_KEY"]
        data = http.get_json(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{target.strip()}",
            headers={"hibp-api-key": key, "user-agent": "osintkit"},
            params={"truncateResponse": "false"}, timeout=25)
        if data is None:
            return [f("Kebocoran", "HIBP", "tidak ada kebocoran terdeteksi")]
        out = [f("Kebocoran", "Total breach", len(data))]
        for b in data[:40]:
            out.append(f("Kebocoran", b.get("Name"),
                         f"{b.get('BreachDate')} — {b.get('PwnCount')} akun "
                         f"[{', '.join(b.get('DataClasses', [])[:4])}]",
                         b.get("Domain")))
        return out
