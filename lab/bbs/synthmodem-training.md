# Negotiated V.22 DSP data path

The originating native DSP now trains with the normal VM answering stack at
V.22/1200 and exchanges decoded all-byte payloads in both directions. This is
real software modulation/demodulation over PCMU/RTP, through the Nix-rebuilt
control helper. No CONNECT flag or decoded payload is supplied by the harness.
The full external SIP server, DOS/BBS and physical modem/ATA are outside this
checkpoint.

## Reproduce

First create the accepted normal-stack runtime described in
[normal runtime validation](synthmodem-runtime.md). The training runner verifies
all39 source files and both boot inputs against that recorded receipt. A new
directory copies those inputs and applies only the isolated
[originating V.22 patch](patches/synthmodem-v22/README.md). Original runtime,
upstream checkout and installed services remain unchanged.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_training.py \
  --runtime build/bbs-lab/synthmodem-runtime-auto-03 \
  --v22-patch lab/bbs/patches/synthmodem-v22/originate.patch \
  --output build/bbs-lab/synthmodem-training-v22-new
```

Use a fresh output directory and free loopback tunnel ports5062/10002/10003.
Omitting `--v22-patch` exercises the stock originating wrapper for comparison.
The baseline cohorts fail their CONNECT deadline;
both decoded streams are empty despite active RTP. Its audio contains premature
low-channel unscrambled marking and an inappropriate1800Hz guard tone. That
failure is not a Boca test or proof that the answering backend cannot do V.22.

## Path and assertions

The actual PjsipBackend boots normal guest init and learns the real d-modem SIP
registration. The software answering modem receives `AT&K0`,
`AT+MS=22,0,1200,1200`, `AT\N0` and `AT%C0` through the actual RING/init/ATA
sequence. These commands configure only the VM modem; do not copy them to the
unidentified Boca. Error correction, compression and local PTY flow are disabled
for this fixed, uncompressed DSP test.

The real native ModemDSP originates in forced V22 mode through RtpSession with
explicit immediate playout. All sockets bind loopback via the supported adopt
API. Both DSPs must report1200 before either payload is written. Each1058-byte
stream contains a directional marker, four cycles of all256 byte values and an
end marker. Both complete decoded streams must equal their expected payloads;
prefix/suffix garbage cannot pass. Python reconstructs every guest control frame
and requires its concatenated DATA_RX to equal the caller payload. It also
audits both captured RTP streams for valid PCMU framing, sequence/timestamp
continuity and consistent SSRC. Teardown uses actual SIP BYE and backend stop.

The [receipt](../../docs/validation/synthmodem-training.json) records exact source
and boot inputs, candidate patch, signal checks, both CONNECT events, payload
hashes, raw audio/control capture hashes and resource cleanup. It preserves the
baseline failure alongside the successful candidate rather than replacing it.
Runtime images, binaries and captures remain under ignored build storage.

Accepted candidate cohort: `synthmodem-training-v22-05`, with13 VM/data/audit
checks and117 signal/waveform regressions. Both decoded streams are exactly1058
bytes; caller-to-answer SHA256 is
`f1a3ad234d1fa81180d1e6aeabf3c6daa61c1d987fcc3dcbf45c9a838af9ff99`,
and answer-to-caller SHA256 is
`6643289a966bafef22fac86f87f1867f2d17deb476346894def2f0fcf6fc35c5`.
The final baseline comparison uses the same harness without the source patch.
Earlier successful candidate probes are retained separately. One expanded
audit initially rejected RTP's valid marker bit; its payload type check was
corrected without changing either DSP. The accepted audit masks off the marker
bit when checking payload type.

## Remaining work

This checkpoint establishes one fixed-rate software caller/answerer data path.
It uses an internal SIP call and direct backend bytes, without CallSession's
post-training attachment, Telnet proxy, DOS terminal or a BBS. Add those layers
with the same trained DSP transport before calling the full gateway validated.
Other modulation protocols, error correction/compression, sustained timing and
loss recovery, native flow credit, reverse TCP pressure and physical
Boca/SPA2102 compatibility remain open. The separate V32bis datapump entry
probe still does not establish a14400-bps connection.
