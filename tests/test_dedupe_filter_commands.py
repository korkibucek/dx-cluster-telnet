import asyncio
from datetime import UTC, datetime

from rbn_dxcluster.dedupe import SpotDeduplicator
from rbn_dxcluster.filtering import SpotFilter
from rbn_dxcluster.models import SourceType, Spot
from rbn_dxcluster.telnet import ClientSession, TelnetDXClusterServer


def make_spot(endpoint="a", freq=14025.0, dx="ZD7XYZ", source=SourceType.RBN_CW_RTTY):
    return Spot(
        source=endpoint,
        source_type=source,
        endpoint_name=endpoint,
        source_instance=f"{endpoint}/host:7000",
        spotter_callsign="MM0ABC-#",
        spotted_callsign=dx,
        frequency_khz=freq,
        band="20m",
        mode="CW",
        timestamp_utc=datetime.now(UTC),
        is_rbn=source != SourceType.CLASSIC_CLUSTER,
        is_skimmer=source != SourceType.CLASSIC_CLUSTER,
        is_human_spot=source == SourceType.CLASSIC_CLUSTER,
    )


def test_dedupe_merges_supporting_sources():
    dedupe = SpotDeduplicator(window_seconds=60, frequency_tolerance_khz=0.5)
    first_emit, first = dedupe.process(make_spot("rbn-main"))
    second_emit, merged = dedupe.process(make_spot("rbn-backup"))
    assert first_emit is True
    assert second_emit is False
    assert merged.id == first.id
    assert {e.endpoint_name for e in merged.supporting_sources} == {"rbn-main", "rbn-backup"}
    assert merged.confidence_score > first.confidence_score or len(merged.supporting_sources) == 2


def test_dedupe_does_not_merge_frequency_move():
    dedupe = SpotDeduplicator(window_seconds=60, frequency_tolerance_khz=0.5)
    assert dedupe.process(make_spot(freq=14025.0))[0] is True
    assert dedupe.process(make_spot(freq=14026.2))[0] is True


def test_filter_band_mode_and_skimmer():
    filt = SpotFilter(bands={"20m"}, modes={"CW"}, include_skimmer=False)
    assert filt.allows(make_spot(source=SourceType.CLASSIC_CLUSTER)) is True
    assert filt.allows(make_spot()) is False
    filt.include_skimmer = True
    assert filt.allows(make_spot()) is True


async def test_telnet_command_parser_updates_filters():
    server = TelnetDXClusterServer("127.0.0.1", 0, "banner", 10, 60)
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    transport, _ = await asyncio.get_running_loop().connect_read_pipe(
        lambda: protocol, open("/dev/null", "rb")
    )
    writer = asyncio.StreamWriter(transport, protocol, reader, asyncio.get_running_loop())
    session = ClientSession("K1ABC", writer, asyncio.Queue())
    saved = []
    server.filter_saver = lambda callsign, filt: saved.append((callsign, filt.to_dict()))
    assert await server.execute_command(session, "set/band 20m") == "Band filter updated"
    assert session.filter.bands == {"20m"}
    assert await server.execute_command(session, "unset/skimmer") == "Skimmer spots disabled"
    assert session.filter.include_skimmer is False
    assert saved[-1][0] == "K1ABC"
    assert saved[-1][1]["include_skimmer"] is False
    writer.close()
