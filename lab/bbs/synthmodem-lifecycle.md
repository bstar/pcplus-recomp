# Pool and registrar integration

The combined normal gateway now includes the tested warmup-timer and REGISTER
ownership fixes alongside the rebuilt DISCARD_NONE d-modem. Exactly three source
files change: `ModemBackendPool.js`, `VmRegistrar.js` and `UdpTcpTunnel.js`.
The kernel, normal initrd, answering DSP, helper and d-modem are byte-identical
to the accepted rebuilt gateway. No installed service or BBS is modified.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_lifecycle_runtime.py \
  --output build/bbs-lab/lifecycle-runtime-new
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --runtime build/bbs-lab/lifecycle-runtime-new/runtime --lifecycle \
  --output build/bbs-lab/dos-lifecycle-new
./tools/modem-dev --command python3 lab/bbs/audit_synthmodem_audio_dos.py \
  build/bbs-lab/dos-lifecycle-new
./tools/modem-dev --command python3 lab/bbs/audit_lifecycle_sip.py \
  build/bbs-lab/dos-lifecycle-new \
  --baseline build/bbs-lab/synthmodem-audio-dos-07
```

Use fresh directories and the accepted local runtime prerequisites. The stager
pins patch hashes against their isolated receipts, applies them with zero fuzz,
and requires every output file to match the accepted identities. It permits
only the three declared JavaScript changes; the normal boot archive is unchanged.

## Actual DOS and REGISTER refresh

Cohort -08 passes 19 producer and 19 independent byte-audit checks: numeric
dialing, real DSP CONNECT, online destination entry, authentication, Main ->
Messages -> Main -> Files, exact 64 upstream and 46,908 downstream bytes, normal
DOS return, UART/vector restoration, directory accounting and SIP/VM cleanup.

A diagnostic observer records the actual internal TCP tunnel in both directions.
It preserves socket write arguments, return values and callbacks. The independent
SIP audit reconstructs framed datagrams and identifies the guest's real refresh
inside the active ACK/BYE dialog. That request receives exactly one 200 response,
and the guest's own log confirms reception. No 405 or duplicate UAC warning occurs.
The preserved -07 baseline shows 200 and 405 for its refresh transaction.

All 11 SIP audit checks pass, including actual peer consumption, captured byte
hashes and a runtime comparison showing only the three lifecycle files differ.
Raw SIP/media/session captures remain in ignored build storage.

## Fresh VM and natural process exit

The short gateway scenario exercises actual external/internal SIP, CallSession,
pool, both DSPs, Telnet BINARY/ANSI/80x25, exact 534/538-byte duplex payloads,
TCP reconnect on one carrier, QUIT, a distinct warm replacement VM and cleanup.
It then records Node's natural beforeExit event and the parent-observed process
exit, rather than forcing process termination or unrefing the timer.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_gateway.py \
  --runtime build/bbs-lab/lifecycle-runtime-new/runtime --lifecycle \
  --output build/bbs-lab/lifecycle-gateway-new
# Paired unpatched pool/registrar baseline, with the same rebuilt modem:
./tools/modem-dev --command python3 lab/bbs/synthmodem_gateway.py \
  --runtime build/bbs-lab/synthmodem-jitter-runtime-01/runtime \
  --dmodem candidate --output build/bbs-lab/lifecycle-gateway-baseline-new
```

The candidate passes all 26 checks, including the timer-release gate. After its
fresh replacement VM and sockets close, Node exits in 39.8 ms. The baseline
passes its 25 transport/cleanup checks but remains alive for 40.53 seconds on
the unused warmup timer. The beforeExit hook independently measures 2.73 ms
versus 40.51 seconds after logical cleanup. Both actual VM processes exit in
both runs; the difference is the remaining referenced timer.

The gateway audit accounts for the exact logged pre-proxy training-tail sink
count and retains any prefix; it still requires exact user bytes after attachment.
It does not trim online corruption or accept authentication alone as compatibility.

See the [combined receipt](../../docs/validation/synthmodem-lifecycle.json).
The earlier isolated [pool](patches/synthmodem-pool/README.md) and
[registrar](patches/synthmodem-registrar/README.md) receipts retain their scopes.
The separate [carrier runtime](synthmodem-carrier.md) now resolves the tested
carrier/data ambiguity and passes the actual DOS menu route. This lifecycle-only
image retains its original scope. Editor/file-transfer workflows through audio,
sustained pressure/faults, all whole-application gates and physical
Boca/SPA2102 acceptance remain open. No negotiated 14.4 kbps claim is made.
