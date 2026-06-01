from __future__ import annotations

from .models import Spot


def format_spot(spot: Spot, mode: str = "classic") -> str:
    timez = spot.timestamp_utc.strftime("%H%MZ")
    marker = "#" if spot.is_skimmer else ""
    spotter = f"{spot.spotter_callsign}{marker}"
    comment_parts = []
    if spot.comment:
        comment_parts.append(spot.comment)
    if spot.snr is not None and "db" not in (spot.comment or "").lower():
        comment_parts.append(f"{spot.snr} dB")
    if mode == "verbose":
        comment_parts.append(
            f"[{spot.source_type}:{spot.endpoint_name} conf={spot.confidence_score:.1f}]"
        )
    elif spot.is_rbn:
        comment_parts.append(f"[{spot.mode or 'RBN'} {spot.endpoint_name}]")
    comment = " ".join(comment_parts)[:43]
    return f"DX de {spotter:<10}: {spot.frequency_khz:8.1f}  {spot.spotted_callsign:<12} {comment:<43} {timez}\r\n"
