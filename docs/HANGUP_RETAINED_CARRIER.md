# Blocked hangup with retained carrier

[The selected correction](validation/hangup-failure-policy.json) is accepted on
normal parent `3b453f2b` and its mouse variant. A timed-out online hangup whose
DCD remains high returns to online state6 with status8, **Hangup failed**, and
retains the existing flow state. Alt-D refuses to initialize/dial that unresolved
session. Incoming traffic, including XON, is still serviced; after XON, another
Alt-H can send the configured hangup. Observed carrier loss permits clean redial.

This gate applies only to the failed online hangup. Initial high DCD, the saved
initialize-with-carrier setting, successful configured hangup, direct lines and
pre-CONNECT cancellation retain their existing behavior. If DTR actually lowers
carrier after the command times out, ordinary idle timeout status3 and clean
retry are preserved. Explicit exit remains bounded and releases DOS ownership;
it cannot guarantee an external modem disconnected if that modem ignores DTR.

Four actual DOS old/new cases show the retry/abort contamination is removed;
two further DOS BOTH cases recover through XON, successful Alt-H, redial and a
manual query, with DTR enabled/disabled. Independent audits require exact raw
transport, timer, file and vector evidence. [Three semantic corruption controls](validation/hangup-failure-audit-rejection.json)
reject retired pause, missing carrier and leaked vectors even after the modified
file hashes are updated. Two stock DOS modem DTR-reconnect
cases and five ordinary modem cases pass. Both normal/mouse products pass23
linked policy cases each, plus retry/carrier/connection regressions, and reproduce
from398 admitted source files without originals. Normal/mouse resident code
spare remains318/170 bytes and near-data spare112/64 bytes.

The first recovery fixture expected its final observed pause to remain1 even
after XON. That assertion was wrong: the observer correctly recorded0 after
XON. Its failed cohort is retained; the second cohort checks resumed flow and
the exact subsequent hangup/redial/manual stream. No product correction was
needed between those recovery cohorts.

[Current-parent stock BBS and application regressions](validation/hangup-policy-regressions.json)
now accept four Synchronet/ENiGMA recorder/compile/replay/manual sessions and two
script reference/help/continuation/parent-menu workflows, with independent raw
custody audits. Six startup groups (45 inputs, including eight invalid ABI cases)
and13 attached DOS PROGRAM cases pass on rebuilt external parentd688f4a4.
The retained region is10,278 bytes:10,152 fixed resource bytes plus63 two-byte
renderer policy words, each compared before/after child execution. The existing
older recorder ledger's hard-coded10,276-byte expectation is not reused.

Physical modem behavior, broader initialization/results/flow-pressure policies,
current-parent normal SIP/audio validation and all full application gates remain open.

## Preserved baseline

[Four linked cases](validation/hangup-retained-carrier-baseline.json) reproduce
the former controller policy on preceding parent `1cbb4f8f`. After an established
MODEM session receives XOFF, manual hangup cannot send its configured command.
The attempt times out, retires software flow and returns to idle. If the hardware
boundary still reports DCD high, retry sends `ATZ` and the configured dial command.

Both SOFT/BOTH configurations are covered with DTR drop enabled and disabled.
The explicit hardware model retains DCD even across the enabled DTR pulse; the
disabled policy performs no DTR writes. Controller, sender, receive IRQ, flow
retirement and retry instructions execute without patched product callbacks.
The test preserves source inputs, executable/map and exact emitted retry bytes.

This proves a controller/wire combination in the declared model. DCD high alone
does not prove a real modem remains in data mode: some profiles assert carrier
when idle. No physical Boca behavior or actual DOS peer result follows yet.
The actual DOS evidence below now confirms an online peer receives the retry.
Correction must still distinguish failed hangup from intentional carrier-ignore
configurations.
Preserve configurable initialization and DTR policy; do not introduce an
unconditional DCD-low startup requirement that breaks such configurations.

~~~sh
./tools/dev --command python3 standalone/check_hangup_retained_carrier.py \
  --output build/hangup-retained-carrier/baseline-new
~~~

`passed=true` means the gap was reproduced. `compatibility_accepted=false`
remains explicit. That baseline remains negative evidence after the correction above; no full F03
or application gate closes.


## Actual DOS reproduction

[Four independently audited DOS cases](validation/hangup-retained-carrier-dos-baseline.json)
confirm the gap on the unchanged source-built parent. An owned modem peer sends
CONNECT with DCD high, then XOFF after the operator types `arm`. BIOS Alt-H
starts hangup; the read-only timer observer records the blocked operation,
optional DTR pulse, idle timeout status3 with carrier high and pause cleared,
and a subsequent BIOS Alt-D retry while carrier remains high. The peer remains
in online data mode throughout: it never treats those retry bytes as modem
commands. SOFT/BOTH and DTR enabled/disabled all reproduce the same stream.

After the initial ATZ/dial and ANSI replies, the exact online bytes are
`armATZ\rATDCaseTest:23\r\x1b`. The final ESC is the configured abort character
when Alt-X cancels the unacknowledged retry; it also reaches the online peer.
The independent audit reconstructs data and guest control frames from raw
transport events, checks the exact whole wire and timer sample, verifies input
and capture hashes, and requires UART/PIC and INT21/INT1C restoration.

This uses the explicitly patched lab UART DCD backend, not stock nullmodem or
physical modem evidence. The peer deliberately ignores DTR for this negative
case. The first DOS cohort remains failed because its observer sampled DTR in
state9 instead of state8; the corrected second cohort observes the actual DTR
wait. Product instructions and binaries were unchanged between these cohorts.

~~~sh
./tools/dev --command python3 standalone/test_hangup_retained_carrier_dos.py \
  --output build/hangup-retained-carrier/dos-new
./tools/dev --command python3 standalone/audit_hangup_retained_carrier_dos.py \
  build/hangup-retained-carrier/dos-new --output build/hangup-retained-carrier/dos-new/audit.json
~~~

The correction above is compared against this preserved baseline. Its
acceptance is limited to the declared hangup/recovery workflows. It does not
impose DCD-low on every startup.

~~~sh
./tools/dev --command python3 standalone/test_hangup_retained_carrier_dos.py \
  --expect-fixed --output build/hangup-retained-carrier/fixed-new
./tools/dev --command python3 standalone/test_hangup_failure_recovery_dos.py \
  --output build/hangup-retained-carrier/recovery-new
./tools/dev --command python3 standalone/check_hangup_failure_policy.py \
  --product build/terminal --output build/hangup-retained-carrier/linked-new.json
~~~
