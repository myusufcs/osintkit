"""Paket modul osintkit.

Setiap modul mendaftarkan diri otomatis lewat subclass `core.registry.Module`.
Helper `f()` dipakai untuk membuat satu baris temuan.
"""
from __future__ import annotations


def f(section: str, key: str, value, source: str | None = None) -> dict:
    """Satu baris temuan yang seragam."""
    return {"section": section, "key": str(key), "value": value, "source": source}
