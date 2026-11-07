# Native errors during ALARM

A native transmit timeout inside ALARM previously skipped the alert's cleanup.
The interpreter returned serial error14 while the speaker gate remained on,
the child speaker owner remained acquired and the temporary duration stayed6
instead of returning to4. The new optional-profile checkpoint returns that
error through the alert's ordinary cleanup before propagating it to the VM.

The current candidate is `b4f0aecc`; parent `689bdce9` is unchanged. The
[validation record](validation/aspect-alarm-unwind.json) binds the pre-fix
failure, current sources/products, positive captures, memory funding, cold
rebuild and diagnostic reuse. Installed RCC859D7 and the release selector
remain unchanged. The subsequent [matched-package checkpoint](ALARM_CONNECTION_RELEASE.md)
passes fresh modern BBS and complete-package software gates. Physical acceptance
and the remaining original-feature inventory are still open.

## Owned error return

The exact recovered controller and operand wrapper remain unchanged. Its
maintained bridge records its own near stack, SS, flags and callee-saved
registers around the native alert. An ordinary native abort checks the existing
external-PROGRAM recovery owner first. When no such owner is active, an active
ALARM checkpoint can restore only its matching stack and return to the
cooperative caller. Otherwise the recovered VM abort path remains in use.

That caller records service failure, retires its running state and attempts
generation-safe speaker release normally. After the DOS/tone owner retires, a
checkpoint-qualified WHEN unwind clears the abandoned callback bookkeeping
and key lease. The operand wrapper can then restore the configured duration,
and the original typed runtime error propagates to ordinary VM finish. Finish
disarms the native disconnect registration and closes script resources. No
success result or keyboard event is manufactured from the error.

The checkpoint does not promise recovery from a foreign stack, kernel or
allocator corruption, or recursive cleanup faults. Failed speaker release
still follows the existing quarantine rules. Synchronous native TRANSMIT
retains its own configured stall deadline; the progress watchdog does not
preempt an in-progress callback. The timeout test explicitly uses
`PCPLUS_TXWAIT=2`.

## Actual modem and interpreter tests

The owned peer sends HOLD, then a cursor query, then closes its TCP socket.
DOSBox-X's real virtual-modem device changes DCD and emits NO CARRIER. The
passive observer does not write product state, modem inputs or parser replies.
It verifies upper-memory residency and reads the child duration/disconnect
state, speaker gate, parent resources and actual post-return command screen.

Each case runs with sound enabled and `alarm 6`:

| Disconnect registration | Expected result |
| --- | --- |
| None | Alert completes; main file operation follows |
| Framed CALL | Worker preserves local37; file order is BEGIN, CALL37, MAIN |
| TRANSMIT modem AT | Exactly one AT action after loss; alert completes |
| TRANSMIT with XOFF retained | Serial error14; main tail does not execute |

All four cases pass separately with ANSI profile6 and VT220 profile4. In the
failure case the speaker gate/owner are zero at exit and duration is4. The
disconnect registration is retired. Normal handlers disarm while duration6 is
still active; the failing TX action retains its registration until VM finish,
matching its native success-only disarm behavior. Exact peer bytes and event
ordering prove the cursor reply precedes hangup. Parent JFT/sink owners return
unchanged, owner flags retire and the restored PROCOMM PLUS command screen
opens afterward.

The old-profile negative capture still shows gate3/owner1/duration6 with typed
error14, bound to its actual public4057dd3 application sources. Early fixture
attempts are separate: an inherited8086 setup aborted before ALARM, and an
older menu-title matcher missed the current restored command screen. Accepted
fixtures require actual UMB residency and capture the full screen.

## Same-process reuse

A separately marked diagnostic replaces only the CLI entry. All205 other
backend objects are byte-identical to the current ordinary candidate. It
retains one serial/render lifetime and calls the real VM three times: first
the failing XOFF script, then a recovery script twice. The recovery uses all
six file slots and runs another alert.

The observed results are14,0,0. Every invocation retires the DOS/cooperative
ALARM owner, external checkpoint, globals, streams and frame depth. The abort
outcome changes from1 to0 on later normal entries. DS equals SS throughout,
IF/DF and INT0 remain consistent, JFT bytes match before/after, and all six
slot files contain two exact PASS markers. This prevents DOS process exit
from hiding a stuck owner. **Never package or deploy the diagnostic.**

## Memory funding and reproduction

The first correct cleanup build increased minimum process memory to131344
bytes and failed seven checks in the existing held-stream/nested-child test.
The optional CLI now folds reserved-device name bytes once rather than repeating
the same comparisons. Both actual source branches match on113580 DOS8086 cases:
all uppercase three-letter stems; case and byte substitutions in reserved
names; port suffix bytes; rooted/dotted paths; lengths0–512; fixed-seed byte
strings and NULL handling. Accepted and rejected path behavior is unchanged.

Only `runner.o` differs between the unfunded and funded cleanup builds. The
funded minimum including PSP is131168 bytes, saving176 bytes; no stack, buffer,
slot capacity or CRT growth limit is reduced. The386 held-stream profile passes
all27 checks and the8086 stream-around-child profile passes all26, with three
nested children in each. The ordinary interpreter rebuild is still exactly
`91256a7b`.

A5420-file public-source export reproduces the parent and funded interpreter.
It repeats the bank API, legacy/progress clock suites,113580 CLI comparisons,
1024 slot/four deep-expression cases, one ordinary ALARM case and the actual
ANSI XOFF/carrier error. It does not repeat every root matrix, same-process
diagnostic or capacity test.

The current receipts are under `build/alarm-carrier-funded-ansi-20261106`,
`build/alarm-carrier-funded-vt220-20261106`,
`build/alarm-carrier-reuse-funded-20261106`,
`build/alarm-unwind-funded-capacity[-8086]-20261106` and
`build/alarm-unwind-funded-cold-20261106`.

New Enigma/Synchronet regressions for these exact candidate bytes, package
selection, physical Boca/SPA2102/SynthModem acceptance and the remaining
application inventory are still open. Previous BBS results belong to the
preceding interpreter, not this new build.
