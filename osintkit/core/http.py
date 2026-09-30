"""HTTP klien bersama: session, User-Agent, rate-limit per host, retry ringan."""
from __future__ import annotations

import random
import threading
import time
from typing import Any

import requests

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

_session = requests.Session()
_session.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})

_lock = threading.Lock()
_last_hit: dict[str, float] = {}
MIN_INTERVAL = 0.8          # detik antar-request ke host yang sama


def _throttle(host: str) -> None:
    with _lock:
        now = time.time()
        prev = _last_hit.get(host, 0.0)
        gap = now - prev
        if gap < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - gap + random.uniform(0, 0.25))
        _last_hit[host] = time.time()


def get(url: str, *, params: dict | None = None, timeout: int = 20,
        headers: dict | None = None, allow_redirects: bool = True,
        attempts: int = 2) -> requests.Response | None:
    host = url.split("/")[2] if "//" in url else url
    last_err: Exception | None = None
    for i in range(attempts):
        _throttle(host)
        try:
            return _session.get(url, params=params, timeout=timeout,
                                headers=headers, allow_redirects=allow_redirects)
        except Exception as e:      # noqa: BLE001
            last_err = e
            if i + 1 < attempts:
                time.sleep(1.2 * (i + 1))
    return None


def get_json(url: str, **kw: Any):
    r = get(url, **kw)
    if r is None or r.status_code >= 400:
        return None
    try:
        return r.json()
    except Exception:               # noqa: BLE001
        return None


def head(url: str, *, timeout: int = 12) -> requests.Response | None:
    host = url.split("/")[2] if "//" in url else url
    _throttle(host)
    try:
        return _session.head(url, timeout=timeout, allow_redirects=True)
    except Exception:               # noqa: BLE001
        return None
