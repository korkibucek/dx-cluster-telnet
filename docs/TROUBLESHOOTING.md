# Troubleshooting

## No spots arrive

1. Check `show/sources` from Telnet.
2. Check `curl http://127.0.0.1:8080/sources`.
3. Verify outbound TCP access to upstream hosts and ports.
4. Reduce filters with `clear/filter`.

## Too many spots

Disable FT8 RBN, use `set/band`/`set/mode`, or lower endpoint `max_messages_per_minute`.

## Duplicate spots

Keep `dedupe.enabled: true` and tune `window_seconds` plus `frequency_tolerance_khz`.
