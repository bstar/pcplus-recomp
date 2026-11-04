# Original call timer recovery

The three original timer routines now rebuild exactly from source: start at
CS:3F61(18bytes), seconds-since-midnight at3F73(41bytes), and elapsed update at
37A5(161bytes). Flat binaries match all220 genuine original bytes. Relocatable
OMF forms also assemble. They remain separate from the live terminal until its
call-state and modal-service binding is validated.

## Original policy

The start routine first saves a four-word wall-clock stamp at DS:CFF2, then
reads the clock again for its32-bit seconds-since-midnight anchor at CD8E.
The two reads can straddle a second or midnight; recovery preserves that
behavior. The clock conversion ignores hundredths and calculates
`hour*3600 + minute*60 + second` in DX:AX. It is independent of the modem's
BIOS-tick timeout counter.

Elapsed update subtracts the saved anchor from the current time. If the current
time is earlier, it adds86400 seconds. It calculates hours, minutes and seconds
and formats `%2.2d:%2.2d:%2.2d` into the existing duration string. The anchor is
unchanged. A new call replaces the anchor; update alone does not. These routines
have no logging-enabled check or log-file write, matching the recovered log
controller's clock-before-enable-check order.

The policy is modulo one day: exactly24 hours later displays zero, and setting
the clock backward is interpreted as midnight rollover. It does not count dates
or retain elapsed days. This is an original limitation, not a multi-day timing
guarantee. Any later extension must be identified separately from recovery.
The [Alt-T handler](ELAPSED_TIME_RECOVERY.md) supplies the conditional carrier
check and THIS CALL/LAST CALL view; these routines do not decide carrier state.

## Validation and evidence

The source-only CPU suite executes actual recovered instructions with an
explicit DOS time-structure producer, long division/remainder and sprintf
boundary model. It checks:

- All86400 legal seconds-of-day conversions, including hour arithmetic and
  signed-low-word/carry boundaries; fractional hundredths remain ignored.
- Fourteen start-stamp/anchor cases, including separate reads across second,
  minute, hour,65536-second and midnight boundaries.
- 2788 elapsed pairs: targeted zero/second/minute/hour/high-word boundaries,
  deterministic random pairs, and every minute of duration across midnight.
- A completed midnight-spanning call followed by a newly anchored call in the
  same state owner; update retains the anchor and start replaces it.
- Exact arithmetic/format arguments, callee/caller stack cleanup, DS=SS and
  preserved BP/SI/DI, plus stack guards.

The optional original comparison separately verifies all220 bytes against the
genuine2.01 file before repeating the suite. Matching coverage digests and
current source hashes are recorded in the
[validation receipt](validation/elapsed-timer-native.json). This is not execution
of DOS gettime or the original C runtime itself, an actual DOS modem session,
a live Alt-T command or hardware acceptance.

Fresh REA listing evidence:
`ev_bf3850b87bdcc23f1c9ba31ad7548630966d7132e78b1f1227e584d01d44fe48`
(seconds) and
`ev_caffd24f70912ce218ec4d5271095aeab74c2ed12427a79ee76b9c3497880101`
(update). The start routine is verified by byte Evidence
`ev_dc068807a47c4ae5db785b3003aeefaa263f76f2c5705a033f8e646c49d48ef4`,
its existing caller and terminal RET; Ghidra did not automatically create that
function. Public [provenance](../reconstruction/local_controls/timer-provenance.json)
contains each original file offset, byte hash, mapped state and service boundary.
The complete REA bundle remains in ignored analysis storage. No original
executable or analysis image is an ordinary application build input.

## Live integration still required

Add a call-clock owner that starts once at confirmed connection, updates while
online, and freezes at confirmed disconnect. It must retain LAST CALL through
failed subsequent attempts and work with logging disabled. Bind the original
Alt-T/Alt-Z action after view restoration; service serial/parser/flow/carrier
while the modal view is open, and defer notices until the underlay is released.
Check midnight, clock rollback, reconnect, log-enabled/disabled, failed hangup,
carrier loss while the view is open and partial-CSI admission. Then repeat
source closure, native DOS and Enigma/Synchronet regression and package gates.
This checkpoint changes no application/package bytes or physical machine files.

```sh
./tools/dev --command python standalone/check_elapsed_timer_native.py \
  --output build/NEW-elapsed-timer
./tools/dev --command python standalone/check_elapsed_timer_native.py \
  --output build/NEW-elapsed-timer-original \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```
