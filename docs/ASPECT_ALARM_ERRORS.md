# ALARM operand errors and subsequent reuse

Five actual-parent/interpreter error cases pass, followed by a seven-invocation
recovery test in one terminal process. Products remain `689bdce9` parent and
`9d44b523` child. The [validation record](validation/aspect-alarm-errors.json)
binds current sources, manifests, authored/mutated bytecode, raw observer reports,
wire captures and the later recovery. No application or installed bytes change.

| Authored operand case | Child result | Meaning |
| --- | ---: | --- |
| Signed -1 | 7 | Operand error |
| Wide integer encoding 8000h (signed -32768) | 7 | Operand error |
| Invalid operand tag FFh | 7 | Operand error |
| End of file before option flag | 5 | File/input error |
| End of file before literal value | 5 | File/input error |

The normal source compiler supplies each script. The shared fixture helper
changes only the declared ALARM operand bytes or truncates at the declared
boundary. It requires a unique valid instruction pattern before mutation.
The signed -1 case is emitted directly by the compiler. This is a bounded set
of authored cases, not a claim of arbitrary-bytecode safety.

Each script reaches its entry marker, then aborts without transmitting the
following `BADAFTER` marker. The actual DOS exit status matches the expected
typed error. Existing parent JFT, sink ownership, renderer and keyboard checks
pass. Passive speaker/child-state observations show no speaker activity, gate
and owner zero at exit, duration four and DS equals SS. These operand errors
occur before the alert acquires its foreground owner.

The recovery test starts a valid script, invokes all five errors through the
parent's configured hotkeys, then invokes the valid script again. The passive
exit witness records exactly seven attached ASPECT invocations and results
`0, 7, 7, 7, 5, 5, 0`. Every exit has DS equal to SS and zero cleanup error,
external scope, display owner and native program/process busy state.

Both valid invocations open all six buffered output streams, write a prefix,
execute a real authored DOS COM child with NOCLEAR, write a suffix and close
the streams. Exact final stream bytes and two appended child-log markers prove
both completions. The script also completes `alarm 0`; two `RECOVEROK` wire
markers and subsequent parent keyboard input are required. No restart or
replacement of the terminal happens between failures and recovery.

The accepted captures are:

- `build/aspect-alarm-vm-dos/errors-groups-20261106`: five individual error
  cases, `checks.json` and `speaker-checks.json`.
- `build/alarm-error-recovery-final-20261106/result.json` with raw telemetry
  under `build/connection-dos/alarm-error-recovery-final-20261106`.

The recovery runner reconstructs the original individual fixtures and requires
byte-for-byte equality before compiling equivalent direct-invocation fixtures.
Those remove the login/HOLD waits needed by the individual connected tests;
the invalid operand remains the same. Application sources and ordinary binary
input checks remain intact.

Three fixture mistakes were retained outside the accepted evidence: the first
negative probe expected successful-alert text after the abort; the first
recovery setup did not stage ASPECT alongside the parent; and the next setup
incorrectly treated the deliberately written child log as an immutable input.
The final fresh run creates that log as output and passes every immutable-input
check. None of these failed attempts is counted as application acceptance.

Native bounded-integer checking is retained. The maintained interpreter aborts
on typed errors; it does not reproduce the original's optional unchecked or
error-returning configurations. These tests use standard BIOS/ANSI, emulated
UART, an owned raw modem peer and passive UMB observers. They do not cover a
carrier/service failure while the ALARM owner is active, physical modem/SIP/
audio behavior or full-duration service budgets. Those gates, packaging and the
remaining full-parity inventory stay open. The installed RCC859D7 package is
unchanged; no new cold rebuild or modern BBS regression is claimed for the
unchanged application products.
