"""Metadata gambar lokal + tautan reverse image search."""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path
from urllib.parse import quote

from ..core.registry import Module
from . import f


def dimensions(path: Path) -> tuple[int, int] | None:
    b = path.read_bytes()[:65536]
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", b[16:24])
        return int(w), int(h)
    if b[:2] == b"\xff\xd8":                       # JPEG
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1
                continue
            marker = b[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return int(w), int(h)
            if marker in (0xD8, 0xD9):
                i += 2
                continue
            seg = struct.unpack(">H", b[i + 2:i + 4])[0]
            i += 2 + seg
    if b[:6] in (b"GIF87a", b"GIF89a"):
        w, h = struct.unpack("<HH", b[6:10])
        return int(w), int(h)
    return None


class ImageInfo(Module):
    NAME = "image"
    DESC = "Hash, dimensi, dan tautan reverse image search untuk file gambar"
    ACCEPTS = {"image"}

    def run(self, target, kinds, ctx):
        p = Path(target).expanduser()
        if not p.exists():
            return [f("Gambar", "File", f"tidak ditemukan: {p}")]
        data = p.read_bytes()
        out = [
            f("Gambar", "File", str(p)),
            f("Gambar", "Ukuran", f"{len(data)} byte ({len(data)/1024:.1f} KB)"),
            f("Gambar", "Tipe", p.suffix.lower()),
            f("Gambar", "MD5", hashlib.md5(data).hexdigest()),
            f("Gambar", "SHA1", hashlib.sha1(data).hexdigest()),
            f("Gambar", "SHA256", hashlib.sha256(data).hexdigest()),
        ]
        d = dimensions(p)
        if d:
            out.append(f("Gambar", "Dimensi", f"{d[0]} x {d[1]}"))
        out += [
            f("Gambar", "Google Lens", "buka & unggah manual",
              "https://lens.google.com/uploadbyurl?url=" + quote(str(p))),
            f("Gambar", "Yandex Images", "buka & unggah manual",
              "https://yandex.com/images/search?rpt=imageview&url=" + quote(str(p))),
            f("Gambar", "TinEye", "buka & unggah manual", "https://tineye.com/"),
            f("Gambar", "Bing Visual", "buka & unggah manual",
              "https://www.bing.com/images/searchbyimage/upload"),
        ]
        return out
