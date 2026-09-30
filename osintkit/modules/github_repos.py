"""GitHub: profil & repo yang menyebut target (API publik, token opsional)."""
from __future__ import annotations

import os

from ..core import http
from ..core.registry import Module
from . import f


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "osintkit"}
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


class GithubUser(Module):
    NAME = "github_user"
    DESC = "Profil GitHub (bio, repo publik, lokasi, situs) — token opsional"
    ACCEPTS = {"username"}

    def run(self, target, kinds, ctx):
        u = target.strip().lstrip("@")
        d = http.get_json(f"https://api.github.com/users/{u}", headers=_headers(), timeout=20)
        if not isinstance(d, dict) or d.get("message"):
            return []
        out = [
            f("GitHub", "Login", d.get("login"), d.get("html_url")),
            f("GitHub", "Nama", d.get("name")),
            f("GitHub", "Bio", d.get("bio")),
            f("GitHub", "Lokasi", d.get("location")),
            f("GitHub", "Perusahaan", d.get("company")),
            f("GitHub", "Blog/situs", d.get("blog")),
            f("GitHub", "Email publik", d.get("email")),
            f("GitHub", "Repo publik", d.get("public_repos")),
            f("GitHub", "Follower", d.get("followers")),
            f("GitHub", "Dibuat", d.get("created_at")),
        ]
        return [o for o in out if o["value"]]


class GithubSearch(Module):
    NAME = "github_search"
    DESC = "Repo GitHub yang menyebut target (domain/username)"
    ACCEPTS = {"domain", "username"}

    def run(self, target, kinds, ctx):
        d = http.get_json("https://api.github.com/search/repositories",
                          params={"q": target, "per_page": 10},
                          headers=_headers(), timeout=25)
        if not isinstance(d, dict):
            return [f("GitHub", "Pencarian repo", "tidak tersedia (rate-limit?)")]
        out = [f("GitHub", "Total repo cocok", d.get("total_count", 0))]
        for it in (d.get("items") or [])[:10]:
            out.append(f("GitHub", it.get("full_name"),
                         f"{it.get('description') or ''}"[:120], it.get("html_url")))
        return out
