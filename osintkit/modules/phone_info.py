"""Nomor telepon: normalisasi, kode negara, dan tautan verifikasi manual."""
from __future__ import annotations

import re

from ..core.registry import Module
from . import f

# kode panggil negara (subset umum)
DIAL = {
    "62": "Indonesia", "60": "Malaysia", "65": "Singapura", "61": "Australia",
    "1": "AS/Kanada", "44": "Inggris", "81": "Jepang", "82": "Korea Selatan",
    "86": "Tiongkok", "91": "India", "66": "Thailand", "84": "Vietnam",
    "63": "Filipina", "673": "Brunei", "95": "Myanmar", "855": "Kamboja",
    "971": "UEA", "966": "Arab Saudi", "7": "Rusia", "49": "Jerman",
    "33": "Prancis", "31": "Belanda", "39": "Italia", "34": "Spanyol",
    "55": "Brasil", "52": "Meksiko", "27": "Afrika Selatan", "20": "Mesir",
    "92": "Pakistan", "880": "Bangladesh", "94": "Sri Lanka", "64": "Selandia Baru",
}
# operator umum di Indonesia (prefix setelah 08)
ID_OP = {
    "0811": "Smartfren", "0812": "Telkomsel", "0813": "Telkomsel", "0814": "Indosat",
    "0815": "Telkomsel", "0816": "Telkomsel", "0817": "XL", "0818": "XL",
    "0819": "XL", "0821": "Telkomsel", "0822": "Telkomsel", "0823": "Telkomsel",
    "0851": "Telkomsel", "0852": "Telkomsel", "0853": "Telkomsel",
    "0855": "Indosat", "0856": "Indosat", "0857": "Indosat", "0858": "Indosat",
    "0877": "XL", "0878": "XL", "0881": "Smartfren", "0882": "Smartfren",
    "0895": "3", "0896": "3", "0897": "3", "0898": "3", "0899": "3",
}


class PhoneInfo(Module):
    NAME = "phone"
    DESC = "Normalisasi nomor, kode negara, dan indikasi operator"
    ACCEPTS = {"phone"}

    def run(self, target, kinds, ctx):
        digits = re.sub(r"\D", "", target)
        out = [f("Telepon", "Input", target), f("Telepon", "Digit", digits),
               f("Telepon", "Panjang", len(digits))]
        cc = None
        for n in (3, 2, 1):
            if digits[:n] in DIAL:
                cc = digits[:n]
                break
        if cc:
            out.append(f("Telepon", "Kode negara", f"+{cc} — {DIAL[cc]}"))
            local = digits[len(cc):]
            out.append(f("Telepon", "Format E.164", f"+{digits}"))
            out.append(f("Telepon", "Nomor nasional", local))
        else:
            out.append(f("Telepon", "Kode negara", "tidak dikenali"))

        if digits.startswith("62") or digits.startswith("0"):
            d = "0" + digits[2:] if digits.startswith("62") else digits
            for pfx in (d[:4], d[:3]):
                if pfx in ID_OP:
                    out.append(f("Telepon", "Operator (perkiraan)", ID_OP[pfx]))
                    break
        out.append(f("Telepon", "Catatan",
                     "Validasi pemilik/identitas butuh layanan resmi; modul ini tidak mengakses data pribadi"))
        return out
