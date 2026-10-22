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
Before correction, add a DOS peer that explicitly retains an online connection,
and distinguish failed hangup from intentional carrier-ignore configurations.
Preserve configurable initialization and DTR policy; do not introduce an
unconditional DCD-low startup requirement that breaks such configurations.

~~~sh
./tools/dev --command python3 standalone/check_hangup_retained_carrier.py \
  --output build/hangup-retained-carrier/baseline-new
~~~

`passed=true` means the gap was reproduced. `compatibility_accepted=false`
remains explicit. Actual DOS, policy correction and physical tests are pending;
no full F03 or application gate closes.
