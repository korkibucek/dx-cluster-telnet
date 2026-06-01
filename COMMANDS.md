# Telnet Commands

`rbn-dxcluster` accepts pragmatic DXSpider-like commands:

- `help` - show commands.
- `bye`, `quit`, `exit` - disconnect.
- `show/dx`, `sh/dx` - confirm live stream behaviour.
- `set/filter` - show filter guidance.
- `show/filter` - display current session filter.
- `clear/filter` - reset current session filter.
- `set/band 20m [15m ...]` - filter by band.
- `set/mode CW [FT8 ...]` - filter by mode.
- `set/source RBN_CW_RTTY [CLASSIC_CLUSTER ...]` - filter by source category.
- `set/skimmer`, `unset/skimmer` - include/exclude skimmer spots.
- `set/human`, `unset/human` - include/exclude human spots.
- `set/nodupes` - keep duplicate suppression enabled.
- `set/ve7cc-compatible on|off` - use a more verbose output variant.
- `who` - list connected callsigns.
- `show/version` - show server version.
- `show/sources`, `show/upstreams` - show feed health.

Authenticated admin HTTP endpoints are available for source and feed mutation: `POST /admin/enable-source?source=RBN_CW_RTTY`, `POST /admin/disable-source?source=RBN_CW_RTTY`, `POST /admin/enable-feed?endpoint=rbn-main`, `POST /admin/disable-feed?endpoint=rbn-main`, and `POST /admin/reconnect-feed?endpoint=rbn-main`. Set `admin.auth_token` and send it as `X-Admin-Token` or `Authorization: Bearer <token>`.
