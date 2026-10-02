"""Uji osintkit — semuanya OFFLINE.

Modul yang butuh jaringan tidak dipanggil; yang diuji adalah logika inti:
deteksi tipe target, registry modul, penyusun laporan, dan modul yang murni lokal
(gambar, nomor telepon, dorks).
"""
from __future__ import annotations

import json
import os
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from osintkit.core import detect, registry, report as report_mod   # noqa: E402


def tiny_png() -> bytes:
    """PNG 3x2 minimal (valid) untuk menguji pembaca dimensi."""
    w, h = 3, 2
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * w for _ in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


class TestDetect(unittest.TestCase):
    def test_tipe_dasar(self):
        self.assertEqual(detect.normalize("example.com")[1], {"domain"})
        self.assertEqual(detect.normalize("8.8.8.8")[1], {"ip"})
        self.assertEqual(detect.normalize("2606:4700::1111")[1], {"ip"})
        self.assertIn("email", detect.normalize("budi@example.co.id")[1])
        self.assertEqual(detect.normalize("johndoe")[1], {"username"})
        self.assertEqual(detect.normalize("+628123456789")[1], {"phone"})

    def test_url_diambil_hostnya(self):
        host, kinds = detect.normalize("https://aman.id/halaman?x=1")
        self.assertEqual(host, "aman.id")
        self.assertIn("domain", kinds)
        self.assertIn("url", kinds)

    def test_email_juga_dianggap_domain(self):
        kinds = detect.normalize("a@b.com")[1]
        self.assertIn("email", kinds)
        self.assertIn("domain", kinds)

    def test_kosong_dan_aneh(self):
        self.assertEqual(detect.normalize("")[1], {"unknown"})
        self.assertEqual(detect.normalize("!!!")[1], {"unknown"})

    def test_domain_of(self):
        kinds = detect.normalize("budi@example.com")[1]
        self.assertEqual(detect.domain_of("budi@example.com", kinds), "example.com")
        self.assertIsNone(detect.domain_of("192.168.1.1", {"ip"}))


class TestRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry.load_all()

    def test_modul_terdaftar_dan_unik(self):
        names = [m.NAME for m in registry.ALL_MODULES]
        self.assertGreaterEqual(len(names), 25)
        self.assertEqual(len(names), len(set(names)), "ada nama modul duplikat")

    def test_pemilihan_berdasarkan_tipe(self):
        dom = registry.select({"domain"})
        self.assertTrue(all("domain" in m.ACCEPTS for m in dom))
        self.assertIn("dns", [m.NAME for m in dom])
        self.assertNotIn("phone", [m.NAME for m in dom])

    def test_modul_username(self):
        self.assertIn("username", [m.NAME for m in registry.select({"username"})])

    def test_only_dan_skip(self):
        self.assertEqual([m.NAME for m in registry.select({"domain"}, ["dns"])], ["dns"])
        sisa = [m.NAME for m in registry.select({"domain"}, None, ["dns"])]
        self.assertNotIn("dns", sisa)

    def test_modul_butuh_key_ditandai(self):
        rows = dict((n, m) for n, _a, _d, m in registry.describe())
        self.assertTrue(rows["hibp"])        # butuh HIBP_API_KEY
        self.assertTrue(rows["shodan"])      # butuh SHODAN_API_KEY
        self.assertFalse(rows["dns"])        # gratis
        os.environ.pop("HIBP_API_KEY", None)
        self.assertTrue(all(m.KEY_ENV for m in registry.ALL_MODULES if m.NAME == "hibp"))


class TestReport(unittest.TestCase):
    def _data(self):
        meta = {"target": "example.com", "kinds": ["domain"],
                "started": "2026-01-01T00:00:00", "active": False}
        findings = [{"section": "DNS", "key": "A", "value": "1.2.3.4",
                     "source": "https://dns.google", "module": "dns"}]
        status = [{"module": "dns", "state": "ok", "count": 1, "detail": ""}]
        return meta, findings, status

    def test_markdown_ada_tabel_dan_sumber(self):
        md = report_mod.to_markdown(*self._data())
        self.assertIn("## DNS", md)
        self.assertIn("| Key | Value | Sumber |", md)
        self.assertIn("1.2.3.4", md)

    def test_json_valid(self):
        d = json.loads(report_mod.to_json(*self._data()))
        self.assertEqual(d["meta"]["target"], "example.com")
        self.assertIn("DNS", d["sections"])

    def test_html_memuat_nilai_dan_tanpa_skrip_asing(self):
        h = report_mod.to_html(*self._data())
        self.assertTrue(h.startswith("<!doctype html>"))
        self.assertIn("1.2.3.4", h)
        self.assertIn("</html>", h)

    def test_write_tiga_format(self):
        with tempfile.TemporaryDirectory() as td:
            files = report_mod.write(Path(td), *self._data(), formats=["md", "html", "json"])
            self.assertEqual(len(files), 3)
            for f in files:
                self.assertTrue(f.stat().st_size > 0)


class TestModulLokal(unittest.TestCase):
    """Modul yang tidak butuh jaringan sama sekali."""

    def test_image_info_md5_dan_dimensi(self):
        from osintkit.modules.image_info import ImageInfo, dimensions
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "kecil.png"
            p.write_bytes(tiny_png())
            self.assertEqual(dimensions(p), (3, 2))
            rows = ImageInfo().run(str(p), {"image"}, {})
            keys = {r["key"]: r["value"] for r in rows}
            self.assertEqual(keys["Dimensi"], "3 x 2")
            self.assertEqual(len(keys["MD5"]), 32)
            self.assertEqual(len(keys["SHA256"]), 64)

    def test_image_info_berkas_tidak_ada(self):
        from osintkit.modules.image_info import ImageInfo
        rows = ImageInfo().run("/tidak/ada.jpg", {"image"}, {})
        self.assertIn("tidak ditemukan", rows[0]["value"])

    def test_phone_info_kenali_indonesia(self):
        from osintkit.modules.phone_info import PhoneInfo
        rows = PhoneInfo().run("+6285156549503", {"phone"}, {})
        keys = {r["key"]: r["value"] for r in rows}
        self.assertIn("Indonesia", keys["Kode negara"])
        self.assertIn("operator", " ".join(keys).lower())

    def test_dorks_hasilkan_tautan_pencarian(self):
        from osintkit.modules.dorks import Dorks
        rows = Dorks().run("example.com", {"domain"}, {"domain": "example.com"})
        self.assertGreaterEqual(len(rows), 10)
        self.assertTrue(all(r["source"] and r["source"].startswith("http") for r in rows))
        self.assertTrue(any("site:example.com" in r["value"] for r in rows))


class TestWebUi(unittest.TestCase):
    def test_index_body_memuat_daftar_modul(self):
        from osintkit.webui import index_body
        html = index_body()
        self.assertIn('name="target"', html)
        self.assertIn("Modul tersedia", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
