# Internal REGISTER request ownership candidate

The pinned SynthModem tunnel emits a VM SIP frame to `VmRegistrar`, which
answers REGISTER, then also forwards the same request to its learned UDP peer.
Once `SipUacInternal` owns that socket, it answers the unexpected REGISTER with
405. Both replies therefore reach the guest for the same transaction. This
matches the duplicate200/405 captured during long DOS/audio sessions.

The candidate gives synchronous `frame-rx` consumers an optional fifth argument,
`delivery`, whose `consumed` field suppresses subsequent UDP delivery. Existing
four-argument observers still receive every frame. The active registrar claims
only parsed REGISTER requests, including requests it rejects with400. Other SIP
messages, RTP and RTCP retain their existing routing. Stopping the registrar
removes its listener and releases ownership. No wire format changes.

```sh
./tools/modem-dev --command python3 lab/bbs/patches/synthmodem-registrar/check.py \
  --source build/bbs-lab/synthmodem-gateway-01/runtime/source \
  --output build/bbs-lab/synthmodem-registrar-new
```

The checker pins six source files against the accepted gateway receipt and
stages separate copies. Real loopback TCP carries framed VM-side fixture
datagrams to the actual tunnel; actual registrar and UAC use its UDP routing.
Baseline registration and refresh each receive200+405, and a missing Contact
receives400+405. Candidate transactions each receive one authoritative response.
Eight checks per variant also cover binding refresh, unaffected OPTIONS routing,
exact RTP/RTCP bytes, observer visibility, listener removal and clean closure.
See the [receipt](../../../../docs/validation/synthmodem-registrar.json).

This is isolated network/component evidence. It has not been composed into an
accepted VM/DOS runtime or installed service. Repeat real guest registration
refresh during an active DSP call and verify teardown before closing that gate.
It does not implement a general authenticated registrar. Source targets upstream
revision `b1752e4d0039e0cff72735924e03aa99922723a8`; upstream copyright/license
headers and the adjacent Telnet candidate's component notices remain intact.
