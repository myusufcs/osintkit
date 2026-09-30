"""Info IP: geolokasi/ASN (ip-api.com) + reverse DNS."""
from __future__ import annotations

import shutil
import socket
import subprocess

from ..core import http
from ..core.registry import Module
from . import f


def resolve(host: str) -> str | None:
    try:
        return socket.gethostbyname(host)
    except Exception:                     # noqa: BLE001
        return None


def ptr(ip: str) -> str | None:
    if shutil.which("dig"):
        try:
            p = subprocess.run(["dig", "+short", "-x", ip], capture_output=True,
                               text=True, timeout=10)
            val = p.stdout.strip().splitlines()
            return val[0].rstrip(".") if val else None
        except Exception:                 # noqa: BLE001
            pass
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:                     # noqa: BLE001
        return None


class IpInfo(Module):
    NAME = "ip"
    DESC = "Geolokasi, ISP/ASN, reverse DNS untuk IP (atau domain yang di-resolve)"
    ACCEPTS = {"ip", "domain", "url"}
    ACTIVE = True

    def run(self, target, kinds, ctx):
        ip = target if "ip" in kinds else resolve(ctx["domain"] or target)
        if not ip:
            return [f("IP", "Resolve", "gagal resolve domain")]
        out = [f("IP", "Alamat", ip)]
        rev = ptr(ip)
        if rev:
            out.append(f("IP", "Reverse DNS", rev))

        data = http.get_json(f"http://ip-api.com/json/{ip}",
                             params={"fields": "status,country,regionName,city,zip,"
                                               "lat,lon,timezone,isp,org,as,reverse,"
                                               "mobile,proxy,hosting,query"},
                             timeout=20)
        if isinstance(data, dict) and data.get("status") == "success":
            for key, label in (("country", "Negara"), ("regionName", "Provinsi"),
                               ("city", "Kota"), ("zip", "Kode pos"),
                               ("timezone", "Timezone"), ("isp", "ISP"),
                               ("org", "Organisasi"), ("as", "ASN"),
                               ("lat", "Latitude"), ("lon", "Longitude"),
                               ("hosting", "Hosting/VPS"), ("proxy", "Proxy/VPN")):
                if data.get(key) not in (None, ""):
                    out.append(f("IP", label, data[key]))
        else:
            out.append(f("IP", "Geolokasi", "tidak tersedia (rate-limit?)"))
        return out
