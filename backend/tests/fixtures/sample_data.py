"""Shared fixtures and demo data for tests."""

from __future__ import annotations

import struct
import zlib
from decimal import Decimal

# Minimal valid 1×1 pixel JPEG bytes (no real ticket data)
MINIMAL_JPEG = bytes([
    0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
    0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00,
    0xFF, 0xDB, 0x00, 0x43, 0x00,
    *([0x08] * 64),
    0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x11, 0x00,
    0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01,
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
    0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B,
    0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB, 0xDE,
    0xFF, 0xD9,
])

# Minimal valid PNG (1×1 red pixel)


def _make_minimal_png() -> bytes:
    def chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    png_sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw_data = b"\x00\xFF\x00\x00"  # filter byte + RGB
    idat = chunk(b"IDAT", zlib.compress(raw_data))
    iend = chunk(b"IEND", b"")
    return png_sig + ihdr + idat + iend


MINIMAL_PNG = _make_minimal_png()

# Sample extraction fixture dicts
SAMPLE_ITEMS = [
    {
        "raw_description": "LECHE ENTERA 1L",
        "quantity": Decimal("2"),
        "unit": "ud",
        "unit_price": Decimal("0.89"),
        "total_price": Decimal("1.78"),
    },
    {
        "raw_description": "YOGUR X4",
        "quantity": Decimal("1"),
        "unit": "ud",
        "unit_price": Decimal("0.95"),
        "discount": Decimal("0.20"),
        "total_price": Decimal("0.75"),
    },
]
