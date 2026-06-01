from rbn_dxcluster.models import SourceType
from rbn_dxcluster.parsers import parse_spot_line
from rbn_dxcluster.radio import frequency_to_band, infer_mode, normalize_callsign


def test_frequency_to_band():
    assert frequency_to_band(14025.0) == "20m"
    assert frequency_to_band(50313.0) == "6m"
    assert frequency_to_band(999999.0) is None


def test_infer_mode_for_rbn_ft8_and_cw():
    assert infer_mode("RBN_FT8", "CQ", 14074.0) == "FT8"
    assert infer_mode("RBN_CW_RTTY", "CQ 25 dB", 14025.0) == "CW"
    assert infer_mode("CLASSIC_CLUSTER", "RTTY", 21090.0) == "RTTY"


def test_normalize_callsign():
    assert normalize_callsign(" mm0abc-#: ") == "MM0ABC-#"


def test_parse_rbn_line():
    spot = parse_spot_line(
        "DX de MM0ABC-#: 14025.0 ZD7XYZ CQ 25 dB 1234Z",
        SourceType.RBN_CW_RTTY,
        "rbn-main",
        "rbn-main/telnet.reversebeacon.net:7000",
    )
    assert spot is not None
    assert spot.spotter_callsign == "MM0ABC-#"
    assert spot.spotted_callsign == "ZD7XYZ"
    assert spot.band == "20m"
    assert spot.mode == "CW"
    assert spot.snr == 25
    assert spot.endpoint_name == "rbn-main"
    assert spot.source_instance.endswith(":7000")
    assert spot.is_rbn is True


def test_parse_classic_cluster_line():
    spot = parse_spot_line(
        "DX de K1ABC:  14200.0  G4XYZ nice signal 1510Z",
        SourceType.CLASSIC_CLUSTER,
        "cluster-1",
        "cluster-1/dx.example.net:7300",
    )
    assert spot is not None
    assert spot.is_human_spot is True
    assert spot.is_skimmer is False
