# osintkit

Toolkit OSINT **all-in-one** — satu perintah, banyak modul, satu laporan.

> ⚠️ **Pemakaian yang sah**: hanya untuk aset/domain milik sendiri, atau engagement
> yang sudah ada izin tertulis. Tidak ada modul di sini yang menembus autentikasi,
> memakai kredensial curian, atau mengambil data non-publik.

## Filosofi

Tidak membangun ulang tool yang sudah matang. Modul di sini = pembungkus tipis untuk
**sumber data publik**, **tool lokal** (`dig`, `curl`), dan **API resmi**.
Core yang mengatur: deteksi tipe target, pemilihan modul, paralelisasi, timeout,
normalisasi hasil, dan rendering laporan.

## Instalasi

Cukup Python 3.10+ dan `requests`. **Tidak ada dependensi berat** — Web UI pun memakai
`http.server` bawaan, jadi tidak perlu Flask.

```bash
pip install requests          # kalau belum ada
```

Semua modul inti **gratis tanpa API key**. Modul ber-key bersifat opsional dan otomatis
dilewati (dengan catatan, bukan error) kalau env-nya kosong:

```bash
export SHODAN_API_KEY=xxxx        # opsional — versi gratisnya sudah ada: modul `internetdb`
export HIBP_API_KEY=xxxx          # opsional — versi gratisnya sudah ada: modul `leakcheck`
export GITHUB_TOKEN=xxxx          # opsional — rate limit GitHub lebih tinggi
```

## Pemakaian (CLI)

```bash
# domain -> DNS, RDAP, TLS, HTTP, subdomain (crt.sh + HackerTarget),
#           InternetDB, urlscan, wayback, dork, IP, reverse IP
python3 -m osintkit scan example.com

# email -> gravatar, leakcheck (kebocoran), DNS domainnya
python3 -m osintkit scan "budi@example.com"

# username -> cek di ~29 situs + profil GitHub
python3 -m osintkit scan johndoe --only username,github_user,github_search

# IP -> geo/ASN/reverse DNS, InternetDB (port/CVE), urlscan, reverse IP
python3 -m osintkit scan 8.8.8.8

# gambar -> hash, dimensi, tautan reverse image search
python3 -m osintkit scan ~/foto.jpg

# nomor HP -> normalisasi + kode negara + indikasi operator
python3 -m osintkit scan "+628123456789"

python3 -m osintkit modules      # daftar modul + status gratis/butuh key
```

Hasil ditulis ke `~/osintkit-reports/` dalam **Markdown + HTML + JSON**.
Tambahkan `--open` untuk langsung membuka HTML-nya.

## Pemakaian (Web UI)

```bash
python3 -m osintkit web                 # http://127.0.0.1:8787
python3 -m osintkit web --port 9000 --open
```

- Halaman utama: form target + filter modul + toggle "aktif".
- Scan berjalan di background; halaman job auto-refresh sampai selesai.
- Laporan HTML lengkap disajikan di `/report/<id>`.
- API JSON: `GET /api/modules` dan `GET /api/scan?target=...&only=dns,tls&active=1`.
- Bind default `127.0.0.1` (tidak terekspos ke jaringan).

## Arsitektur

```
osintkit/
  cli.py                 # argparse: scan / web / modules
  webui.py               # Web UI (stdlib http.server, tanpa Flask)
  core/
    detect.py            # klasifikasi target (domain/url/ip/email/username/phone/image)
    registry.py          # auto-register modul + pemilihan berdasarkan tipe target
    pipeline.py          # orkestrasi scan (dipakai CLI & Web)
    runner.py            # ThreadPool, timeout, status per modul
    http.py              # session, UA, rate-limit per host, retry
    report.py            # render Markdown / HTML / JSON
  modules/               # 1 file = 1 modul (atau beberapa modul sejenis)
```

Kontrak modul:

```python
from ..core.registry import Module
from . import f

class MyModule(Module):
    NAME = "mymodule"          # id unik (dipakai --only / --skip)
    DESC = "apa yang dicek"
    ACCEPTS = {"domain"}       # tipe target yang diterima
    KEY_ENV = None             # nama env var API key (None = tidak butuh)
    ACTIVE = False             # True = menyentuh target langsung

    def run(self, target, kinds, ctx):
        return [f("Section", "Key", "Value", "https://sumber")]
```

## Modul yang tersedia

| Modul | Target | Butuh key | Isi |
|---|---|---|---|
| `dns` | domain | — | A/AAAA/MX/TXT/NS/SOA/CAA |
| `zonetransfer` | domain | — | cek AXFR *(aktif, perlu `--active`)* |
| `rdap` | domain, ip | — | registrar, tanggal, nameserver, status |
| `tls` | domain | — | penerbit, expiry, **SAN (subdomain bocor)** |
| `tlsports` | domain | — | port HTTPS alternatif |
| `http` | domain | — | status, redirect, header keamanan, teknologi |
| `robots` | domain | — | robots.txt + sitemap |
| `crtsh` | domain | — | subdomain dari Certificate Transparency |
| `ht_subdomains` | domain | — | subdomain (HackerTarget hostsearch) |
| `ht_reverseip` | domain, ip | — | domain lain di IP yang sama |
| `internetdb` | ip, domain | — | **port + CVE (Shodan InternetDB, gratis)** |
| `urlscan` | domain, ip | — | riwayat scan publik urlscan.io (IP/ASN/server) |
| `wayback` | domain | — | URL historis + path terpopuler |
| `dorks` | domain | — | Google Dork siap pakai |
| `ip` | ip, domain | — | geolokasi, ISP/ASN, reverse DNS |
| `username` | username | — | cek ~29 situs |
| `github_user` | username | — | profil GitHub |
| `github_search` | domain, username | — | repo yang menyebut target |
| `grepapp` | domain, email, username | — | string di repo publik |
| `gravatar` | email | — | indikasi akun email aktif |
| `leakcheck` | email | — | **indikasi kebocoran (leakcheck.io, gratis)** |
| `phone` | phone | — | normalisasi + kode negara + operator |
| `image` | file gambar | — | hash, dimensi, tautan reverse search |
| `shodan` | ip, domain | `SHODAN_API_KEY` | versi lengkap Shodan *(opsional)* |
| `hibp` | email | `HIBP_API_KEY` | HaveIBeenPwned *(opsional)* |

## Roadmap

- [x] CLI + Web UI
- [x] Modul gratis pengganti yang ber-key (InternetDB, leakcheck, HackerTarget, urlscan)
- [ ] Modul email permutasi (firstname.lastname@domain)
- [ ] Integrasi `subfinder`/`amass` kalau terpasang
- [ ] Modul PDF/Office metadata (butuh `exiftool`)
- [ ] IOC enrichment (VirusTotal, AbuseIPDB)
- [ ] Riwayat scan + diff antar-scan di Web UI
- [ ] Ekspor laporan ke PDF
