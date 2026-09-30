"""Deteksi tipe target: domain / url / ip / email / username / phone."""
from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
RE_DOMAIN = re.compile(
    r"^(?=.{4,253}$)([A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$")
RE_USERNAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,29}$")
RE_PHONE = re.compile(r"^\+?\d[\d\s\-()]{6,}$")


def normalize(target: str) -> tuple[str, set[str]]:
    """Kembalikan (nilai inti, himpunan tipe). Contoh: url -> domain."""
    t = (target or "").strip()
    if not t:
        return "", {"unknown"}

    if t.startswith(("http://", "https://")):
        host = urlparse(t).hostname or ""
        kinds = {"url"}
        if host:
            kinds |= _classify(host)
        return host or t, kinds

    return t, _classify(t)


def _classify(t: str) -> set[str]:
    kinds: set[str] = set()
    try:
        ipaddress.ip_address(t)
        return {"ip"}
    except ValueError:
        pass

    if RE_EMAIL.match(t):
        kinds.add("email")
        kinds.add("domain")              # bagian domain ikut diproses
    elif RE_DOMAIN.match(t):
        kinds.add("domain")

    if RE_PHONE.match(t) and not kinds:
        kinds.add("phone")

    if not kinds and RE_USERNAME.match(t):
        kinds.add("username")

    return kinds or {"unknown"}


def domain_of(target: str, kinds: set[str]) -> str | None:
    """Ambil domain bersih (tanpa user@, tanpa subdomain www)."""
    if "email" in kinds and "@" in target:
        target = target.split("@", 1)[1]
    if "domain" in kinds:
        return target.lower().lstrip(".")
    return None
