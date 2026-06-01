import asyncio

from rbn_dxcluster.config import EndpointConfig, SourceCategoryConfig
from rbn_dxcluster.models import EndpointState, FeedStrategy, SourceType
from rbn_dxcluster.upstream import SourceSupervisor


async def test_active_active_starts_all_connectors(monkeypatch):
    queue = asyncio.Queue()
    cfg = SourceCategoryConfig(
        source_type=SourceType.RBN_CW_RTTY,
        strategy=FeedStrategy.ACTIVE_ACTIVE,
        endpoints=[
            EndpointConfig(name=f"rbn-{i}", host="localhost", port=7000 + i) for i in range(3)
        ],
    )
    supervisor = SourceSupervisor(cfg, queue)
    started = []
    for connector in supervisor.connectors:
        monkeypatch.setattr(connector, "start", lambda c=connector: started.append(c.endpoint.name))
    supervisor.start()
    assert started == ["rbn-0", "rbn-1", "rbn-2"]


async def test_endpoint_disable_does_not_disable_category(monkeypatch):
    queue = asyncio.Queue()
    cfg = SourceCategoryConfig(
        source_type=SourceType.CLASSIC_CLUSTER,
        strategy=FeedStrategy.ACTIVE_ACTIVE,
        endpoints=[
            EndpointConfig(name="cluster-1", host="localhost", port=7300),
            EndpointConfig(name="cluster-2", host="localhost", port=7301),
        ],
    )
    supervisor = SourceSupervisor(cfg, queue)

    async def fake_stop():
        return None

    monkeypatch.setattr(supervisor.connectors[0], "stop", fake_stop)
    assert await supervisor.disable_endpoint("cluster-1") is True
    assert supervisor.config.enabled is True
    assert supervisor.connectors[0].enabled is False
    assert supervisor.connectors[1].enabled is True


def test_endpoint_health_status_tracks_metrics():
    queue = asyncio.Queue()
    cfg = SourceCategoryConfig(
        source_type=SourceType.RBN_FT8,
        strategy=FeedStrategy.ACTIVE_ACTIVE,
        endpoints=[EndpointConfig(name="ft8", host="localhost", port=7001)],
    )
    supervisor = SourceSupervisor(cfg, queue)
    connector = supervisor.connectors[0]
    connector.metrics.state = EndpointState.ACTIVE
    connector.metrics.reconnect_count = 2
    connector.metrics.parse_errors = 3
    connector.metrics.mark_message()
    status = supervisor.statuses()[0]
    assert status.name == "ft8"
    assert status.state == EndpointState.ACTIVE
    assert status.reconnects == 2
    assert status.parse_errors == 3
    assert status.spots_per_minute == 1


def test_max_feeds_limits_connectors_to_ten():
    queue = asyncio.Queue()
    cfg = SourceCategoryConfig(
        source_type=SourceType.RBN_CW_RTTY,
        max_feeds=10,
        endpoints=[
            EndpointConfig(name=f"rbn-{i}", host="localhost", port=7000 + i) for i in range(12)
        ],
    )
    supervisor = SourceSupervisor(cfg, queue)
    assert len(supervisor.connectors) == 10
