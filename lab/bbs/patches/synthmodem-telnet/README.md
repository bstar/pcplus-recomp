# SynthModem Telnet transport candidate

This isolated candidate targets upstream SynthModem commit
`b1752e4d0039e0cff72735924e03aa99922723a8`. It implements the Telnet transport
needed between the answering modem DSP and a BBS. PCPlus stays a serial terminal.
No installed bridge, BBS, DOS executable, adapter or upstream repository is
modified. Nothing is deployed or submitted upstream.

Run with the pinned Nix toolchain and a new output directory:

```sh
./tools/dev --command python3 lab/bbs/patches/synthmodem-telnet/check.py \
  --output build/bbs-lab/synthmodem-telnet-new
```

The runner downloads only four checksum-pinned public source/configuration/notice
files into ignored build storage. It copies pristine and candidate variants,
applies `proxy.patch` with zero fuzz, and adds the maintained `TelnetCodec.js`.
It uses the actual upstream logger and configuration module. No npm install,
VM image, QEMU, modem DSP or SIP service is needed. These staged files are a
proxy test fixture, not a complete SynthModem installation.

The unmodified proxy reproduces five findings: incoming Telnet commands reach
serial display, literal FF is not escaped, single-byte Ctrl+] input drops into
the menu, the same byte in a larger chunk stays online, and NAWS reads the wrong
configuration section and advertises zero dimensions. A successful stock-defect
check means those failures were observed; it is not a stock compatibility pass.

The candidate:

- Parses Telnet as a stream across arbitrary input boundaries. Doubled IAC is
  decoded to FF, control commands stay out of serial display, and outgoing FF
  is doubled, including inside NAWS subnegotiation.
- Negotiates BINARY independently in each direction, SUPPRESS-GO-AHEAD, remote
  ECHO, local TTYPE and local NAWS. Pending enable requests distinguish crossed
  acknowledgments from new requests. This owner never initiates disable requests
  or queues reversals; it is not a general RFC1143 option manager.
- Answers TTYPE SEND using `config.telnet.terminalType` and uses
  `config.telnet.terminalCols/terminalRows` for NAWS. Choose the actual ANSI BBS
  profile and screen dimensions when preparing the hardware configuration.
- Retains NVT CR handling until BINARY is accepted. Incoming CR NUL becomes CR;
  CR LF is preserved. Outgoing serial CR immediately becomes CR NUL to avoid
  delaying Enter across input chunks. After BINARY, CR/NUL and every other byte
  remain data. If a server refuses BINARY, arbitrary file transparency is not
  established. Disabling initial offers still parses/responds to server options.
- Disables in-band menu escapes by default. `config.telnet.proxyEscapeByte`
  may explicitly select an integer byte0..255; that byte is then consumed in
  every chunk layout. Keep it unset/null for binary transfers. Remote TCP close
  still returns to CONNECT>, and QUIT in that menu requests modem disconnect.
- Bounds retained subnegotiation to1024 bytes, discards malformed/oversize
  payload until IAC SE, and recovers the subsequent data stream.
- Clears connection timers/parser ownership on close, and rejects delayed
  data/error/close callbacks from a prior socket after a reconnect.

The protocol references are [RFC854](https://www.rfc-editor.org/rfc/rfc854),
[RFC856 BINARY](https://www.rfc-editor.org/rfc/rfc856),
[RFC1091 TTYPE](https://www.rfc-editor.org/rfc/rfc1091) and
[RFC1073 NAWS](https://www.rfc-editor.org/rfc/rfc1073).
This is a tested implementation subset, not a full Telnet conformance claim.

## Evidence and remaining acceptance

The receipt records source/patch/tool hashes and assertions. Deterministic
socket tests execute actual stock/candidate class methods without replacing
their parser or state machine. They cover all256 byte values at every two-chunk
split and as singleton chunks, fragmented negotiation, crossed/duplicate offers,
refusals, NVT, malformed/oversize subnegotiation, explicit escape opt-in and stale
socket events. A separate real loopback TCP server verifies complete-byte duplex
transport, actual TTYPE/NAWS replies and return to the menu on remote close.
The initial loopback attempt failed because its test began payload accounting
before the final NAWS reply arrived. The final test waits for both TTYPE and NAWS;
the failed attempt is retained separately under ignored build storage.

No test uses modem audio, SIP/RTP, real PCPlus, a real BBS, line-rate pacing or
physical DCD/CTS. DSP-to-proxy backpressure under a slow modem, disconnect during
training, full error/timeout routes, large file transfers and a real DOS client
against Synchronet/ENiGMA remain required. The original PCPlus implementation
work and whole-application gates remain open. The
[hardware plan](../../../../docs/ANALOG_MODEM_INTEGRATION.md) retains V.8/14.4
uncertainty and adapter-arrival dependencies.

Upstream source: [SynthModem](https://github.com/synexo/synthmodem/tree/b1752e4d0039e0cff72735924e03aa99922723a8).
The patch includes excerpts of its GPL-2.0-or-later source; preserved upstream
attributions are in [UPSTREAM-NOTICES.txt](UPSTREAM-NOTICES.txt). Maintained
candidate/test JavaScript is GPL-2.0-or-later as marked in its headers.
