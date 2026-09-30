"""Enumerasi username lintas situs (public profile pages)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core import http
from ..core.registry import Module
from . import f

# (nama, template URL, andal?)
# andal=True  -> 404 benar-benar berarti tidak ada
# andal=False -> situs memblokir / selalu 200; hasil ditandai "cek manual"
SITES: list[tuple[str, str, bool]] = [
    ("GitHub", "https://github.com/{u}", True),
    ("GitLab", "https://gitlab.com/{u}", True),
    ("Bitbucket", "https://bitbucket.org/{u}/", True),
    ("Reddit", "https://www.reddit.com/user/{u}/about.json", True),
    ("Medium", "https://medium.com/@{u}", True),
    ("Dev.to", "https://dev.to/{u}", True),
    ("Hacker News", "https://news.ycombinator.com/user?id={u}", True),
    ("Keybase", "https://keybase.io/{u}", True),
    ("npm", "https://www.npmjs.com/~{u}", True),
    ("PyPI", "https://pypi.org/user/{u}/", True),
    ("Docker Hub", "https://hub.docker.com/v2/users/{u}/", True),
    ("Kaggle", "https://www.kaggle.com/{u}", True),
    ("CodePen", "https://codepen.io/{u}", True),
    ("Replit", "https://replit.com/@{u}", True),
    ("Behance", "https://www.behance.net/{u}", True),
    ("Dribbble", "https://dribbble.com/{u}", True),
    ("Vimeo", "https://vimeo.com/{u}", True),
    ("SoundCloud", "https://soundcloud.com/{u}", True),
    ("Spotify", "https://open.spotify.com/user/{u}", True),
    ("Telegram", "https://t.me/{u}", True),
    ("Pinterest", "https://www.pinterest.com/{u}/", True),
    ("About.me", "https://about.me/{u}", True),
    ("Product Hunt", "https://www.producthunt.com/@{u}", True),
    ("Steam", "https://steamcommunity.com/id/{u}", False),
    ("Twitch", "https://www.twitch.tv/{u}", False),
    ("YouTube", "https://www.youtube.com/@{u}", False),
    ("TikTok", "https://www.tiktok.com/@{u}", False),
    ("Instagram", "https://www.instagram.com/{u}/", False),
    ("X / Twitter", "https://x.com/{u}", False),
]


class UsernameEnum(Module):
    NAME = "username"
    DESC = "Cek username di banyak situs (public profile)"
    ACCEPTS = {"username"}

    def _check(self, u: str, site: tuple[str, str, bool]):
        name, tpl, reliable = site
        url = tpl.format(u=u)
        r = http.head(url) if "about.json" not in url else http.get(url, timeout=12)
        if r is None:
            return None
        code = r.status_code
        if code == 200:
            return f("Username", name, "DITEMUKAN" + ("" if reliable else " (cek manual — situs sering blokir otomatis)"), url)
        if code in (404, 410):
            return None
        if code in (301, 302, 303, 307, 308):
            return None
        return f("Username", name, f"tidak bisa dipastikan (HTTP {code})", url)

    def run(self, target, kinds, ctx):
        u = target.strip().lstrip("@")
        found, blocked = [], 0
        with ThreadPoolExecutor(max_workers=10) as pool:
            futs = [pool.submit(self._check, u, s) for s in SITES]
            for fut in as_completed(futs):
                try:
                    res = fut.result()
                except Exception:               # noqa: BLE001
                    blocked += 1
                    continue
                if res:
                    found.append(res)
        out = [f("Username", "Username dicek", u),
               f("Username", "Situs diuji", len(SITES))]
        out += sorted(found, key=lambda x: x["key"])
        if blocked:
            out.append(f("Username", "Error saat cek", blocked))
        if not found:
            out.append(f("Username", "Hasil", "tidak ditemukan di daftar situs"))
        return out
