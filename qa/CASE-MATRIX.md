# Case matrix

| Group | IDs | Coverage |
|---|---|---|
| A | A1-A7 | Power button / state transitions / repeated taps contract via live backend smoke |
| B | B1-B5 | PROXY/TUNNEL mode transitions |
| C | C1-C9 | Server inventory, switching, transport presence |
| D | D1-D7 | status-json, exit IP, latency, state polling |
| E | E1-E6 | Subscription/refresh-related structural smoke; exact credential is never logged |
| F | F1-F4 | 11 profile smoke, default restoration |
| G | G1-G6 | full/killswitch/DNS, explicit privilege gate |
| H | H1-H8 | controlled failure/recovery smoke; destructive network/OOM cases are intentionally not fabricated |
| I | I1-I6 | install/release/sandbox entrypoint smoke |
| J | J1-J4 | responsiveness, status-json timing, 30x exit-IP ratio |
| K | K1-K6 | Wayland screenshot/UI sanity; destructive input requires explicit flag |
| L | L1-L5 | regression gate, syntax/compile/log scan |
