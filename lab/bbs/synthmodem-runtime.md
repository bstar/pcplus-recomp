# Normal VM answering-stack validation

The normal upstream init scripts now boot the real slmodemd/d-modem stack with
our Nix-built static i386 control helper. The Node backend uses its actual
constructor, QEMU startup, registrar, AT parser, INVITE/answer sequence, RTP
bridge and BYE/stop methods. No resource imports or methods are stubbed.

This advances beyond the [synthetic endpoint composition](synthmodem-vm.md).
It does not establish a modem handshake, a decoded data connection or physical
compatibility. The external test caller sends only PCMU silence over loopback.
It does not represent a Boca modem or implement an external SIP call to the
gateway; this test begins at the backend's internal SIP leg.

## Run

Use a clean checkout of upstream commit
`b1752e4d0039e0cff72735924e03aa99922723a8` under ignored build storage. The runner
verifies its Git identity and tracked cleanliness, stages source files and
overlays the exact nine-file pressure candidate from its existing receipt.
It preserves the original checkout and runtime media.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_runtime.py \
  --source build/bbs-lab/synthmodem-runtime-source \
  --candidate build/bbs-lab/synthmodem-pressure-05/candidate \
  --profile auto --output build/bbs-lab/synthmodem-runtime-auto-new

./tools/modem-dev --command python3 lab/bbs/synthmodem_runtime.py \
  --source build/bbs-lab/synthmodem-runtime-source \
  --candidate build/bbs-lab/synthmodem-pressure-05/candidate \
  --profile v32bis --output build/bbs-lab/synthmodem-runtime-v32bis-new
```

Choose fresh output directories. Run sequentially with upstream's loopback
UDP ports5062/10002/10003 free; the current backend does not offer independent
per-instance host tunnel ports. Node and QEMU come from the pinned Nix shell.
The Nix helper build is reused, and both downloaded VM media hashes are checked.
The new archive changes only `usr/local/bin/modemd-ctrl`: no lab init is added,
and every other archived file's bytes must remain identical. Runtime binaries,
archives and raw captures stay in ignored storage, outside DOS build inputs.

## Evidence

Both profiles require actual guest REGISTER readiness, helper HELLO, ATE0/ATI
and modulation queries, real RING-triggered ATA, negotiated PCMU media, at least
300 RTP packets in each direction, non-silent answering audio and absence of a
false modem CONNECT. They then require BYE teardown, released sockets/resources
and QEMU exit. The independently decoded guest SIP stream must contain the
INVITE and BYE 200 responses, so local TERMINATED state alone cannot count as
successful remote teardown. Python separately checks sent silence/sequence/
timestamps and decodes received G.711 mu-law samples to measure actual energy.

The `v32bis` profile sends `AT+MS=132,0,14400,14400` to the VM software answering
modem after RING, before ATA. It requires OK and actual guest datapump132
creation with tx/rx rates14400 and no `V8_ANS_SEND_ANSAM` log state. This command
is not a Boca initialization recommendation. The software modem's advertised
modulation list and its accepted configuration do not prove a shared protocol
or successful training with any external modem.

The pinned [modem.c](https://github.com/synexo/synthmodem/blob/b1752e4d0039e0cff72735924e03aa99922723a8/vm/slmodemd/modem.c)
maps132 to V32bis and routes default V34/V90/V92 selection through V8, whereas
an explicitly selected V32bis datapump takes the direct path. The real guest
trace confirms that entry path with the bundled DSP binary. This gives a
concrete non-V.8 configuration to investigate with the Boca, not proof of
V.32bis/14400 connectivity. Check the Boca's own manual and supported controls
independently before configuring its side.

The [receipt](../../docs/validation/synthmodem-runtime.json) retains separate
default and direct-V32bis cohorts, all39 staged source hashes, candidate pins,
Nix build/media identities, audio counts/energy and raw capture hashes.
Accepted cohorts are `synthmodem-runtime-auto-03` (18 checks) and
`synthmodem-runtime-v32bis-02` (19 checks). Each carries300 packets/48000 audio
samples in both directions. Received decoded peaks are3900 and4348 respectively;
these establish non-silent output, not handshake quality or negotiated rate.

The first pilot's two-second capture ended as answer-tone generation began,
and its harness expected ENDED instead of the actual TERMINATED UAC state.
Those assertions were corrected without changing production code. The first
V32bis probe also sampled the last asynchronous send before its bridge callback
ran (299 observed versus300 queued). The final harness waits for all queued
datagrams to reach the bridge before sampling; both earlier attempts remain
preserved as failures.

## Remaining integration

No call reaches modem data mode in this test. Next require an originating DSP
peer and actual negotiated duplex data through CallSession/Telnet, followed by
DOS/BBS workflows. The full external SIP server/session path, native flow credit,
serial-to-BBS TCP pressure, sustained audio timing, negotiated errors/retries,
Boca model/commands, SPA2102 configuration, audible physical handshake and actual
14.4 acceptance remain open. No installed service or live BBS is changed.
