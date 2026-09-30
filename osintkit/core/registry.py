"""Registry modul: daftar otomatis + pemilihan berdasarkan tipe target."""
from __future__ import annotations

import importlib
import os
import pkgutil
from typing import Any

ALL_MODULES: list[type] = []


class Module:
    """Kontrak modul.

    NAME     : id unik (dipakai untuk --only/--skip)
    DESC     : deskripsi singkat
    ACCEPTS  : himpunan tipe target {"domain","ip","email","username","phone","url"}
    KEY_ENV  : nama env var API key (None = tidak butuh)
    ACTIVE   : True kalau modul menghubungi target langsung (bukan sumber pihak ketiga)
    """

    NAME = "?"
    DESC = ""
    ACCEPTS: set[str] = set()
    KEY_ENV: str | None = None
    ACTIVE = False

    def __init_subclass__(cls, **kw: Any) -> None:
        super().__init_subclass__(**kw)
        if getattr(cls, "NAME", "?") != "?":
            ALL_MODULES.append(cls)

    def available(self) -> tuple[bool, str]:
        if self.KEY_ENV and not os.environ.get(self.KEY_ENV):
            return False, f"butuh env {self.KEY_ENV}"
        return True, ""

    def run(self, target: str, kinds: set[str], ctx: dict) -> list[dict]:
        raise NotImplementedError


def load_all() -> None:
    """Impor semua modul di paket osintkit.modules supaya terdaftar."""
    from .. import modules as pkg
    for info in pkgutil.iter_modules(pkg.__path__):
        if info.name.startswith("_"):
            continue
        importlib.import_module(f"osintkit.modules.{info.name}")


def select(kinds: set[str], only: list[str] | None = None,
           skip: list[str] | None = None) -> list[type]:
    out = []
    for cls in ALL_MODULES:
        if only and cls.NAME not in only:
            continue
        if skip and cls.NAME in skip:
            continue
        if cls.ACCEPTS & kinds:
            out.append(cls)
    return sorted(out, key=lambda c: c.NAME)


def describe() -> list[tuple[str, str, str, bool]]:
    rows = []
    for cls in sorted(ALL_MODULES, key=lambda c: c.NAME):
        rows.append((cls.NAME, ",".join(sorted(cls.ACCEPTS)), cls.DESC,
                     bool(cls.KEY_ENV and not os.environ.get(cls.KEY_ENV))))
    return rows
