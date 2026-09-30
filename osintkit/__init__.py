"""osintkit — toolkit OSINT all-in-one (modular).

Filosofi:
  - JANGAN bikin ulang tool yang sudah matang. Modul di sini = pembungkus tipis
    untuk sumber data publik + tool lokal (dig, curl) + API resmi.
  - Tiap modul mendeklarasikan tipe target yang diterima; core yang mengatur
    kapan modul dipanggil, paralelisasi, timeout, dan penyusunan laporan.
  - Semua hasil dinormalkan jadi list[dict] dengan bentuk seragam:
        {"section": str, "key": str, "value": Any, "source": str|None}

PEMAKAIAN YANG SAH: hanya untuk aset/domain milik sendiri, atau dalam rangka
engagement yang sudah ada izin tertulis. Tidak ada modul yang menembus
autentikasi atau memakai kredensial curian.
"""

__version__ = "0.1.0"
