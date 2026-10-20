# DOS and owned ENiGMA over the software modem audio path

This runner connects the actual source-built DOS terminal and ASPECT child to
the [trained gateway](synthmodem-gateway.md), then exercises the already-running
owned stock ENiGMA lab. Local Hayes command control is synthetic; every online
byte passes through the real originating DSP, PCMU/RTP, external/internal SIP,
CallSession, pool, guest answering DSP, rebuilt helper and Telnet proxy.
There is no direct DOS-to-BBS data shortcut.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --runtime build/bbs-lab/synthmodem-gateway-01/runtime \
  --output build/bbs-lab/synthmodem-audio-dos-new

./tools/modem-dev --command python3 lab/bbs/audit_synthmodem_audio_dos.py \
  build/bbs-lab/synthmodem-audio-dos-new
```

Use a fresh directory and the owned ENiGMA process on127.0.0.1:23233. The runner
verifies that process's cwd, pinned source revision and tracked cleanliness,
then freezes its configuration/menu/core identities. It neither restarts nor
patches the server and never uses the live LAN board. The optional Nix modem
shell supplies DOSBox-X and NASM as well as Node/QEMU/Python. Original runtime
inputs, application binaries and installed services remain unchanged.

## Workflow and evidence

DOS imports an owned PRM and a synthetic directory entry whose telephone target
is1 and whose script binding is AUDIO. ATZ returns a local OK; ATD1 starts a
real SIP/DSP connection. The adapter emits CONNECT1200 only after both DSPs
connect. The DOS script waits for the gateway's actual CONNECT> before
transmitting a loopback hostname:port as online data. That destination is never
part of the ATD telephone command.

The maintained ASPECT compiler produces the fixture script without a vendor
compiler. The actual DOS child follows matrix/form prompts, sends only the
synthetic loclab credentials and handles pause/newscan prompts with WHEN CALL.
It then requires Main -> Messages -> Main -> Files and writes an owned success
marker only after reaching the final prompt and draining output. Each stage
closes its own log file so progress can be inspected while the process is live.
The raw serial/Telnet streams and authoritative ENiGMA session log must agree
with successful authentication and that menu order.

A test-only INT1C helper reads the displayed File Base footer and, after a
ten-second dwell, inserts Alt-X through BIOS INT16/AH05. It does not write
application memory, send serial replies or manufacture screen text. It restores
the original timer vector before injecting the key. A separate DOS program
samples that vector after return; the original/restored values must match.
Before/after42-byte UART/PIC/vector snapshots, normal DOS return, exact selected
directory accounting and the final file-menu screen are also required.

The separate read-only audit reconstructs guest DATA_RX, compares DOS online
bytes to actual guest-decoded input and Telnet application bytes, requires the
entire BBS display in decoded audio, and compares decoded audio with serial
output. It independently checks actual DOS DA/CPR responses, one guest carrier,
RTP continuity, SIP teardown, server menu order, success markers, capture hashes
and restored hardware/vector state. Raw captures, runtime images, compiled
fixtures and all credential-bearing files remain under ignored build storage.

## Preserved fixture failures

The first preparation attempt failed a NASM resident-size expression before
starting the gateway or DOS. The next attempt authenticated but used one long
WAITFOR240 while WHEN handlers were deferred until that command returned. It
therefore failed its main-menu wait. Its keyboard fixture also expected a
PROGRAM return pause which successful online scripts deliberately bypass.
That invalid run was stopped and retained; it is not a menu pass. Its decoded
16098-byte BBS display and both upstream byte comparisons remain exact.

The corrected script uses short WAITFOR polling and the helper watches the
actual final menu. The harness owns a separate emulator process group so a
forced test stop can also retire quit-dialog descendants retaining its serial
socket. A forced stop never counts as normal DOS return or hardware restoration.

## Current result: authentication passes, menu route fails

The corrected `synthmodem-audio-dos-03` attempt authenticates and advances through
login artwork, last callers, online users and oneliners. At the newscan prompt,
the DOS serial stream contains a final N which never appears in guest DATA_RX
or the BBS application stream. All preceding upstream bytes match exactly, and
all23773 bytes of BBS display are present in decoded caller audio. The captured
caller RTP sequence/timestamps are continuous.

An [offline decoder](diagnose_audio_caller.js) independently recovers N at
caller packet11541. That proves the byte was modulated into the observed caller
audio; it does not prove what the VM's internal RTP/jitter or proprietary DSP
receiver consumed. The record in
[validation](../../docs/validation/synthmodem-audio-dos.json) remains failed.
The run was stopped after its explicit FAIL-MAIN marker; normal exit, final
menu and UART/helper restoration are not claimed for either stopped attempt.

Subsequent [helper isolation](patches/synthmodem-sparse/README.md) reproduces an
indefinite N hold on a raw host PTY: the in-band NO CARRIER parser waits for
another byte. A bounded-lookahead candidate passes the sparse-prefix and prior
transport checks and builds as static i386. This identifies a concrete cause
consistent with the audio symptom without assigning the loss to DSP decoding.
The candidate has not yet been booted or tested in this workflow. Next stage a
separate runtime, verify sparse data over DSP and repeat this complete route.
Do not mask the failure with duplicate keystrokes or count authentication alone
as ENiGMA workflow compatibility. Literal carrier-text collisions remain open.

## Limits and remaining tasks

This is a fixed V.22/1200 software line with38400 8N1 HARD on the emulated DOS
UART. DOSBox-X holds modem status/CTS ready; physical IRQ/CTS/DCD/DTR behavior
is not established. The front end does not emulate a Boca command set beyond
the declared local ATZ/ATD1 control. The PRM uses an empty software hangup string
and modeled DTR cleanup; physical hangup behavior still needs hardware tests.

Editor keys, file transfers, sustained load/fault recovery, Synchronet over this
audio path, other modulations and actual Boca/SPA2102 acceptance remain separate.
No14400-bps connectivity follows from this1200-bps test.

During the longer preserved run, a real guest registration refresh received a
200 from VmRegistrar and an additional405 from SipUacInternal for the same
transaction. Registration succeeded, but the duplicated request ownership needs
cleanup before extended testing. This is distinct from the script fixture
failure. Existing pool timeout retention and status CRCRLF normalization are
also still open.
