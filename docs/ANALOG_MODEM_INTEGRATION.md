# Boca / SPA2102 / SynthModem integration target

Compatibility is the priority. This adds a hardware acceptance target to the
ongoing source-built DOS PCPlus reconstruction; it does not replace the full
application plan or establish hardware compatibility. Hardware testing remains
planned; DOS/bridge software checkpoints are recorded below. No adapter, analog
carrier, handshake audio or Boca test has run.

## Equipment and connection

- DOS PC with Boca 14.4 kbps ISA modem; exact model, chipset, UART, jumpers,
  I/O base, IRQ and supported AT command set still need identification.
- Ordered unlocked Cisco/Linksys SPA2102, administrator access and power supply;
  adapter has not arrived. Ethernet and RJ11 cables are available.
- Linux Framework workstation on the same home router/switch.

```text
PCPlus -> Boca ISA modem -> RJ11 -> SPA2102 PHONE 1
                                     INTERNET -> home router/switch
Linux Framework workstation --------------------> same router/switch
  SynthModem: local SIP/RTP + answering modem DSP -> remote Telnet BBS
```

SynthModem runs on Linux. Keep the SPA2102's existing firmware; configure SIP
and audio there. SIP, RTP, DNS, TCP and Telnet remain bridge responsibilities.
PCPlus remains a serial modem terminal. The modem originates a call to the
local answering service; after a genuine modem handshake and carrier CONNECT,
SynthModem displays `CONNECT>`. Enter `hostname` or `hostname:port` there.
Do not send an Internet hostname to the Boca as an ATDT telephone number.

The existing `/D:bbs.example:23` documentation describes the emulated Hayes/TCP
lab. For this hardware use a documented local dial string/number routed by the
ATA, then enter the BBS address as terminal data. An ATA speed-dial/direct-SIP
rule may permit an empty ATDT target, but the current CLI requires a nonempty
explicit target: do not presume that combination works. Choose a supported
numeric local dial rule or address this UI gap deliberately.

## Source review and concrete PCPlus gaps

Reviewed maintained source, not original binaries. Existing emulator/replay
receipts remain scoped to those environments.

| Requirement | Current implementation and remaining acceptance |
| --- | --- |
| COM / base / IRQ | `src/config/terminal_import.c` accepts COM1..4 at 3F8/2F8/3E8/2E8, IRQ4/3/4/3. `setup_model.c` enforces those pairs. The separate [child IRQ extension](CUSTOM_IRQ.md) now tests3/4/5/7, but parent setup/v7/helper integration remains open. Nonstandard ISA jumper settings are not yet supported by the composed application; shared IRQs remain unsupported. Identify the Boca configuration first. |
| 8N1 / DTE speed | Import and setup support 8N1 and selectable 300,1200,2400,4800,9600,19200,38400,57600,115200 baud. DTE speed is distinct from negotiated line rate. Choose a documented fixed DTE rate supported by this modem/UART; start conservatively and measure overruns. |
| RTS/CTS | Hardware flow can be enabled independently; bounded TX waits service cancellation/deadlines. Prefer HARD with software flow off for binary acceptance, provided Boca flow configuration matches. Physical CTS stalls, RTS receive backpressure and FIFO/UART behavior remain untested. |
| DCD | `connection.asm` samples MSR bit7 online and detects loss only after seeing DCD high in that session. A forced-high DCD profile hides loss; a carrier that never asserts DCD is not rejected. Verify modem carrier-following behavior and both failure cases. |
| DTR / hangup | Configured hangup string and optional DTR drop/restore exist. Drop lasts 18 BIOS ticks (about one second). Actual modem DTR response, escape guards, carrier teardown and subsequent redial need testing. |
| Result codes | Configurable eleven-slot legacy byte matcher is case-sensitive and first-completion wins. Generic CONNECT in slot0 can beat a speed-specific result and autobaud can select 300. No 14400/57600/115200 response-rate slots; numeric and firmware suffix variants need fixtures/policy. For initial fixed-DTE tests disable autobaud and capture actual verbose results. |
| Initialization | Six configurable command buffers and caret expansion exist. Init is limited to 46 content bytes; dial/hangup buffers to 24. Identify supported commands and speaker controls from Boca documentation. No assumed AT+MS, reset profile, &K, &C or &D settings. Preserve audible handshake through supported speaker settings. |
| Timeouts | Dial timeout is configurable 1..32767 seconds and covers init/send/wait together. Cancellation has bounded cleanup. Modem S7, bridge training and later Telnet connect/idle timers are separate. One BIOS tick per ordinary command byte adds setup delay; measure total and choose explicit budgets. |
| ANSI / CP437 | Preserve 8-bit data, supported ANSI BBS profile, font and intended translation settings. Check all high-bit bytes and box drawing through the whole bridge; do not convert the serial stream to UTF-8. |

See [connection controller](CONNECTION.md), [configuration](MODEM_CONFIGURATION.md),
[live serial settings](SERIAL_LIVE.md), [UART](UART.md) and
[port handoff](PORT_HANDOFF.md). Existing ENiGMA immediate-forwarding Home/Insert
failures remain open; a buffered or patched-server pass is separate evidence.

## SynthModem backend investigation

The [accepted normal software audio download](validation/synthmodem-audio-download-03.json)
now verifies one11521-byte automatic ENiGMA transfer at V.22/1200 with fixed38400
DTE: complete file/CRC/ZFIN/OO, actual post-helper search/list, full byte identity
and normal DOS/UART/IRQ/timer return. It uses the unchanged stock local BBS and
explicit250ms bridge key framing. The earlier deadline and queued-completion
failures remain retained. Uploads, cancellation/loss/pressure and Synchronet over
audio remain software work items; this closes no physical commissioning gate.

Upstream reviewed at commit `b1752e4d0039e0cff72735924e03aa99922723a8`.
Links below pin the reviewed source; future versions require rechecking.

- [README](https://github.com/synexo/synthmodem/blob/b1752e4d0039e0cff72735924e03aa99922723a8/README.md)
  describes `auto`, VM-backed `slmodemd-pjsip`, and JavaScript `native` backends.
  Upstream reports high-rate connections on its hardware; that is not evidence
  for our unidentified Boca.
- [CallSession.js](https://github.com/synexo/synthmodem/blob/b1752e4d0039e0cff72735924e03aa99922723a8/src/session/CallSession.js)
  starts auto calls on the VM backend, then swaps to native after pre-CONNECT
  silence hangup interpreted as V.8 timeout. Native's legacy chain is
  V.22bis -> V.21 -> Bell103. This source review does not prove that every
  such hangup means missing V.8, or that this Boca can complete the swap.
- Native does not provide V.32/V.32bis. If this 14.4 Boca lacks V.8, auto's
  fallback is not a demonstrated 14.4 path. Establish a supported low-speed
  baseline (V.22/1200 or V.22bis/2400 if documented by the modem), then investigate
  legacy V.32bis answering on the VM backend. The runtime checkpoint below now
  demonstrates direct datapump entry, but no negotiated connection.
  No 14.4 promise until measured;
  a backend limitation may need bridge changes rather than PCPlus changes.
- [config.js](https://github.com/synexo/synthmodem/blob/b1752e4d0039e0cff72735924e03aa99922723a8/config.js)
  defaults to a Windows QEMU path: explicitly select Linux's `qemu-system-i386`
  path. Bridge AT_INIT commands configure its software answering modem, not Boca.
  Defaults advertise VT100/80x24; review ANSI terminal type and geometry for the
  actual BBS/client. The stock Telnet idle timer is five minutes.
- [TelnetProxy.js](https://github.com/synexo/synthmodem/blob/b1752e4d0039e0cff72735924e03aa99922723a8/src/telnet/TelnetProxy.js)
  lines92..109 forward modem data directly to TCP, except single-byte 1D/1C
  chunks immediately return to the menu. Lines297..300 forward server bytes
  directly to the modem. Initial option messages at331..349 do not implement
  an inbound IAC parser, TTYPE SEND response, BINARY negotiation or IAC escaping.
  These are concrete bridge gaps for Telnet negotiation and binary transparency;
  single-byte escape interception is also chunk-dependent and can break transfer
  payloads. Unit-test fragmented negotiation and every byte, then correct the
  bridge or use a verified Telnet layer before claiming transfer compatibility.
  Merely disabling initial negotiation does not handle server-originated IAC.

## Actual DOS / ENiGMA audio checkpoint (intermittent integrity gap)

[The DOS audio cohort](../lab/bbs/synthmodem-audio-dos.md) now passes19 producer
checks through real V.22/1200 software DSP: numeric dialing, CONNECT> entry,
source-built terminal/ASPECT authentication, Main -> Messages -> Main -> Files,
normal return, UART/vector restoration and directory accounting. The bounded
sparse-helper candidate resolves the lone-N stall; the
[stager](../lab/bbs/synthmodem_sparse_runtime.py) verifies every source/kernel
identity and original archive entry, replacing only the helper executable.

Overall acceptance remains open. Cohort -05 fails one of19 independent checks
on six extra bytes after the DOS CPR, received by ENiGMA. Offline caller decoding
matches all64 DOS online bytes; three earlier training-tail bytes are separately
accounted for by the pre-proxy hold. Cohort -06 uses the added diagnostic export
channel and passes all19 producer/19 audit checks, including exact64 upstream and
46908 downstream bytes and normal cleanup. Its actual guest pre-resampling PCM
matches3559200 overlapping caller samples after a stable60ms delay. Both offline
decoders recover the DOS input exactly. This clean run does not resolve -05.

The [receive trace](../lab/bbs/synthmodem-receive-trace.md) documents both captures.
The [paired VM comparison](../lab/bbs/synthmodem-jitter-vm.md) now reproduces a
policy failure: releasing300ms of ordered, unmodified queued RTP causes the
rebuilt baseline to insert89 bytes at the same CPR boundary while shrinking its
audio delay. The explicit DISCARD_NONE candidate preserves the waveform and all
34 upstream/6000 downstream diagnostic bytes. Both builds train and pass the
direct route; independent image/transport checks isolate the d-modem change.
The normal candidate also passes the full DOS/ENiGMA main/message/file route in
cohort -07, with19 producer/19 independent checks and64/46908 exact upstream/
downstream bytes. Only d-modem changes in that image; no trace daemon is added.
Editors, broader loss/timing, sustained data, transfers and physical acceptance
remain separate. This does not prove the exact historical
six-byte event's cause. See [the VM receipt](validation/synthmodem-jitter-vm.json).

The normal helper still has an in-band carrier/data ambiguity: literal NO CARRIER can
be consumed as status, while a slowly fragmented real result can become data.
Out-of-band carrier reporting remains required. The
[rebuilt modem-wrapper checkpoint](../lab/bbs/synthmodem-slmodem.md) establishes
a Nix-built baseline through actual V.22 DSP and tests the opt-in carrier-channel
client/helper pair on real host PTYs. The candidate also preserves literal
carrier-like payload at the CONNECT boundary. The separate
[VM/Node integration](../lab/bbs/synthmodem-carrier.md) now passes real waveform-loss
and complete gateway checks, with the pending writer retired before notification
and no modem result text leaking into online data. The
[actual DOS/ASPECT ENiGMA menu route](../lab/bbs/synthmodem-audio-dos.md) now passes
19 producer, 22 byte/cleanup and 13 SIP/archive checks on that candidate. It
preserves 64 online and 47,454 display bytes, restores UART/vector state and
receives exactly one successful real registration-refresh response. Editors,
transfers, Synchronet over audio and physical carrier acceptance remain open.
The first actual audio editor run now fails key semantics and upstream integrity:
the independent caller decode matches 114 DOS bytes while the guest receives 126.
The [retained counterexample](../lab/bbs/synthmodem-audio-dos.md#actual-editor-counterexample)
requires guest PCM/timing investigation before sustained hardware acceptance.
The
[combined lifecycle runtime](../lab/bbs/synthmodem-lifecycle.md) now verifies
the pool-timer and REGISTER-ownership fixes through the actual VM/DSP path.
DOS -08 passes 19 producer/19 byte/11 SIP checks, with one successful guest
refresh response and exact 64/46,908-byte streams. The real replacement-VM
gateway passes 26 checks and exits about 40 ms after cleanup, versus the old
40.53-second timer linger. No installed service is changed.
No physical hardware has been tested; no14400 claim is made.

## Full software gateway checkpoint

The [complete software path](../lab/bbs/synthmodem-gateway.md) passes24 checks
using actual external/internal SIP, CallSession setup/activation/teardown,
modem pool and both DSPs. It retains the default post-training hold, receives
CONNECT>, enters a destination as online data, negotiates BINARY/ANSI/80x25,
recovers exact534/538-byte duplex payloads and reconnects TCP on the same
carrier. QUIT ends both SIP legs and recycles a distinct registered VM; actual
QEMU process exits and independent stream audits are required. See the
[receipt](validation/synthmodem-gateway.json).

The isolated RTP bind-address candidate preserves the wildcard LAN default
while allowing a loopback-only lab. Four native binding/allocator checks also
pass. This test uses a software caller and deterministic Telnet peer, not DOS,
actual BBS software, Boca or SPA2102. Those workflows, sustained data/error
recovery and negotiated14400 remain open. Existing pool timer retention and
status CRCRLF normalization remain recorded gaps.

## Negotiated software DSP checkpoint

The [V.22 training test](../lab/bbs/synthmodem-training.md) now completes actual
native-originating/VM-answering DSP training at1200 and exchanges exact1058-byte
payloads each way, including all256 byte values. Stock native originating
startup fails; a separately staged role-specific source candidate fixes that
caller. No connected flag or decoded bytes are injected. Full decoded streams,
guest DATA_RX frames and captured RTP continuity are independently audited.
The [receipt](validation/synthmodem-training.json) binds the fixed software
profile and unchanged Nix-built helper/runtime inputs.

This establishes software data mode beyond the earlier silence-caller test.
CallSession/Telnet/DOS/BBS composition, other modulation protocols and physical
Boca/SPA2102 acceptance remain open. In particular, V32bis direct entry remains
separate from successful training; no14400 claim follows from this V.22 pass.

## Normal answering-stack checkpoint

The [normal VM runtime test](../lab/bbs/synthmodem-runtime.md) now exercises
actual startup/REGISTER, software modem AT queries, RING-triggered ATA, SIP
INVITE/PCMU media, answering DSP audio, BYE and resource cleanup. Only the helper
changes in the runtime archive; normal init and slmodemd/d-modem remain intact.
The caller sends silence, so no modem data connection is claimed.

A separate software answering profile accepts `AT+MS=132,0,14400,14400` and the
guest creates its V32bis datapump with tx/rx rates14400 without the V.8 answer
state. This is a concrete direct-training route to investigate with the Boca;
it does not prove successful training or make that command appropriate for the
Boca. The [receipt](validation/synthmodem-runtime.json) separates profiles and
binds source, runtime, toolchain, signaling and independently decoded RTP evidence.
An originating DSP peer, negotiated data, full gateway SIP/session integration
and all physical acceptance remain outstanding.

## Composed Node/helper VM checkpoint

The [combined VM test](../lab/bbs/synthmodem-vm.md#nodehelper-composition) passes19
checks with the actual candidate Node parser/writer/session methods connected
to the Nix-built i386 helper. The guest's synthetic CONNECT triggers backend
attachment, a stalled modem endpoint pauses BBS reads, both16777219-byte payloads
match and actual session teardown retires writer/drain ownership before guest
exit. Independent Python audits reconstruct all guest frames and both payloads.
See the [receipt](validation/synthmodem-vm-composed.json).

This composes the separately tested Node and C candidates; it does not run
normal SIP/DSP startup. The modem endpoint and BBS TCP peer are synthetic, and
session SIP ownership is modeled. CONNECT14400 is a result-code fixture, not
V.32bis training. DSP/native credit, reverse TCP pressure, DOS/BBS composition
through this complete candidate and all analog/hardware acceptance remain open.

## Booted rebuilt-helper checkpoint

The [i386 VM helper test](../lab/bbs/synthmodem-vm.md) now passes14 checks plus an
independent raw-frame/payload audit. Nix builds the patched helper as a static
ELF32 Intel386 binary; the pinned upstream kernel boots a separate archive that
changes only the helper and adds the lab init. Both16777219-byte payloads match,
source writers block under pressure, opposite-direction probes remain live and
transport close produces the expected helper exit and VM poweroff. See the
[receipt](validation/synthmodem-vm-control.json).

The second virtio character port is a modem endpoint stand-in. The normal
SIP/DSP startup is bypassed, no Node writer is connected in this standalone run, and no physical
handshake/audio or DOS/BBS compatibility is established by these VM checks.
Normal runtime images, installed services and the live board remain untouched.

## Node VM-data pressure checkpoint

[The Node writer candidate](../lab/bbs/patches/synthmodem-pressure/README.md)
now composes bounded frame splitting, PjsipBackend readiness, active CallSession
ownership and BBS socket pause/resume. Upstream oversized writes throw beyond
4093 bytes and are swallowed by the session; those defects and ignored stream
pressure are reproduced separately. The candidate transfers16MiB exactly over
real loopback TCP with a paused VM-side reader, and passes the existing1220
Telnet assertions. The [receipt](validation/synthmodem-pressure.json) binds the
source, toolchain, lifecycle/failure checks and recovered byte hash.

The retained ring is256KiB; Node socket buffering remains separately bounded by
its writable high-water mark plus an accepted frame. False means accepted then
paused, not a request to replay the frame. Capacity/replaced-channel failures
hang up instead of silently continuing, and teardown removes stale drain owners.

This source candidate is not installed. The combined VM checkpoint above now
composes it with the C helper; actual DSP/SIP/audio and DOS/BBS remain untested
through that complete composition. Native
DSP flow credit, serial-to-BBS pressure and physical hardware remain open.

## Bidirectional helper backpressure checkpoint

The [control-helper candidate](../lab/bbs/patches/synthmodem-control/README.md)
now queues complete reverse header/payload frames into a fixed65536-byte buffer.
PTY reads pause while host output is pending, with opposite-direction service
kept live. Partial headers, EINTR/EAGAIN, queue compaction, capacity exhaustion
and fatal writes are covered by16 fault cases. Twelve real-PTY checks pass:
262147 exact forward bytes,1048579 exact reverse bytes, stalled readers and
responsive shutdown with both outputs pending. The
[receipt](validation/synthmodem-control-reverse.json) also retains an independently
reproduced stock truncated-header failure and exact fixture comparisons.

This extends the earlier one-direction checkpoint below. The VM image/prebuilt,
installed services, DOS application and Telnet candidate remain unchanged.
The separately tested Node writer above supplies VM-data pressure propagation;
a rebuilt-VM end-to-end test and native DSP credit remain required before hardware
acceptance. These helper host tests do not exercise SIP or modem audio.

## Control-helper backpressure checkpoint

[An isolated control-helper source candidate](../lab/bbs/patches/synthmodem-control/README.md)
now fixes two reproduced upstream faults: receive-buffer compaction invalidating
a parsed payload, and nonblocking PTY writes losing unsent bytes. Nine fault
cases and seven real-PTY checks pass, including262147 exact binary bytes with
the PTY reader stopped/throttled. Queue admission is bounded to one frame; host
reads pause until it drains. Hangup guards remain serviced, and observed carrier
loss clears queued session bytes before further output. The
[receipt](validation/synthmodem-control.json) records the Nix GCC host build.

The initial checkpoint left reverse host-output recovery open; the bidirectional
checkpoint above addresses it. Backpressure support remains incomplete because
PjsipBackend/CallSession ignore stream-write pressure and the native DSP write
interface supplies no flow credit. No VM image/prebuilt,
installed bridge, application, BBS or hardware was changed. Rebuild/integration
and end-to-end tests remain required; earlier proxy/BBS receipts retain their
unchanged candidate identity and do not test this new helper.

## Logged-in BBS upload checkpoint

[Actual DOS upload through the candidate](../lab/bbs/synthmodem-enigma.md#logged-in-upload)
now passes19 checks plus independent serial/protocol/server audits. A fresh
11521-byte file and its FileEntry metadata match exactly after the real upload
form. The final handshake, nine opposite controls, helper exit0 and subsequent
File List are confirmed; prior files and source media remain unchanged. See the
[receipt](validation/synthmodem-enigma-upload.json). This complements the logged-in
download checkpoint below without establishing other protocols, fault tolerance,
modem backpressure, SIP/audio or physical acceptance.

## Logged-in BBS download checkpoint

[Automatic ZMODEM download through the candidate](../lab/bbs/synthmodem-enigma.md#logged-in-automatic-download)
now passes21 checks plus independent audits against the owned ENiGMA lab. The
11521-byte fixture matches exactly, the complete CRC/EOF/final handshake is
validated in both directions, the official download counter advances and a new
keyboard search succeeds after return. Saved PRM preferences start reception;
no manual transfer keys or injected replies are used. The existing helper and
selector-first configuration are frozen unchanged. See the
[receipt](validation/synthmodem-enigma-download.json). Other protocols, error/retry/cancel, SIP/audio and hardware acceptance remain
open; the upload checkpoint above is separate evidence.

## Authenticated stock BBS checkpoint

[Stock ENiGMA through the candidate](../lab/bbs/synthmodem-enigma.md) now passes
34 producer checks over menu and unsaved-editor sessions, plus exact serial/TCP
payload and authoritative server/video audits. Login and named menu order are
confirmed, Home moves to line start, Insert toggles overtype, and no post is
saved. The measured editor escape sequences arrived whole at the TCP observer;
this pass does not establish arbitrary-fragmentation tolerance or replace earlier
stock ENiGMA failures. The [receipt](validation/synthmodem-enigma.json) keeps
those scopes explicit. No server, application or candidate code was changed.

These are synthetic-call, real-DOS/BBS software tests. SIP/DSP/audio, BBS upload
and broader transfer workflows through this path and physical acceptance remain open.

## DOS transfer composition checkpoint

[Actual DOS transfer tests](../lab/bbs/synthmodem-dos.md) now pass84 checks over
four routes through the exact candidate proxy: small and65797-byte batches,
uploaded and downloaded with independent lrzsz. Numeric ATD1 precedes the bridge
prompt and keyboard-entered server address. ANSI TTYPE/NAWS and BINARY are
observed, both streams decode exactly, files match, terminal input/display
resume, UART state restores and staging files disappear. The
[independent audited receipt](validation/synthmodem-dos.json) freezes the DOS
executable, candidate/config/logger, test helpers and wire hashes. No production
application or bridge change was needed for this checkpoint.

These tests use a synthetic call adapter and independent local transfer peer,
not a real BBS or SIP/DSP/audio. Full BBS workflows, other transfer protocols,
error/retry/cancel, slow-modem backpressure and Boca/SPA2102 acceptance remain open.

## Isolated bridge transport candidate

The [SynthModem Telnet candidate](../lab/bbs/patches/synthmodem-telnet/README.md)
now reproduces five stock-proxy findings and passes1220 assertions with its
maintained streaming codec. The [receipt](validation/synthmodem-telnet.json)
binds the upstream revision, original files, candidate, test source and Node
version. Tests include all256 bytes under fragmentation, TTYPE/NAWS/BINARY,
NVT handling, bounded malformed subnegotiation, opt-in menu escapes, stale socket
isolation and a real loopback TCP duplex exchange. It also corrects NAWS reading
from `config.terminal` rather than the actual `config.telnet` fields.

This is a separately staged source candidate, not a deployed or upstream fix.
The original source findings above remain valid for the pinned stock version.
Run `lab/bbs/patches/synthmodem-telnet/check.py` through `tools/dev` as documented
there. No DSP, SIP/RTP, DOS application, modem or real BBS is exercised by this
checkpoint. Complete DOS/BBS transfers, slow-modem backpressure and hardware
acceptance remain open; do not treat byte-oracle success as a file-transfer pass.

## Source-built software prerequisite checkpoint

[The recorded receipt](validation/analog-modem.json) binds 49 linked-instruction
cases, the existing 46-input connection suite and 15 actual DOS checks to the
same executable. A Nix source rebuild reproduced executable SHA256
`c4f7e525740d2e9c12d424a59c12e539ca2ecee80d5b6e619a9a426c26cd587c`.
No application code or command policy changed.

The new linked cases program real linked UART divisor instructions at all nine
supported DTE rates, check verbose CONNECT suffixes with autobaud disabled,
characterize DCD-never-high admission, require output cancellation on observed
carrier loss, reset carrier history on redial, preserve concurrent RTS changes
across configured DTR cleanup, and exercise a 55-second handshake budget plus
stalled-initialization timeout. UART registers and BIOS clock remain modeled.

Actual DOS executes `/D:1 COM1 38400 8N1 HARD`, sends `ATZ` and `ATD1`, renders
the synthetic peer's `CONNECT>` prompt, then transmits typed `bbs.example` as
online data. Exact wire order includes DOS-generated CPR/DA replies. The frozen
PRM, executable/map and helper inputs are checked; 42-byte UART/PIC/vector
snapshots match before/after. This establishes the numeric CLI route without
claiming SIP, Telnet negotiation or analog hardware support.

```sh
./tools/build terminal
./tools/dev --command python3 standalone/check_analog_modem.py
./tools/dev --command python3 standalone/check_connection.py
# Choose a fresh label on every run; previous evidence is preserved.
./tools/dev --command python3 standalone/test_analog_dial_dos.py --label analog-local-001
```

`test-terminal` includes the new linked checks. The accepted DOS cohort is
`analog-numeric-02` under ignored `build/connection-dos`; the first pilot passed
with the identical executable, then the rebuild changed its map hash, so a
fresh cohort was run against the final map. Earlier fixture-development
assertions were corrected for a non-exported private symbol, cancellation
versus hangup mode, and the full abort-plus-DTR cleanup budget. They did not
cause production changes. Actual Boca result fixtures and physical acceptance
below remain outstanding.

## Workstation and adapter preparation (not applied)

Keep the DOS toolchain managed by pinned Nix. For later workstation dependencies,
prefer official distribution packages, then Nixpkgs. Do not use AUR, yay or paru.
Upstream needs Node.js and QEMU for auto/VM backends; record their exact versions,
upstream revision and runtime-image hashes before a test. No package install,
service start, firewall change or adapter reconfiguration is part of this review.

Save the adapter configuration first. Use PHONE1 and INTERNET as above, a
reachable workstation LAN address, local SIP routing and matching RTP settings.
Upstream's SPA2102 baseline specifies G.711u/PCMU only, UDP SIP, no silence
suppression, no echo cancellation/suppression, disabled adaptive jitter adjustment
and 30 ms RTP packets. Treat it as a starting configuration, not proven settings
for our line. Keep the modem/ATA/workstation path wired when possible; record
any workstation Wi-Fi segment. Preserve stock firmware and document every change.

## Acceptance tasks and evidence

### Work order and completion gates

Keep this target alongside the full application rebuild. The next work follows
this order; completing a software gate never checks off a hardware gate.

| Order | Work item | Evidence needed to close it |
| --- | --- | --- |
| 1 — software | Separate carrier status from online payload in the VM helper. | The [structured carrier checkpoint](validation/synthmodem-carrier.json) verifies literal status text as payload, real software waveform loss, and retirement of queued writes. Full current DOS/SIP/audio loss and redial remain separate acceptance work. |
| 2 — software | Complete flow-pressure and BBS workflow coverage on the combined runtime. | Sustained duplex counts/hashes, bounded queues, recovery after stalls, and actual Synchronet/ENiGMA editor and upload/download sessions through SIP/audio/DSP. Separate synthetic transport results do not close this gate. |
| 3 — hardware identification | Identify the Boca and obtain matching documentation. | Model/chipset/firmware, UART, COM/base/IRQ, supported modulation and documented initialization, speaker, fixed-DTE, flow and carrier commands. Leave the Boca initialization profile unset until those facts are available. |
| 4 — adapter commissioning | Save the SPA2102 configuration and configure PHONE 1 routing/audio using existing firmware. | Recorded firmware/settings and a reachable Linux SIP endpoint, then a real audible handshake, modem CONNECT, DCD assertion and `CONNECT>` in PCPlus. Adapter arrival is required. |
| 5 — physical acceptance | Run connection, display, sustained-data, disconnect/reconnect and transfer tests separately. | Completed commissioning worksheets with byte hashes, UART errors, result strings, timings and failure recovery; explicitly record the negotiated protocol and rate. |
| 6 — higher-speed investigation | Establish whether this Boca can negotiate with the selected backend without V.8. | Actual negotiated V.32bis data and clean sustained transfers before accepting 14400 bps. Direct datapump entry and a synthetic CONNECT result are insufficient. |

No default Boca command string or production service is installed by this plan.
The bridge's software-modem commands and numeric lab dial target are test inputs,
not a discovered configuration for the physical modem or adapter. Record the
actual local telephone destination only after configuring the SPA2102 route;
enter the remote BBS address after `CONNECT>`.

All hardware tasks remain unchecked until the adapter arrives and the DOS PC
is connected. Do software-only bridge tests first without relabeling them as
analog modem results.

Use the [commissioning worksheet](BOCA_COMMISSIONING.md) for each physical run.
The following status separates prerequisites already exercised from hardware
acceptance; historical checkpoint sections above describe their own frozen inputs.

| Area | Software evidence available | Still required |
| --- | --- | --- |
| Serial/controller | Linked and DOS synthetic-call tests cover selectable DTE, numeric dialing, DCD history/loss, DTR cleanup and timeout budgets. | Actual Boca identity/results, COM/IRQ, CTS/RTS, DCD/DTR and UART load. |
| Telnet/CP437/binary transport | Codec/gateway all-byte checks, scoped ENiGMA editor/download audio, Synchronet editor/download/upload audio and same-call retry receipts exist. Structured carrier status has separate software evidence. | Revalidate exact current binaries per workflow, broader display/transfer cases, sustained load, audio loss/reconnect and physical display/transfers. Historical receipts are not implicit current-version passes. |
| Modem data pressure | Node writer and booted i386 helper pass separate and composed pressure checks; normal software gateway runs. | Sustained pressure through normal DSP; resolve native DSP flow credit and serial-to-BBS TCP pressure. |
| Answering protocol | Actual native/VM software training and exact data pass at V.22/1200; explicit V32bis profile enters datapump132 directly. | A shared protocol with this Boca, physical training, V.8 and negotiated V.32bis/14400 connectivity. |
| Hardware/audio | Equipment and topology selected; adapter ordered. | All analog connection, audible handshake and end-to-end acceptance. |

- [ ] Identify Boca model/chipset/UART and manual; record jumpers/base/IRQ,
  firmware identification, supported speaker, flow, DCD/DTR and modulation controls.
- [ ] Add fixtures from actual Boca result strings and supported command behavior
  when identified; retain the existing source-only/synthetic controller regressions.
- [x] Compose the tested Telnet and Node/control-helper candidates through normal
  SIP/DSP startup and the DOS menu route. The lifecycle receipt records actual
  guest refresh and cleanup; this remains software evidence, not deployment or
  physical acceptance.
- [ ] Resolve remaining DSP/native and reverse-TCP pressure gaps before sustained
  hardware tests, and complete editor/file-transfer workflows over the audio path.
- [ ] Record the selected runtime's Linux dependency versions and backend/image
  identities; existing Nix lab receipts establish only their recorded software inputs.
  Simulated callers cannot establish Boca/V.8 compatibility.
- [ ] Configure and record ATA routing/audio after arrival; establish and hear a
  real handshake, observe CONNECT plus `CONNECT>` and enter a BBS hostname there.
  Record backend, protocol, negotiated line rate, fixed DTE and elapsed times.
- [ ] Display/interaction: CP437 byte chart, ANSI colors/cursor/scroll, DA/CPR and
  stock Synchronet/ENiGMA login, menus and editors; exercise immediate and measured
  buffered paths separately. Verify first banner byte and no Telnet negotiation
  artifacts. Keep any server patches explicit.
- [ ] Sustained duplex data: deterministic payloads with hashes/counts, idle periods,
  CTS backpressure and receive load; record UART overrun/overflow counters and
  errors. Increase line/DTE speeds only after a clean lower-speed baseline.
- [ ] Disconnect/reconnect: local hangup, DTR drop, remote BBS close returning to
  bridge menu while analog carrier stays up, bridge/SIP failure and actual carrier
  loss; repeat calls and verify UART/vector cleanup on DOS exit. Distinguish
  remote TCP closure from physical DCD drop.
- [ ] File transfers: both directions, empty/binary/all-byte/over64KiB files,
  XMODEM/YMODEM/ZMODEM where supported, hashes, cancellation, retries and carrier
  loss. No transfer pass until menu escapes and Telnet binary transport are safe.
- [ ] Investigate and measure V.32bis/14400 separately from lower-rate success.

Each run should bind executable/source revision, synthetic/public profile or
redacted private settings, COM/base/IRQ/UART, DTE/8N1/flow, modem identity/results,
ATA settings/firmware, bridge backend/revision, BBS version, topology, timestamps,
byte counts/hashes and observed failures. Keep credentials, private dialing
files, disk images and raw private session captures outside the public repo.

## Current software acceptance boundary

The [central audio ledger](validation/synthmodem-audio-dos.json) is the current
index of version-bound software results and remaining failures. Historical
sections above retain the scope of their original runs. In particular,
Synchronet uploads, cancellation and same-call retry now have scoped audio
evidence; indexed partial-file cleanup remains failed. These results do not
close the entire sustained-data or transfer matrix.

The [current Synchronet download repeat](validation/current-synchronet-download-audio-01.json)
now validates terminal `976ba8d0` over actual software SIP/RTP/V.22-1200 audio:
exact source/CRC/control finish, Files/Main, complete upstream/downstream byte
identity, official metadata and DOS/UART/timer cleanup. Current upload, cancellation,
same-call retry and ENiGMA audio workflows still need their own current-version
results. This is a download baseline for the next audio fault campaign.

The [current DOS carrier checkpoint](CURRENT_DOS_CARRIER.md) accepts terminal
`976ba8d0` losing a connection after a real partial receive, observing emulated
DCD loss, redialing and completing the exact retry through ENiGMA. DOSBox-X's
built-in modem supplies that DCD transition. The existing SIP/audio DOS fixture
instead uses a null-modem UART and synthetic Hayes responses; its DCD is held
ready. A successful audio transfer through that fixture cannot prove the DOS
carrier-loss path. A combined test must derive the DOS carrier transition from
actual audio/SIP failure, retain the interrupted-transfer evidence, and verify
fresh training, login and retry on a subsequent call.

Remote Telnet close is a different case: the bridge may return to `CONNECT>`
while the analog carrier remains up. Do not convert that event into a modem
hangup merely to reuse the emulated-DCD test. Physical Boca/SPA2102 commissioning
and negotiated higher-speed compatibility remain unverified.

The [first combined audio bridge-restart campaign](../lab/bbs/synchronet-reconnect-audio.md)
now records a current-build failure: DOS observes emulated carrier loss, removes
the partial and redials; both DSPs train again, but the second ASPECT invocation
reports an unsupported command or service at opcode D4, step2 and sends no BBS address. The final
watchdog exit restores UART/timer state. The failed receipt retains the missing
retry and the first call's one-ACK in-flight tail loss. This is diagnostic
progress, not accepted audio reconnect or an identified product fix.

The [helper diagnosis](validation/reconnect-stale-prompt-diagnosis.json) identifies
stale transfer text causing the test helper to inject Alt-R into the second
ASPECT invocation. The corrected helper passes actual DOS regressions and a
two-script replay with unchanged production binaries. A subsequent
[real audio run](validation/current-synchronet-reconnect-audio-02.json) completes
the exact retry and menus with clean DOS/UART/timer return:14 CRC blocks, full
upstream byte identity,26 serial checks,7 official metadata checks and23
damaged-evidence rejections. It still fails one of19 producer gates because
the footer-only observer missed the loss notice. A tested full-screen observer
and fresh real audio run are required before overall reconnect acceptance.
Physical modem/ATA, waveform-loss, sustained pressure and higher-rate acceptance
remain separate.

The [latest repeat](validation/current-synchronet-reconnect-audio-03.json) exposes
an intermittent integrity failure before the intended stop:119 DOS/caller-audio
bytes become123 guest/BBS bytes, with four inserted bytes before file selection.
The first file recovers exactly, but the strict stop observer correctly refuses
the mismatched stream. This run has no injected loss, retry or normal-cleanup
acceptance. Guest PCM and media-arrival evidence are needed to distinguish the
media/DSP/helper cause. A successful earlier retry does not establish reliability
against this counterexample.
