# Retained modem command after canceled initialization

The current parent (SHA256 `1600a5b37094d5a3b666ffee6bf1da387dad7a7435a332be76618975c47bcdab`)
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
This source observation does not establish an actual stock-backend or Boca
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

Reproduce with the admitted parent and pinned DCD lab available:

~~~sh
./tools/dev --command python3 standalone/test_manual_cancel_retained_dos.py \
  --label retained-baseline-new --expect-gap
./tools/dev --command python3 standalone/audit_manual_cancel_retained.py \
  build/manual-cancel-dos/retained-baseline-new \
  --output docs/validation/manual-cancel-retained-gap-new.json
~~~

The producer preserves its scripts under the run's `retained-inputs/standalone`
directory. The initial recorded run retained both scripts manually with their
declared hashes before any candidate edits.

Recovery is in progress in an isolated candidate tree. Its hypothesis is one
paced carriage return before retry initialization following an aborted MODEM
attempt, keeping the configured initialization string intact. The isolated
`build/manual-resync-candidate-01` passes two retained-parser SOFT/BOTH DOS
producer cases: the stale `A` terminates separately, then clean `ATZ` and dialing
proceed. This is preliminary producer evidence, pending independent audit.
It is not yet accepted or installed in the main build. Retained/cleared parser policies,
stall/cancellation during synchronization, ordinary first connections and
configured initialization behavior need validation before adoption. Full modem
and application requirements, and physical Boca/SPA2102 testing, remain open.
