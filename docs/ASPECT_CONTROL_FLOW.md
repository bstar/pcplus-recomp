# ASPECT compiler control-flow evidence

72 source-owned scripts were submitted to the original pinned ASPCOMP1.01:
49 accepted and23 rejected. The resulting ASX files were inspected but not
executed in this experiment. This constrains the maintained compiler and VM
reconstruction; it does not implement either or establish their runtime behavior.

The optional private harness is `standalone/aspect_flow_probe.py`. It requires a
new ignored `analysis/aspect-vm-runtime/control-*` output directory and accepts
`--only` selections. `standalone/record_aspect_flow.py` verifies the three saved
reports and freezes sanitized observations in `validation/aspect-flow.json`.
Historical source hashes differ as the corpus expanded; each original run is
preserved with its recorded source hash and all rejected fixtures.

## Observed emission

All numbers in the following token column are hexadecimal. Targets are absolute
32-bit little-endian **file offsets including the ASX header**, not16-bit near
code addresses or relative instruction displacements.

| Construct | Observed form |
| --- | --- |
| Call without callee frame | D0 C7 target32 |
| Call with callee locals or parameters | D0 C8 target32 |
| Main procedure after another procedure | Header,62 main-target32 |
| Conditional false branch |15 target32 |
| ELSE/loop-back/EXITWHILE/LOOPWHILE branch |62 target32 |
| RETURN or ENDPROC without frame |94 |
| RETURN or ENDPROC with frame |95 |
| Local storage reservation | D2 size16, before procedure CF |
| Caller argument adjustment | D2 signed-negative16, after call |

Matched CALL and GOSUB sources emit identical bytes. For a procedure with a
D2 local-storage prefix, its call target points to that prefix rather than CF.
WHILE back edges and LOOPWHILE point to the condition's5B record; EXITWHILE
points beyond the loop. The caller argument adjustment is an emission
observation; its complete runtime semantics still need native VM composition.

Cases FARCALL and FARMAIN create67,214/67,216-byte ASX files and reach target
positions0x10689 and0x10688. FARIF/FARWHILE conditional fields target0x10690 and
0x10695. Their nonzero upper words rule out a16-bit target interpretation.
None of these large ASX files was executed, so this does not establish large-file
VM runtime correctness.

## Parameters and numeric typing

Accepted syntax includes `CALL helper WITH 7`. WITH is required before actual
arguments. The tested comma-separated and whitespace-separated argument forms
compile identically; parenthesized `(7)` fails C001 in the tested context.
Numeric and string actual arguments use CC/CD prefixes followed by typed operand
records. INTPARM, LONGPARM, STRPARM and FLOATPARM imply argument adjustments of
-2,-4,-81 and-8 respectively. Two integers use-4; integer plus string uses-83.
A parameterized callee uses return95 even with no local declarations.

Two integer parameters use operand97 with16-bit offsets10 and8. In the tested
mixed integer/string case, numeric97 offset89 and string96 offset87 appear.
These offsets must be interpreted with the native frame layout; they are not
indices in the global string table.

`7L` emits long operand AC followed by32-bit7. Decimal32768 and65535 infer long
in the tested parameter contexts. Unsuffixed7, hex0x8000 and an integer variable
fail LONGPARM matching with C049; a long variable is accepted using operand A2.
Decimal2147483648 is also accepted and emits80000000, matching-2147483648.
This permissiveness is recorded as original behavior, not a prescribed future
validation policy.

## Scope and next integration

The tests establish emission for the listed fixtures, not a general grammar,
complete expression decoder or safe recursion implementation. Earlier selected
original application flow probes in [ASPECT_DISPATCH.md](ASPECT_DISPATCH.md)
are separate and do not execute the parameter or large-file cases here.

The next interpreter work must compose the recovered dispatch, real DWORD file
positions, typed value/frame stack, expression readers and resource/error owner.
The existing native setjmp/longjmp source in
`reconstruction/transfer_session/{setjmp,longjmp}.asm` can support actual
nonlocal-unwind composition once its10-byte context and DS=SS/CS invariants are
verified with this dispatcher. The current dispatcher and globals diagnostics
use declared callback models and do not prove that composition. Complete
compiler/VM/recorder and application script integration remain open under F13.

The subsequent [execution composition](ASPECT_EXECUTION.md) now verifies native
setjmp/longjmp with this dispatcher, including an actual value-stack guard
failure and direct/chained-script context restoration. File-backed targets,
call/return frames and typed expression execution remain the next dependencies.
