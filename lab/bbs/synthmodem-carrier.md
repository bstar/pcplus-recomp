# Carrier status across the normal software-modem runtime

The carrier-channel candidate now composes the client/helper with the Node
backend and normal VM startup. Actual software-DSP carrier loss and the complete
SIP/CallSession/Telnet gateway pass. This remains a separate lab runtime: no
installed service changes, physical acceptance or complete DOS/BBS audio
workflow is established by this checkpoint.

## Runtime and backend

The stager starts from the accepted lifecycle runtime. It changes one source
file (`PjsipBackend.js`) and exactly three existing boot archive entries:
`slmodemd`, `modemd-ctrl` and `S99modem-pjsip`. Init supplies the same
`SYNTHMODEM_CARRIER_PATH` to both processes, running as the existing `slmodemd`
user. The helper completes HELLO before waiting for the PTY. Kernel, NoDiscard
d-modem, other archive entries/metadata, existing lifecycle repairs and remaining
source files are unchanged. No diagnostic daemon or chardev is added. Both
replacement executables must match their Nix/host-test receipts.

The backend treats structured nocarrier, text failure, control HANGUP and
internal SIP termination as terminal for that backend instance. Before notifying
consumers it clears connection/rate state, cancels pending result parsing and
retires the data writer. Control/parser/asynchronous writer errors retire the
writer before emitting one error. Repeated termination, late data/CONNECT and
queued drain work cannot revive the instance. AT/data writes reject after
retirement. Explicit stop retires without another hangup. A new physical call
uses a newly created pool backend/VM.

Twelve parser/writer checks exercise these methods with modeled sockets. The
SIP-ended case supplies its transition directly; it is not evidence of an actual
peer-initiated SIP BYE.

## Actual carrier loss

The VM and native caller complete V.22/1200 training and exchange exact 287
upstream and 289 downstream bytes, including all byte values and literal
`NO CARRIER`. The test corks the real Node control socket, retaining 65,536
stream bytes and 134,512 writer bytes. Those bytes are deliberately abandoned
on carrier loss; they are not counted as transmitted.

The caller stops its modem waveform and sends real G.711 silence every 20 ms
while RTP continues. No connected flag, decoded byte or status is injected.
The guest DSP reaches its 700-ms carrier-loss threshold and executes modem stop.
The callback receives the helper acknowledgement before entering command mode
and writing result text. Node retires the writer before one hangup notification,
about 772 ms after waveform removal in cohort -02. Late transmission rejects.

All 15 producer checks pass. The independent audit checks raw frame boundaries,
ordered connect/nocarrier events, exact online bytes, absent leaked result text,
continuous RTP and final silence, plus actual guest log order: modem stop,
helper exit, idle state, result text. It also verifies pending-writer state,
notification state and frozen inputs/captures. Its 72 checks include identity
checks, not 72 independent protocol scenarios.

## Complete gateway

The existing gateway runner accepts `--carrier` with exact runtime validation.
All 26 checks pass: external/internal SIP, normal CallSession activation, real
DSP training, default post-training hold, CONNECT> destination entry,
BINARY/ANSI/80x25 negotiation and exact 534/538-byte duplex data. Remote TCP
close returns to CONNECT> while the modem carrier stays up. Another TCP
connection uses that same carrier. QUIT ends SIP and the pool registers a
distinct replacement VM. Both VMs exit; natural Node exit follows cleanup by
17.1 ms in the retained run.

This gateway uses a synthetic Telnet application peer. It does not run DOS,
ENiGMA or Synchronet, or cover every event race, packet-loss condition and
modulation protocol.

## Reproduction and remaining work

Use fresh output directories and the validated lifecycle runtime/earlier build
receipts. Staging does not update the accepted ledger automatically.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_carrier_runtime.py \
  --output build/bbs-lab/synthmodem-carrier-runtime-new
mkdir -p build/bbs-lab/carrier-backend-new
./tools/modem-dev --command node lab/bbs/test_carrier_backend.js \
  build/bbs-lab/synthmodem-carrier-runtime-01/runtime build/bbs-lab/carrier-backend-new
./tools/modem-dev --command python3 lab/bbs/synthmodem_carrier_vm.py \
  --runtime build/bbs-lab/synthmodem-carrier-runtime-01/runtime \
  --output build/bbs-lab/synthmodem-carrier-vm-new
./tools/modem-dev --command python3 lab/bbs/audit_carrier_vm.py \
  build/bbs-lab/synthmodem-carrier-vm-new
./tools/modem-dev --command python3 lab/bbs/synthmodem_gateway.py --carrier \
  --runtime build/bbs-lab/synthmodem-carrier-runtime-01/runtime \
  --output build/bbs-lab/synthmodem-carrier-gateway-new
```

The runtime commands use the accepted files pinned by the
[staging receipt](../../docs/validation/synthmodem-carrier-runtime.json).
See the [integration receipt](../../docs/validation/synthmodem-carrier.json) and
[client/helper groundwork](synthmodem-slmodem.md).

Next run actual DOS/ASPECT and stock BBS routes through this candidate, then
complete editors, sustained pressure and transfers across the audio path.
Physical Boca identity, SPA2102 commissioning, DCD/DTR behavior, V.8 compatibility
and negotiated 14,400-bps connectivity remain open. All full-application gates
remain open; this bridge checkpoint preserves the PCPlus rebuild objective.
