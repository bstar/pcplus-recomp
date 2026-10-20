# Configurable RTP listener interface

This isolated patch adds `config.rtp.bindAddress` to the composed SynthModem
candidate. Its default is `0.0.0.0`, preserving LAN caller reachability. Local
labs set `127.0.0.1` before importing the runtime. The setting controls all three
RTP bind paths: raw CallSession B2BUA sockets, native RtpSession.open and the
port allocator's availability probe. SIP has its own existing `config.sip.host`.
The internal VM tunnel continues to use its existing loopback bindings.

The patch applies after the pressure candidate against pinned upstream commit
`b1752e4d0039e0cff72735924e03aa99922723a8`. It changes only `config.js`,
`src/session/CallSession.js` and `src/rtp/RtpSession.js`. It does not replace
audio, SIP, pool or session methods with test doubles. Upstream licensing and
[notices](../synthmodem-telnet/UPSTREAM-NOTICES.txt) remain applicable.

```sh
./tools/modem-dev --command node lab/bbs/patches/synthmodem-bind/check.js \
  build/bbs-lab/synthmodem-gateway-01/runtime/source \
  build/bbs-lab/synthmodem-bind-new
```

The checker requires a fresh output directory. Its four checks verify the
default, actual native binding and port allocation against a competing socket
on127.0.0.2. A wildcard bind would conflict, while the selected127.0.0.1 bind
can coexist on the same port. It records checker/patch/source hashes in the
[receipt](../../../../docs/validation/synthmodem-bind.json). The separate
[full gateway test](../../synthmodem-gateway.md) verifies normal CallSession
setup binds its actual RTP socket to loopback. No installed service is changed.
