# SynthModem source integration

The [integration receipt](validation/bridge-integration.json) binds a scoped
SynthModem patch,25 Telnet tests, seven session tests and two actual DOS/Enigma
paths. Local SynthModem commits6478ebd and7e5fc16 contain only the seven
proxy/collector/test/documentation targets. Existing VM/backend/performance and
configuration changes remain uncommitted outside this integration. No upstream
push or service restart was performed.

The public GPL-2.0-or-later
[integration patch](../lab/bbs/patches/synthmodem-menu-size/integration.patch)
replays with zero fuzz on f0e8d5f, produces seven files matching the workstation
source, and passes all25 Telnet tests in an isolated tree with generic config.
SynthModem attribution and COPYING are preserved. SIP/audio/DSP code is not
claimed as PCPlus reconstruction.

## Compatibility and the discovered heartbeat issue

Size probing is optional. An absent or zero `terminalSizeProbeTimeoutMs` emits
no CSI18t query and retains fixed geometry. Pre-patch golden wire bytes protect
that path. Enabled probes have bounded replies/typing, absolute deadlines,
split-CRLF handling, NAWS quoting, socket-identity guards and opaque binary data.
Timeout/malformed/overflow closes the failed probe without opening BBS TCP.
Do not enable it for terminals that cannot answer the query.

The existing heartbeat tests depended on a local positive interval and mistook
banner CRs for heartbeat bytes. Explicit fixture configuration revealed a real
pre-existing bug: ignored RX reset the TX keepalive deadline. The pre-patch
source fails exactly that one fixture test; the corrected source passes it and
a positive test showing real local-echo TX still defers the deadline. Configured
off remains off. This establishes timer/byte behavior, not a physical UART fix.

## DOS and remaining activation gates

The actual integrated proxy runs in isolated loopback processes against stock
Enigma with the reviewed terminal executable. Probe-enabled and fixed80x24 paths
both authenticate, open the unsaved editor, execute the external mode13h child,
restore the exact editor/cursor/shape, continue editing and abort the draft.
Independent audits match1920 cells per run with zero differences. The fixed
adapter supplies valid explicit PRM geometry while removing only the bridge's
size-query switch and adapting its expectation. No terminal reports or product
state are fabricated.

Seven session/backend tests exercise current CallSession work with stubbed
SIP/backend objects. They do not validate pending QEMU/modem/backend changes or
real SIP/audio. No bridge config, live service, DOS package selector or physical
installation changed. Activation remains separate because a restart would also
load the checkout's existing VM/backend changes; their readiness was requested
from bstar. Physical Boca/SPA2102/SIP/audio/CTS tests and complete PCPlus parity
remain open. The earlier large-file transfer receipts retain their exact staged
bridge identity and are not relabeled as integrated-runtime results.
