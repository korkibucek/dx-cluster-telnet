import asyncio

from rbn_dxcluster.admin import AdminServer
from rbn_dxcluster.app import DXClusterApp
from rbn_dxcluster.config import AppConfig, EndpointConfig, SourceCategoryConfig
from rbn_dxcluster.filtering import SpotFilter
from rbn_dxcluster.models import EndpointState, SourceType
from rbn_dxcluster.storage import SQLiteStore


async def test_admin_requires_token_for_mutating_actions():
    async def action_handler(action, params):
        return 202, {"action": action, "params": params}

    server = AdminServer(
        "127.0.0.1",
        0,
        lambda: {},
        lambda: "sources",
        action_handler,
        auth_token="secret",
    )
    await server.start()
    assert server._server is not None
    port = server._server.sockets[0].getsockname()[1]

    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(b"POST /admin/disable-feed?endpoint=rbn-main HTTP/1.1\r\nHost: local\r\n\r\n")
    await writer.drain()
    response = await reader.read()
    assert b"401 Unauthorized" in response

    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(
        b"POST /admin/disable-feed?endpoint=rbn-main HTTP/1.1\r\n"
        b"Host: local\r\nX-Admin-Token: secret\r\n\r\n"
    )
    await writer.drain()
    response = await reader.read()
    assert b"202 Accepted" in response
    assert b"disable-feed" in response
    await server.stop()


def test_sqlite_store_persists_filters(tmp_path):
    store = SQLiteStore(f"sqlite:///{tmp_path / 'cluster.sqlite3'}")
    filt = SpotFilter(bands={"20m"}, modes={"CW"}, include_skimmer=False)
    store.save_filter("k1abc", filt)
    loaded = store.load_filter("K1ABC")
    assert loaded is not None
    assert loaded.bands == {"20m"}
    assert loaded.modes == {"CW"}
    assert loaded.include_skimmer is False


async def test_app_admin_action_disables_one_feed_not_category(monkeypatch, tmp_path):
    cfg = AppConfig(
        database_url=f"sqlite:///{tmp_path / 'cluster.sqlite3'}",
        upstreams={
            SourceType.RBN_CW_RTTY: SourceCategoryConfig(
                source_type=SourceType.RBN_CW_RTTY,
                endpoints=[
                    EndpointConfig(name="rbn-main", host="localhost", port=7000),
                    EndpointConfig(name="rbn-backup", host="localhost", port=7001),
                ],
            )
        },
    )
    app = DXClusterApp(cfg)

    async def fake_stop():
        return None

    monkeypatch.setattr(app.supervisors[0].connectors[0], "stop", fake_stop)
    status, payload = await app.handle_admin_action("disable-feed", {"endpoint": "rbn-main"})
    assert status == 202
    assert payload["endpoint"] == "rbn-main"
    assert app.supervisors[0].config.enabled is True
    assert app.supervisors[0].connectors[0].enabled is False
    assert app.supervisors[0].connectors[0].metrics.state == EndpointState.DISABLED
    assert app.supervisors[0].connectors[1].enabled is True
