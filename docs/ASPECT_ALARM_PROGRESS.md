# ALARM progress budget and pending-key completion

The opt-in interpreter now bounds work between valid observed second changes
instead of imposing a single service-call limit on an entire alert. This keeps
long alerts viable while preserving a finite escape from stalled clock/tone
helpers. A pending completion key also survives the final service-credit
boundary. The recovered native ALARM controller's instruction bytes are unchanged.

The current parent remains `689bdce9`; the new interpreter is `12c5f77e`.
The ordinary interpreter remains byte-identical (`91256a7b`). Installed RCC859D7
and the release selector are unchanged. The
[validation record](validation/aspect-alarm-progress.json) binds sources,
products, modeled clock tests, product gates, cold reproduction and BBS captures.
This is still a development checkpoint, not an accepted release or full parity.

## Policy and correction

The preceding VM passed2000000 as a total service-call budget regardless of the
requested duration. A sufficiently active polling loop could therefore expire
before32767 observed second changes. The new `alarm_coop_run_progress` renews
its remaining budget only when native flow already requests a valid second
value that differs from its previous observation. It makes no additional DOS
clock call per service poll. The VM still uses2000000 credits, now per progress
interval rather than for the whole alert.

The existing `alarm_coop_run` and `alarm_dos_run` retain their total-budget
semantics for existing callers and fault diagnostics. New DOS/VM adapters opt
into the progress policy explicitly. Callback accounting saturates at the
32-bit maximum; it is separate from the remaining watchdog credits.

A frozen DOS seconds source does not renew the budget. A stuck BIOS tick wait
or tone loop cannot reach a new native seconds observation, so it remains
bounded too. Context, service and speaker faults keep their existing cleanup
and ownership rules. This is a maintained scheduling policy around the exact
controller, not a claim that the original program had this watchdog.

The new boundary tests exposed another issue: after a key was detected on the
last credit, the controller's final peek spent another credit and produced a
budget error before reading the key. The cooperative adapter now retains that
observed pending key for the final peek. Its exclusive key lease and read-time
context check remain in place. A key arriving after an exhausted budget is not
fabricated or consumed.

## Verification and limits

The existing total-budget regression passes94 cases/1701 checks. The new DOS8086
suite passes33 cases/1457099 checks with the real recovered controller and
explicit modeled clock/key/speaker/receive callbacks. It covers both sound
policies, durations0/1/4/59/60/32767, independent second/day rollovers, frozen
seconds/ticks, last-credit and too-late keys, service faults, invalid clocks,
busy/reentry and retained cleanup recovery.

With four service polls per modeled BIOS tick, the total-budget control stops
at2000000 calls before the requested duration. The progress policy completes
32767 counts with2359226 quiet calls and2359262 sounding calls. These are fast
modeled clock runs in actual DOS8086, not nine hours of wall-clock or physical
modem operation. The initial new-suite run failed the last-credit key cases;
the corrected fresh suite passes them. Earlier overflowing diagnostic check
counts were widened before accepting the final suite.

Five actual-parent native WHEN/render cases pass on the new interpreter.
Three sounding Escape/printable/F1 cases also pass: exact wire, receive query
response, speaker gate/owner release and child duration restoration at exit.
The no-TSR386 held-stream capacity test passes all27 checks, retaining six
buffered streams and three real nested children. No stack, stream, numeric slot
capacity, buffer size or CRT growth setting is reduced. The child's minimum
including PSP is131152 bytes,208 above the preceding build.
The8086 stream-around-child profile also passes all26 checks with three nested
children and clock queries.

A5415-file public-source cold export reproduces both products and repeats the
94-case legacy and33-case progress suites,33341 bank API checks,1024 native
slot/four deep-expression cases and one actual-parent ALARM case. It does not
repeat all root WHEN/key/capacity/BBS matrices. An initial completed cold run
failed in report aggregation because its new model case count was an integer;
the corrected fresh export is the accepted proof.

Stock Synchronet's editor/external COM viewer return and Enigma's carrier-loss,
redial and exact65539-byte transfer retry are separate loopback regressions.
Their captures and the independent carrier audit are bound in the record.
They exercise staged SynthModem Telnet code, not physical SIP/audio/DSP,
analog carrier or hardware CTS stalls.

Failures during an active alert, including carrier/service errors and their
full VM cleanup, remain open. The preceding
[operand-error checkpoint](ASPECT_ALARM_ERRORS.md) covers failures before
foreground alert ownership. Packaging, physical tests and the remaining full
application inventory still require acceptance.

The subsequent [native-error checkpoint](ASPECT_ALARM_UNWIND.md) fixes the
active-alert timeout cleanup gap and funds its memory cost. Its new candidate
identity and acceptance limits supersede this checkpoint for that path.
