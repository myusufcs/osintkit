"""robots.txt & sitemap.xml — sering membocorkan path internal."""
from __future__ import annotations

import re

from ..core import http
from ..core.registry import Module
from . import f

RE_LOC = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.I | re.S)


class RobotsSitemap(Module):
    NAME = "robots"
    DESC = "robots.txt & sitemap.xml (path tersembunyi, sitemap index)"
    ACCEPTS = {"domain", "url"}
    ACTIVE = True

    def run(self, target, kinds, ctx):
        host = ctx["domain"] or target
        out = []
        r = http.get(f"https://{host}/robots.txt", timeout=15)
        if r is not None and r.status_code == 200 and "text" in r.headers.get("content-type", "text"):
            lines = [ln.strip() for ln in r.text.splitlines() if ln.strip()]
            out.append(f("robots.txt", "Baris", len(lines)))
            disallow = [ln for ln in lines if ln.lower().startswith(("disallow", "allow"))]
            for d in disallow[:40]:
                out.append(f("robots.txt", d, d, f"https://{host}/robots.txt"))
            smaps = [ln.split(":", 1)[1].strip() for ln in lines
                     if ln.lower().startswith("sitemap")]
            for s in smaps[:10]:
                out.append(f("robots.txt", "Sitemap", s, s))
        else:
            out.append(f("robots.txt", "Status", "tidak ada"))

        for path in ("/sitemap.xml", "/sitemap_index.xml"):
            r = http.get(f"https://{host}{path}", timeout=15)
            if r is None or r.status_code != 200:
                continue
            locs = RE_LOC.findall(r.text or "")
            out.append(f("sitemap", path, f"{len(locs)} URL"))
            for u in locs[:25]:
                out.append(f("sitemap", "URL", u, u))
        return out
