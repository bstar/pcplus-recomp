# Maintained DOS process boundary

`src/process/dos_exec.asm` provides a source-built, bounded DOS EXEC backend.
`src/process/program.c` adds the command-processor policy used by live KEY
PROGRAM actions. These are maintained implementations. The exact recovered
PCPlus executor, its provenance and unresolved application services are separate
in [PROGRAM_EXEC.md](PROGRAM_EXEC.md).

## Raw EXEC ABI

```c
unsigned __cdecl process_run(const char *path, const char *tail,
                            process_result *result);
```

The near caller removes six argument bytes; DS must equal SS. Path is an
ASCIIZ string of 1..127 bytes, and optional tail is ASCIIZ with 0..126 bytes.
CR/LF, wrapping extents, aliases with backend-owned state, and a result overlapping
an input are rejected before DOS IO. A null tail means empty; a null result is
allowed. BP/SI/DI/DS/ES/SS/SP are preserved. Calls are nonreentrant.

| Return AX | Meaning |
| --- | --- |
| 0 | EXEC succeeded and child termination status was collected |
| 1 | Invalid arguments or host state |
| 2 | Parent memory resize failed |
| 3 | EXEC failed |
| 4 | Backend already busy |

The optional eight-byte result contains four words: status, raw DOS error,
child termination/exit AX from INT21h/AH4Dh, and retained parent paragraphs.
Invalid/busy calls leave the caller's result untouched. A nonzero child exit
code is distinct from an EXEC failure.

The host initializes `process_psp`, `process_keep_paragraphs` and
`process_minimum_paragraphs`. Before the first child, AH4Ah shrinks that PSP
allocation to the retained count. Later calls reuse that allocation. The live
terminal computes the count through its statically allocated stack top, rounded
up to a paragraph; this covers its code/data/BSS/stack without a heap or runtime
overlays. This policy cannot be reused unchanged by a host which allocates
objects above that boundary. A successful shrink is not grown back afterward.

The backend constructs the length-prefixed DOS tail and final CR, prepares two
FCBs with AH29h, and calls AX4B00h with an inherited environment. CS-owned scratch
saves SS/SP/DS before EXEC; the returned context is restored before touching the
parent stack or data. AH4Dh then collects child status. There is no PATH search,
UI, UART ownership policy or automatic file execution in this raw API.

## PROGRAM command policy

`program_execute(command, result)` is near C caller-cleanup four bytes; the
nonoverlapping eight-byte result is required. It accepts 1..51 stored command
bytes and rejects CR/LF or a missing bounded terminator. It passes exactly
` /c ` followed by the stored command to a command processor. Caret, tilde and
other characters are literal input to that processor: KEY TEXT expansion is not
applied, although the selected command processor has its own syntax.

Environment lookup validates the PSP environment segment and MCB extent, scans
only the owned span, and requires complete string termination. Variable names
`COMSPEC` and `PATH` are case-sensitive, matching the recovered lookup behavior.
The search is:

1. Nonempty COMSPEC, within the 127-byte executable path capacity.
2. `COMMAND.COM` in the current directory/search behavior of DOS EXEC.
3. Each nonempty bounded PATH component with `COMMAND.COM` appended.

Fallback proceeds only after EXEC errors DOS2/3/5, corresponding to the native
file/path/access fallback cases. Other errors stop the search. Empty inherited
environments are allowed; malformed environments return status5, and argument
failure returns status1. Raw EXEC statuses0..4 retain their meanings. The result
reports the selected command processor's termination status, which need not be
the nested application's exit code.

DOSBox's virtual `COMMAND.COM` resolves even with COMSPEC/PATH emptied in the
isolated DOS diagnostics. It returns zero in the tested `/c` workflow although
the nested synthetic CHILD.COM returns37. Real DOS tests therefore establish
nested execution and exact child arguments; modeled DOS-kernel tests separately
establish candidate order, missing-processor failures and child status handling.
They do not turn DOSBox behavior into a claim about every DOS command processor.

## Verification

```sh
./tools/dev --command python standalone/build_process.py
./tools/dev --command python standalone/check_process.py
./tools/dev --command python standalone/check_program_process.py
./tools/dev --command python standalone/test_process_dos.py
./tools/dev --command python standalone/test_program_process_dos.py
```

The raw backend has 68 linked CPU inputs; PROGRAM policy has 57. Only declared
DOS-kernel boundaries are modeled. Tests cover clobbered child context, near
extent/alias limits, resize/EXEC errors, exact tails, inherited environments,
COMSPEC/PATH ordering and malformed environment spans. Isolated DOS diagnostics
execute only synthetic source-built children. Live UART/video scheduling and
its independent tests are described in [LIVE_PROGRAM.md](LIVE_PROGRAM.md).
