from __future__ import annotations

import re

CALL_RE = re.compile(r"^[A-Z0-9]{1,3}[0-9][A-Z0-9/]{1,12}$")

BANDS: list[tuple[str, float, float]] = [
    ("160m", 1800, 2000),
    ("80m", 3500, 4000),
    ("60m", 5330, 5407),
    ("40m", 7000, 7300),
    ("30m", 10100, 10150),
    ("20m", 14000, 14350),
    ("17m", 18068, 18168),
    ("15m", 21000, 21450),
    ("12m", 24890, 24990),
    ("10m", 28000, 29700),
    ("6m", 50000, 54000),
    ("4m", 70000, 70500),
    ("2m", 144000, 148000),
]


def normalize_callsign(value: str) -> str:
    return value.strip().upper().rstrip(":")


def is_callsign_like(value: str) -> bool:
    return bool(CALL_RE.match(normalize_callsign(value)))


def frequency_to_band(frequency_khz: float) -> str | None:
    for band, low, high in BANDS:
        if low <= frequency_khz <= high:
            return band
    return None


def infer_mode(source_type: str, comment: str | None, frequency_khz: float) -> str:
    source_upper = source_type.upper()
    text = (comment or "").upper()
    if "FT8" in source_upper or "FT8" in text:
        return "FT8"
    if "FT4" in text:
        return "FT4"
    if "RTTY" in text:
        return "RTTY"
    if "WSPR" in source_upper or "WSPR" in text:
        return "WSPR"
    if any(token in text for token in ("PSK", "JT65", "JT9", "DIGI")):
        return "DIGITAL"
    if any(token in text for token in ("SSB", "USB", "LSB", "PHONE")):
        return "SSB"
    if source_upper == "RBN_CW_RTTY":
        return "RTTY" if "RTTY" in text else "CW"
    if frequency_khz % 1 and frequency_khz > 28000:
        return "UNKNOWN"
    return "UNKNOWN"
