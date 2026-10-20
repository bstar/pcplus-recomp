# SynthModem VM data pressure candidate

This isolated source candidate composes the earlier Telnet patch with changes
to upstream `PjsipBackend`, `CallSession` and `TelnetProxy`, plus the maintained
`ControlWriter.js`. Upstream revision is
`b1752e4d0039e0cff72735924e03aa99922723a8`. It does not change installed services,
VM images, the existing proxy candidate used by DOS/BBS receipts, or PCPlus.

The existing VM wire format permits4093 payload bytes. Upstream PjsipBackend
passes a whole write to its encoder, so a normal8192-byte payload throws. It
also ignores the socket's false return. CallSession catches and discards write
exceptions, leaving the call online without those bytes. The runner reproduces
all three observations in the actual baseline methods before testing the fix.

`ControlWriter` copies admitted payload into a fixed256KiB ring and writes
complete DATA_TX frames of at most4093 payload bytes. It preserves byte order
across ring wrap and retains the original encoder's Buffer/Uint8Array/string
input representations. A false socket write has accepted its whole frame; the
cursor advances once and waits for drain, so that frame is never resent. Extra
admission beyond retained bytes plus observed socket buffering throws before
changing the ring. Node's writable buffering remains separately governed by
its high-water mark plus an accepted frame; the ring bounds retained payload.

PjsipBackend returns readiness and relays writer drain/errors. CallSession
returns that value to the proxy and forwards drain only from its owned active
DSP. TelnetProxy pauses its BBS socket on false and resumes when that owner
drains. This also handles pressure before TCP connect; the new socket starts
paused if needed. The pressure flag survives returning to the bridge menu,
while final disconnect retires the callback. Session teardown removes its drain
listener, and backend stop retires the writer before awaited resource cleanup.

Capacity/unavailable/replaced-channel errors now cause the active call to hang
up instead of swallowing the loss and continuing. Errors while an asynchronous
drain is flushing retire the writer and reach the existing backend error event.
Closed or replaced sockets cannot flush stale queued bytes into another owner.
The native DSP's legacy undefined return is still accepted; this does not add
native DSP flow credit.

```sh
./tools/dev --command python3 lab/bbs/patches/synthmodem-pressure/check.py \
  --output build/bbs-lab/synthmodem-pressure-new
```

Choose a new output directory. The runner checksum-pins seven upstream files,
constructs the previous Telnet candidate as a baseline, applies this patch with
zero fuzz and stages a separate candidate. It starts no QEMU/SIP/DSP service
and installs no package. The actual Node methods run with modeled sockets and
unopened SIP/RTP/VM resources; only resource dependencies are substituted, not
the writer, serialization, parser or session/teardown methods. Negotiation is a
declared test boundary, supplied as an established connection.

Checks cover64KiB writes, wire limits, false/drain without replay, caller-buffer
mutation, ring wrap, atomic overflow rejection, asynchronous failure, replaced
channel rejection, session pause/resume, teardown/stale drains, fatal admission
and native compatibility. The actual proxy/session/backend also transfer16MiB
through two real loopback TCP servers while the VM-side reader starts paused.
The remote all-byte source is Telnet escaped; each VM frame is independently
length/type checked, BBS pause is observed and the recovered source is exact.
The existing1220-assertion Telnet suite runs against this composed candidate.

The first fixture failed because it supplied literal FF directly as Telnet
wire data. It was corrected to double IAC, without changing the codec. Earlier
attempts and their output are preserved under ignored build storage. Assertion
counts can vary with real TCP framing; byte equality and ownership requirements
are fixed.

Remaining work: combine this with the separately tested C control-helper in a
rebuilt VM, test the full SIP/DSP path and actual DOS/BBS sessions against that
combined build, add native DSP flow credit and serial-to-BBS write pressure,
then validate the Boca/SPA2102 hardware. Existing DOS/BBS passes retain their
earlier proxy hashes and do not test this new writer. This is not an end-to-end
analog modem compatibility claim.

Upstream: [SynthModem](https://github.com/synexo/synthmodem/tree/b1752e4d0039e0cff72735924e03aa99922723a8).
The patch includes GPL-2.0-or-later upstream excerpts. Maintained JavaScript is
GPL-2.0-or-later as marked; component attributions are preserved in the
[upstream notices](../synthmodem-telnet/UPSTREAM-NOTICES.txt).
