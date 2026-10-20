# DOS and owned ENiGMA over the software modem audio path

This runner connects the actual source-built DOS terminal and ASPECT child to
the [trained gateway](synthmodem-gateway.md), then exercises the already-running
owned stock ENiGMA lab. Local Hayes command control is synthetic; every online
byte passes through the real originating DSP, PCMU/RTP, external/internal SIP,
CallSession, pool, guest answering DSP, rebuilt helper and Telnet proxy.
There is no direct DOS-to-BBS data shortcut.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --runtime build/bbs-lab/synthmodem-sparse-runtime-01/runtime \
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

The separate read-only audit reconstructs guest DATA_RX, accounts for the exact
logged training-tail sink count before proxy attachment, compares all subsequent
bytes to DOS online input and Telnet application bytes, and requires the
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

## Current result: menus and cleanup pass; upstream bytes fail

`synthmodem-audio-dos-05` uses the Nix-built sparse-helper runtime, whose normal
init, DSP, kernel and39 gateway source files retain their accepted identities.
All19 producer checks pass: real training/login, Main -> Messages -> Main ->
Files, normal DOS return, matched42-byte UART snapshots and timer-vector
restoration, unchanged profile, selected-directory accounting and actual VM exit.
The script does not add a second N or change the BBS.

The independent audit still fails overall:18 of19 checks pass, but six bytes
`4e80c84432d3` are inserted after the DOS CPR (online byte offset29), before the
login keystroke. They exist in actual guest DATA_RX and BBS application input.
The [offline decoder](diagnose_audio_caller.js) recovers exactly all64 DOS online
bytes from recorded caller RTP, with no such insertion. RTP sequences/timestamps
are continuous. This narrows the investigation to actual guest RTP/jitter/DSP
consumption; the offline receiver cannot prove what that guest consumed.

Separately, the normal post-training hold reports discarding three bytes
`ff42f9` before the proxy attaches and CONNECT> is issued. The audit explicitly
accounts for that sink count, retains its raw prefix and still requires exact
post-hold equality. It does not trim the six online bytes or accept them because
login succeeded. All46908 bytes of downstream BBS display match, SIP teardown
and normal DOS restoration independently pass. The
[public receipt](../../docs/validation/synthmodem-audio-dos.json) stays failed.

The earlier -03 cohort remains failed on its held N. The new helper independently
reproduces and bounds that lookahead. Cohort -04 reaches main/message menus with
exact upstream bytes and39064 exact downstream bytes, but its script waits for
`Message Menu:` instead of this theme's actual `MESSAGE AREA`. It is stopped
after FAIL-MESSAGES; normal cleanup is not claimed. The final footer assumption
is also corrected from nonexistent `File Base >>` to the observed `File Base`
menu description. Those fixture failures and source identities remain preserved.

The sparse runtime can be reproduced with
[`synthmodem_sparse_runtime.py`](synthmodem_sparse_runtime.py); see the
[candidate instructions](patches/synthmodem-sparse/README.md). This is a test
runtime, not an installed bridge change.

## Full receive-trace cohort

Cohort `synthmodem-audio-dos-06` uses the explicit receive-trace option and the
accepted diagnostic image. It passes all19 producer and19 independent audit
checks with64 exact upstream bytes and46908 exact BBS display bytes. All menu,
SIP, RTP, normal DOS exit, UART and helper-vector checks pass. The guest dump
matches3559200 overlapping input PCM samples after a constant480-sample/60ms
delay. Offline native receivers recover exactly the DOS input from both external
caller RTP and actual guest pre-resampling PCM. No training-tail bytes occur in
this run. See [the trace guide](synthmodem-receive-trace.md) and
[PCM receipt](../../docs/validation/synthmodem-receive-pcm.json).

The earlier -05 failure remains preserved and unresolved. The additional
observers/export daemon and timing conditions are explicit; a clean diagnostic
run is not proof that the original intermittent insertion has been fixed. Next
compare paired rebuilt d-modem jitter policies under controlled timing, retain
actual guest PCM and repeat the full DOS byte audit.

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
cleanup before extended testing. Separate [REGISTER ownership](patches/synthmodem-registrar/README.md)
and [pool timer](patches/synthmodem-pool/README.md) candidates pass isolated
network/lifecycle checks; neither is composed into this runtime yet. Status
CRCRLF normalization and carrier/data ambiguity also remain open.
