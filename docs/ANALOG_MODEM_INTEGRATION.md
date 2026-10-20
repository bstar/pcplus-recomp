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
| COM / base / IRQ | `src/config/terminal_import.c` accepts COM1..4 at 3F8/2F8/3E8/2E8, IRQ4/3/4/3. `setup_model.c` enforces those pairs. Nonstandard ISA jumper settings and shared-IRQ operation are unsupported; identify the Boca configuration first. |
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
  legacy V.32bis answering on the VM backend. No 14.4 promise until measured;
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

## Booted rebuilt-helper checkpoint

The [i386 VM helper test](../lab/bbs/synthmodem-vm.md) now passes14 checks plus an
independent raw-frame/payload audit. Nix builds the patched helper as a static
ELF32 Intel386 binary; the pinned upstream kernel boots a separate archive that
changes only the helper and adds the lab init. Both16777219-byte payloads match,
source writers block under pressure, opposite-direction probes remain live and
transport close produces the expected helper exit and VM poweroff. See the
[receipt](validation/synthmodem-vm-control.json).

The second virtio character port is a modem endpoint stand-in. The normal
SIP/DSP startup is bypassed, no Node writer is connected yet, and no physical
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

This source candidate is not installed. It has not yet been composed with the
C helper in a rebuilt VM or tested with actual DSP/SIP/audio and DOS/BBS. Native
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

All hardware tasks remain unchecked until the adapter arrives and the DOS PC
is connected. Do software-only bridge tests first without relabeling them as
analog modem results.

Use the [commissioning worksheet](BOCA_COMMISSIONING.md) for each physical run.
The following status separates prerequisites already exercised from hardware
acceptance; historical checkpoint sections above describe their own frozen inputs.

| Area | Software evidence available | Still required |
| --- | --- | --- |
| Serial/controller | Linked and DOS synthetic-call tests cover selectable DTE, numeric dialing, DCD history/loss, DTR cleanup and timeout budgets. | Actual Boca identity/results, COM/IRQ, CTS/RTS, DCD/DTR and UART load. |
| Telnet/CP437/binary transport | Isolated codec candidate passes fragmentation/all-byte checks; synthetic-call DOS/BBS transfer receipts exist. | Candidate integration through the complete SIP/DSP path; physical display and transfers. |
| Modem data pressure | Node writer and booted i386 helper pass separate pressure checks. | Compose those components; resolve native DSP flow credit and serial-to-BBS TCP pressure. |
| Answering protocol | Pinned source describes VM-first auto mode and legacy native fallback. | Prove a shared protocol with this Boca; V.8 and V.32bis/14400 are unverified. |
| Hardware/audio | Equipment and topology selected; adapter ordered. | All analog connection, audible handshake and end-to-end acceptance. |

- [ ] Identify Boca model/chipset/UART and manual; record jumpers/base/IRQ,
  firmware identification, supported speaker, flow, DCD/DTR and modulation controls.
- [ ] Add fixtures from actual Boca result strings and supported command behavior
  when identified; retain the existing source-only/synthetic controller regressions.
- [ ] Compose and validate the tested Telnet and Node/control-helper candidates
  through normal SIP/DSP startup. Existing isolated passes are not deployment or
  physical acceptance. Resolve remaining pressure gaps before sustained hardware tests.
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
