# Spot Sources

## Reverse Beacon Network CW/RTTY

Default endpoint: `telnet.reversebeacon.net:7000`. These spots are skimmer-originated and high volume. They are marked `source_type: RBN_CW_RTTY`, `is_rbn: true`, and `is_skimmer: true`.

## Reverse Beacon Network FT8

Default endpoint: `telnet.reversebeacon.net:7001`. FT8 reports are not human DX spots and are marked as RBN/skimmer reports.

## Classic DX Cluster

Classic cluster endpoints use the same line-oriented spot format but are normally human-originated. Configure one or more nodes under `classic_cluster`.

## Redundant feeds

Each category supports up to 10 configured endpoints. In `active_active`, all endpoints connect at once and duplicate suppression collapses repeated spots. Stored spots retain `supporting_sources` evidence showing all endpoints that reported the same spot.

## Future sources

The architecture reserves source types for DXSummit, PSK Reporter, WSPRnet, and local skimmers. They should emit the same `Spot` model and set source-specific flags honestly.
