"""Sertifikat TLS: penerbit, masa berlaku, dan nama alternatif (SAN)."""
from __future__ import annotations

import datetime as dt
import socket
import ssl

from ..core.registry import Module
from . import f


class TlsCert(Module):
    NAME = "tls"
    DESC = "Sertifikat TLS server: penerbit, expiry, SAN (subdomain bocor)"
    ACCEPTS = {"domain", "url"}
    ACTIVE = True

    def run(self, target, kinds, ctx):
        host = ctx["domain"] or target
        try:
            raw = ssl.get_server_certificate((host, 443), timeout=10)
        except Exception as e:                       # noqa: BLE001
            return [f("TLS", "Status", f"gagal ambil sertifikat ({type(e).__name__})")]

        try:
            from cryptography import x509
            cert = x509.load_pem_x509_certificate(raw.encode())
        except Exception:                            # noqa: BLE001
            return [f("TLS", "Sertifikat", raw[:600])]

        nb = cert.not_valid_before_utc if hasattr(cert, "not_valid_before_utc") else cert.not_valid_before
        na = cert.not_valid_after_utc if hasattr(cert, "not_valid_after_utc") else cert.not_valid_after
        days = (na - dt.datetime.now(dt.timezone.utc)).days

        out = [
            f("TLS", "Subject", cert.subject.rfc4514_string()),
            f("TLS", "Penerbit", cert.issuer.rfc4514_string()),
            f("TLS", "Berlaku dari", nb.isoformat()),
            f("TLS", "Kedaluwarsa", f"{na.isoformat()}  ({days} hari lagi)"),
            f("TLS", "Serial", hex(cert.serial_number)),
        ]
        try:
            san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            names = san.value.get_values_for_type(x509.DNSName)
            for n in names[:60]:
                out.append(f("TLS — SAN (subdomain)", n, n))
            if len(names) > 60:
                out.append(f("TLS — SAN (subdomain)", "(dipotong)",
                             f"{len(names)} nama total"))
        except Exception:                            # noqa: BLE001
            pass
        return out


class TlsPorts(Module):
    NAME = "tlsports"
    DESC = "Cek port HTTPS umum alternatif (8443, 9443, 4443)"
    ACCEPTS = {"domain", "url"}
    ACTIVE = True

    def run(self, target, kinds, ctx):
        host = ctx["domain"] or target
        out = []
        for port in (8443, 9443, 4443):
            s = socket.socket()
            s.settimeout(4)
            try:
                s.connect((host, port))
                out.append(f("Port", f"tcp/{port}", "terbuka"))
            except Exception:                        # noqa: BLE001
                pass
            finally:
                s.close()
        return out
