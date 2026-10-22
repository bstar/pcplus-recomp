# Blocked hangup with retained carrier

[Four linked cases](validation/hangup-retained-carrier-baseline.json) reproduce
another open controller policy on current parent `1cbb4f8f`. After an established
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
remains explicit. Policy correction and physical tests are pending; no full F03
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

Next, implement explicit failed-hangup handling and compare it against this
baseline, including ordinary successful hangup, carrier loss, pre-CONNECT
cancellation, exit and intentional always-high carrier configurations. Do not
solve this by imposing DCD-low on every startup.
