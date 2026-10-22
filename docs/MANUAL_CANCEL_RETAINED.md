# Retained modem command after canceled initialization

The main source now includes the paced retry separator. The
[current component audit](validation/modem-resync.json) accepts four actual DOS
retained/cleared-parser SOFT/BOTH cases, binds normal/mouse products to fresh
source-only reproductions, and checks 34 linked synchronization cases plus four
manual reconnect cases. Normal/mouse SHA256 prefixes are `1cbb4f8f`/`b14074ec`.
[Additional regressions](validation/modem-resync-regressions.json) pass46 connection
inputs,42 carrier-policy cases,eight startup ABI cases and13 attached PROGRAM
workflows using the rebuilt external parent `c3466222`. The unchanged recorder
helper passes13 ENiGMA TCP-control checks on this parent. These do not accept
the separate failed audio run or close full application/hardware requirements.
Four fresh [Synchronet/ENiGMA recorder/replay sessions](validation/bbs-modem-resync-compat.json)
also pass independent raw audit. Synchronet required a declared temporary
synthetic-account logon exemption; its original exemption bits are restored.

Run the maintained normal/mouse synchronization checks through Nix:

~~~sh
./tools/build test-modem-resync
~~~

The preceding parent (SHA256 `1600a5b37094d5a3b666ffee6bf1da387dad7a7435a332be76618975c47bcdab`)
fails retry initialization when a modem retains its partial command buffer
through the cancellation DTR pulse. Both actual DOS SOFT/BOTH lab cases retain
the first `A`, observe cancellation, then parse retry `ATZ` as `AATZ` and return
`ERROR`. The following dial still connects, receives ANSI queries, accepts manual
input, updates accounting and hangs up. Connection success therefore does not
prove initialization succeeded.

The earlier [cancellation acceptance](MANUAL_CANCEL_LAB.md) explicitly used a
peer that clears its parser on DTR fall. These retained-parser cases preserve
that controller/flow correction: first-attempt DCD and carrier history stay zero,
the idle flow pause clears, and the later online dwell exceeds 18 BIOS ticks.
The new failure is command framing, separate from retiring stale XOFF.

The owned peer policy is motivated by pinned DOSBox-X 2026.07.02 softmodem
source: `setDTR` starts hangup handling only when connected; `DoCommand` resets
the parser on command termination, rejecting input without an AT prefix.
See [upstream source](https://github.com/joncampbell123/dosbox-x/blob/dosbox-x-v2026.07.02/src/hardware/serialport/softmodem.cpp).
This source observation alone does not establish an actual stock-backend or Boca
result. The tests use the separately pinned patched DCD lab and an explicit
owned peer, as documented in the earlier acceptance.

Evidence:

- `build/manual-cancel-dos/retained-baseline-01/checks.json` retains the failed
  producer outcome. Only actual initialization and unexpected-command checks
  fail; the report is not relabeled as accepted compatibility.
- [Independent failure receipt](validation/manual-cancel-retained-gap.json)
  checks frozen products/sources, exact raw UART bytes and transport framing,
  ordered DTR/error/CONNECT events, passive guest samples, directory accounting,
  hardware and interrupt-vector restoration.
- [Audit corruption controls](validation/manual-cancel-retained-audit-guards.json)
  reject six modified captures/declarations while keeping their declared hashes
  consistent. Failure reproduction remains distinct from product acceptance.

Run the corrected current workflow with the pinned DCD lab available:

~~~sh
./tools/dev --command python3 standalone/test_manual_cancel_retained_dos.py \
  --label retained-fixed-new
~~~

The producer preserves its scripts under the run's `retained-inputs/standalone`
directory. The initial recorded run retained both scripts manually with their
declared hashes before any candidate edits. Historical `--expect-gap` runs
require the recorded preceding source/product, not the corrected main build.

Recovery was first tested in an isolated candidate tree, using one
paced carriage return before retry initialization following an aborted MODEM
attempt, keeping the configured initialization string intact. The isolated
`build/manual-resync-candidate-01` passes four retained/cleared-parser SOFT/BOTH
DOS cases: the stale `A` or empty command terminates separately, then clean
`ATZ` and dialing proceed. The [independent candidate audit](validation/modem-resync-candidate.json)
checks both parser policies and binds the exact [recorded patch](../patches/modem-retry-resync.patch)
to the admitted old/new product sources. It accepts these candidate cases only;
the matching patch is now adopted in the main build with the current audit above.
The earlier frozen audio run has now ended and is
[preserved as failed](validation/recording-manual-reconnect-audio-failure.json):
startup reached Files, but the recipe helper delivered no keys and reached its
watchdog. This run provides no recording/replay/audio acceptance.

Normal and mouse candidates each pass 17 linked instruction cases covering
CTS/THRE/XOFF stalls before the separator, repeated cancellation, configurable
initialization, a CR pause character, and the configured high-carrier skip.
The existing 46-input connection suite and 42 carrier-flow policy cases also
pass on the normal candidate.
Five stock-backend DOS cases cover first connection, BUSY, timeout, normal
hangup and redial, checking that first initialization has no extra separator
and BUSY retry sends one separator followed by the configured commands.
These use an owned peer explicitly ignoring empty modem command lines; they
are distinct from stock softmodem backend or physical-modem acceptance.

The separate [stock modem parser comparison](validation/modem-resync-stock-softmodem.json)
now exercises the actual stock DOSBox-X modem backend, with no patched DCD
transport or owned command parser. Timed Escape interrupts a long configured
`AT` + spaces + `Z` initialization. The unchanged parent joins its partial
command, abort character and retry initialization, receives `ERROR`, and still
connects. The candidate terminates the partial command separately, then the
configured initialization receives `OK` before `CONNECT`. Both render the
immediate ANSI banner/replies and restore hardware on exit. This establishes
the specific software-modem cancellation/retry behavior; it does not establish
physical Boca behavior or sustained/other modem policies. Loopback Internet
address dialing here belongs to the emulator's modem implementation; physical
Boca connections still use numeric dialing through the planned SIP/audio bridge.

~~~sh
./tools/dev --command python3 standalone/test_modem_resync_softmodem_dos.py \
  --baseline-product build/manual-resync-candidate-01/stock-softmodem-03/baseline/admitted-product \
  --candidate-product build/terminal \
  --output build/modem-resync-stock-softmodem-new
~~~

Keep the baseline product at the recorded old identity when repeating this
comparison after adoption. The test preserves both executable copies, config,
modem command/result logs, peer bytes and guest hardware/screen captures.

Normal candidate SHA256 is
`1cbb4f8fa243f9ce63c3a2d0788d0f039c3cb481f8e03d267f77e039823a6ba0`.
Resident code spare remains 318/170 bytes and near data spare 112/64 bytes for
normal/mouse. The new internal sender entry preserves pacing and leaves the
configured initialization buffer intact. Candidate captures and linked reports
are retained under its ignored build directory. A fresh source-only tree of
398 declared files reproduces both normal/mouse executables byte-for-byte,
with no originals or prebuilt inputs. The [regression inventory](validation/modem-resync-candidate-regressions.json)
records product identities, tool hashes and individual report hashes.
Other application/BBS workflows remain required after adoption; current TCP
recorder/replay controls pass while normal audio still needs investigation.
Full modem and application requirements, and physical
Boca/SPA2102 testing, remain open.
