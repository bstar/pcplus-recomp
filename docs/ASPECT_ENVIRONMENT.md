# ASPECT environment commands

Both maintained compilers and production ASPECT now support GETENV/PUTENV.
The dispatcher implements105 of215 slots and rejects110. Native command/CRT
recovery and the maintained ownership adapter have separate controls; the full
application, compiler/recorder and physical modem gates remain open.

```text
string directory
proc main
putenv "LOC_WORK=C:\GAMES"
if success
getenv "loc_work" directory
message directory
endif
putenv "LOC_WORK="
endproc
```

GETENV takes an atomic string name and writable string destination; PUTENV takes
one atomic assignment string. Globals, locals, parameters and string registers
work. Expressions, parentheses, wrong types and readonly destinations reject.
The48 original-compiler cases establish19 exact accepted outputs and29 rejections,
matched by both maintained compilers.

## Native behavior

GETENV uppercases a private name copy, performs case-sensitive lookup, preserves
the value's case, clears missing results and flushes writable destinations. It
leaves comparison unchanged. For values over80 bytes, its bounded copy helper
raises native warning3. Component tests exercise the original returning-warning
truncation; the maintained interpreter retains its existing typed error7 and
unchanged-output policy. The original interactive warning UI remains open.

PUTENV uppercases **the whole assignment, including its value**. The first equals
sign separates name/value; further equals signs belong to the value. Empty names
work, empty values delete, and missing equals signs return FFFFh. Success reports0
in comparison. Name matching is exact; source inputs remain unchanged.

The native CRT borrows the assignment pointer. Reusing the command's temporary
buffer for LOC_A and LOC_B consequently loses the first name. Actual DOS probes
also show that Watcom's PUTENV borrows its input and rejects empty names, so it
cannot directly replace the recovered behavior.

## Maintained ownership and process lifetime

The adapter uses the recovered lookup/update routines. On first mutation it
clones the pointer vector while retaining the original CRT vector and strings.
New nonempty assignments receive owned near-heap storage before native update.
Realloc operates only on the private vector; publication updates ordinary C
`environ`. A collector frees only owned assignments no table slot references.
Inherited strings are never freed or changed.

The process environment survives script completion, later invocations, EXECUTE
and post-mutation script errors. Ordinary DOS children inherit the updated table.
Per-script finish deliberately does not release this process owner. A callback
using Watcom's actual callback ABI restores the borrowed vector and releases all
private storage before normal CRT shutdown. Interpreter entries remain cdecl.

Preparation/value/growth failures report FFFFh without publishing the new value.
The native deletion policy remains: deletion has already occurred if shrinking
realloc fails, and still reports0. The adapter retains that valid larger vector
and retires the removed assignment; it does not claim rollback for that path.

## Validation

REA/Ghidra identifies555 exact new bytes for commands, bounded result copying,
lookup/update and name matching, plus237 reused bytes for five string primitives.
Flat outputs match original ranges/hashes. The697 source cases and697 original
comparisons cover case rules, missing/empty/long values, updates/deletes, allocation
results, buffer aliasing and full nonstack/BP/SI/DI/DS=SS/ES/DF guards. Operands,
near realloc and returning warnings are explicit component boundaries.

The actual8086 DOS suite passes403 interpreter invocations/3,119 assertions over31
rounds. It checks inherited mixed-case values, independent assignments, replacement,
deletion/empty names, malformed input, local/parameter/register/alias destinations,
unchanged inputs and six occupied file slots. It proves persistence across
invocations/EXECUTE, ordinary child inheritance, automatic exit restoration,
long-value errors, post-mutation divide/budget exits, admitted allocation faults
and final vector/near/far heap/JFT/INT0/FLAGS/ABI restoration. A separate native
control passes9 checks while reproducing the missing first value.

The production ASP CLI compiles/runs these commands. Actual terminal login is
gated on inherited values, independent assignments, deletion and exact ENV.LOG
before the existing query/file/timestamp checks. The full DOS compiler passes
1,932 deduplicated cases (1,008 exact accepted/924 rejected); the composed runtime
passes1,111 cases/26,686 assertions. Query and timestamp regressions pass341/2,905
and248/2,907; assertion totals include the updated linked heap shape.

```sh
./tools/build test-aspect-environment test-aspect-environment-compiler
./tools/dev --command python3 standalone/test_aspect_environment_dos.py --label NEW
```

The isolated ENiGMA `--environment-login` mode requires owned lookup/deletion and
ENV.LOG before all previous probes/authentication and the actual custom
search/index/DIZ/NFO route. It uses a staged decoder/generated catalog, not a
live-server installation. The [ledger](validation/aspect-environment.json) binds
all current binaries, controls, application checks, package and clean build.
All23 expanded ENiGMA checks pass. A fresh snapshot without originals reproduces
271 normal outputs byte-for-byte; the refreshed package matches the tested
executables. The terminal binary and64832-byte DS=SS layout remain unchanged.

An initial DOS harness omitted stdlib and stopped at C compilation, before any
script ran. It remains retained. Flat reconstruction also corrected a RET4 range
endpoint and preserved native alignment NOPs; all555 bytes now match. Normal
builds and the public repository contain no original executables, private
configuration or REA databases. Complete application/recorder and physical
validation remain unfinished.
