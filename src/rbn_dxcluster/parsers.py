from __future__ import annotations

import re
from datetime import UTC, datetime

from .models import SourceType, Spot
from .radio import frequency_to_band, infer_mode, normalize_callsign

DX_RE = re.compile(
    r"^DX\s+de\s+(?P<spotter>\S+):\s+"
    r"(?P<freq>\d+(?:\.\d+)?)\s+"
    r"(?P<dx>\S+)\s*"
    r"(?P<comment>.*?)\s*"
    r"(?P<time>\d{4}Z)?\s*$",
    re.IGNORECASE,
)
SNR_RE = re.compile(r"(?P<snr>[+-]?\d+)\s*dB", re.IGNORECASE)
WPM_RE = re.compile(r"(?P<wpm>\d+)\s*(?:WPM|CWPM|BPS)", re.IGNORECASE)


def parse_spot_line(
    line: str,
    source_type: SourceType,
    endpoint_name: str,
    source_instance: str,
) -> Spot | None:
    match = DX_RE.match(line.strip())
    if not match:
        return None
    spotter = normalize_callsign(match.group("spotter"))
    dx = normalize_callsign(match.group("dx"))
    frequency = float(match.group("freq"))
    comment = (match.group("comment") or "").strip() or None
    snr_match = SNR_RE.search(comment or "")
    wpm_match = WPM_RE.search(comment or "")
    mode = infer_mode(str(source_type), comment, frequency)
    is_rbn = source_type in {SourceType.RBN_CW_RTTY, SourceType.RBN_FT8}
    return Spot(
        source=endpoint_name,
        source_type=source_type,
        endpoint_name=endpoint_name,
        source_instance=source_instance,
        spotter_callsign=spotter,
        spotted_callsign=dx,
        frequency_khz=frequency,
        band=frequency_to_band(frequency),
        mode=mode,
        comment=comment,
        snr=int(snr_match.group("snr")) if snr_match else None,
        speed_wpm=int(wpm_match.group("wpm")) if wpm_match else None,
        raw_line=line.rstrip("\r\n"),
        is_rbn=is_rbn,
        is_skimmer=is_rbn or "#" in spotter,
        is_human_spot=not is_rbn,
        confidence_score=0.6 if is_rbn else 0.7,
        timestamp_utc=datetime.now(UTC),
    )
