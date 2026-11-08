# GET/WHEN failure retirement

The full capability22 parent and experimental interpreter now pass two additional
compiled-source failure scenarios beyond the [successful WHEN cases](ASPECT_GET_WHEN.md).
The new evidence exercises native divide unwinding and confirmed cancellation
with an action pending. No application binary, default profile or installed
package changes.

Both cases register immediate PING→TRANSMIT INLINE and deferred PONG→CALL worker.
The script opens a real buffered OWNED.TXT stream and writes BEFORE| before
entering GET. The owned peer supplies PINGPONG after GETREADY. The passive
observer must see the live field with gate0, then the same field with a pending
native CALL gate1 before it admits the BIOS answer.

| Case | Input and handler | Expected result |
| --- | --- | --- |
| Framed worker divide | Accept LoC42; worker verifies local37, transmits WORKER, writes WORKER| and divides by a variable containing zero. | Error11/opcode26h; exact flushed file BEFORE\|WORKER\|; no trailing main/password or BADAFTER command. |
| Pending CALL cancellation | Escape, then native confirmation Yes while the CALL is pending. | Error13/opcode49h; worker never executes; exact flushed file BEFORE\|; no password. |

At child exit the passive observer reads the actual far GET storage. Active,
busy, keyboard ownership, display ownership and completed-output flags are all
zero in both cases. The native error identity matches the child's DOS exit;
script-file status is0. The sampled CRT errno is1, a separate retained value,
not a replacement diagnosis for the explicit divide/cancel result.

Existing parent file-table/sink/history checks, the error display, normal parent
keyboard resumption and clean hangup all pass. INLINE occurs exactly once;
WORKER occurs once for division and never for cancellation. The observer only
reads state and injects ordinary BIOS keys at the checked boundary; it does not
force cleanup, run an action, alter the FILE position or emulate the divide.

```sh
./tools/dev --command python standalone/test_aspect_get_vm_dos.py \
  --parent-dir build/PARENT --child-dir build/GET_CHILD \
  --get-compiler-dir build/GET_COMPILER --when-error-cases \
  --allocation-probe --output build/FRESH_ERRORS
./tools/dev --command python standalone/prove_get_vm_source.py \
  --parent build/PARENT --parent-profile keymap --child build/GET_CHILD \
  --compiler build/DEFAULT_COMPILER/ASPCOMP.EXE \
  --checks build/FRESH_ERRORS/checks.json --output build/FRESH_SOURCE
```

Both programs are compiled by actual DOS8086 ASPCOMP and compared byte for byte
with host output. The isolated public-source proof reproduces the exact parent,
interpreter and compilers, repeats the two failure cases with identical wire
and passive observations, then repeats the two successful WHEN, two GET/EXECUTE
and six ordinary GET cases plus compiler/serial/CLI/file/MZ checks. Sources and
reports are bound by the [receipt](validation/aspect-get-when-errors.json).

This is DOS386/UMB,640KB and a synthetic serial peer, not physical
Boca/SPA2102/SynthModem/BBS acceptance. Each scenario has one child invocation;
repeated failures within one child, post-error script restart, carrier loss,
multiple/rearmed/nested actions, EXECUTE from a handler and full memory pressure
remain unverified here. GET field policies/local/parameter/S0 runtime, floating
support, ordinary8086 parent capacity, three-process compiler residency, package
promotion and full ASPECT/application parity remain open.
