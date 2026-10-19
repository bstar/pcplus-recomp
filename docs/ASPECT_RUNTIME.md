# ASPECT compiled-script execution

This document records the initial 24-slot checkpoint at `1dbbc04`. The
[arithmetic extension](ASPECT_ARITHMETIC.md) added numeric math; the
[current parameter/string extension](ASPECT_PARAMETERS.md) expands it to 39 slots,
132 compiled fixtures and 320 composed DOS cases. Counts and artifact identity
below describe the initial checkpoint.

The standalone owner now executes selected compiled ASX scripts using recovered
8086 instructions and actual DOS files and far-heap allocations. The fixed
`EXECUTE.EXE` diagnostic completes15 authored compiler fixtures: integer/long
assignment, IF/ELSE, comparisons, boolean operations, postfix increment/decrement,
a terminating WHILE loop, calls, local frames and global-string allocation.
Four further compiled fixtures intentionally stop at unavailable float/PAUSE
services, an instruction budget or native recursive-stack overflow.

This is an incremental interpreter composition, not a complete compiler or a
script runner integrated into TERMINAL. All F01–F16 application gates remain
open. [Frozen evidence](validation/aspect-runtime.json) binds sources, artifacts,
compiler-fixture provenance, original comparisons and DOS results.

## Build and execution

Use the pinned Nix toolchain:

```sh
./tools/build test-aspect-operands test-aspect-operations test-aspect-runtime
```

These tests require no original executable, compiler, install or REA database.
The public fixture file contains our authored source and its compiled bytecode;
normal builds materialize those vectors without invoking the original compiler.
`standalone/aspect_execution_probe.py` and `freeze_aspect_execution.py` document
the separate optional compiler-oracle workflow. Original compiler1.01 identity:
`5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a`.

Optional native comparisons, requiring the ignored local original:

```sh
./tools/build test-aspect-operands-compat test-aspect-operations-compat test-aspect-runtime-compat
```

`build/aspect-runtime/EXECUTE.EXE` SHA256:
`75eb875ca12aa1676844754afd41486a421a8679cb2093448753ca845e79ecfb`.
It runs a fixed suite rather than accepting arbitrary scripts on its command line.

## Recovered code and coverage

| Module | Exact native bytes | Evidence |
| --- | ---: | --- |
| Numeric operands |381|4,599 CPU scenarios and16,248 actual8086 DOS assertions |
| Numeric operations |1,182|2,809 CPU scenarios covering all464 instruction addresses;4,439 actual DOS assertions |
| Expression support |501|Optional byte comparison plus composed DOS execution |

Operand units cover D19E..D1B0, DB10..DB65, DC48..DD26 and E0F1..E129.
Operations cover D4A5..D943. Expression support covers D2A0..D2D6,
D3F2..D408, DB7D..DC48, DE4D..DF04 and resident9AC0..9AE7.
Ends are exclusive. Resident9AC0 is unsigned near-byte comparison, not floating
point comparison; retained REA pseudo-code/assembly evidence is identified in
the validation report. Synthetic analysis carriers were never executed.

The composed owner reuses the earlier dispatcher, control-flow, stack,
global-string and abort modules, plus actual native copy and setjmp/longjmp.
Its24 mapped opcode slots are:

```text
03 15 1E 32 48 54 5A 5B 5C 62 68 6D 7F 81 84 94 95 BC BD C7 C8 CF D0 D2
```

All other191 in-range slots abort explicitly. Numeric comparison entry names
refer to native operand order: second decoded operand versus first staged
operand. Compiler output is preserved; source `3 < 7` emits the native greater
entry6D. Relabeling or reversing operands would break execution.

Operand/operation component tests use controlled external services. Their
opaque floating-point models only verify call/ABI boundaries; they supply no
floating-point mathematics. The composed runtime stops on unavailable float
read/conversion services and builtins.

## DOS resource ownership and failure paths

The maintained `runtime.c` owner consumes and validates the string-count header
before dispatch, allocates strings through real `_fmalloc`, and closes actual
stdio files through the checked [file bridge](ASPECT_FILE_FLOW.md). It clears
all128 pointer slots before native allocation, frees successful prefixes after
allocation failure, and invalidates pointers after native release. This avoids
reusing the native release routine's retained freed pointers.

Short operands, failed positions and unavailable commands enter the recovered
abort path and restore the real10-byte BP/DI/SI/SP/IP context. DS=SS and a common
code segment remain required. The source-owned arena initializes the original
relative stack base at +1B1Ah and seeds an owned word below it for framed main
return. Finish resets frame/depth/value-stack state. UI waits and application
callbacks are unavailable in this headless owner; they cannot silently succeed.

The219-case actual DOS suite passes2,179 assertions. It includes19 compiled
fixtures, bad/missing headers, missing files, truncated operands, invalid
opcodes, failed first/second allocation, successful retry and all191 unsupported
slots. Each run verifies closed file ownership, zero live allocations, cleared
string count, reset native frame/stack state and preserved ABI. The128-string
fixture allocates and frees every slot. Recursion hits native error105 after
6,087 dispatched steps; an endless loop hits the maintained instruction budget.
Allocation fault injection is diagnostic-only; successful allocations and frees
still use the actual DOS heap.

## Remaining scope

Native index, type and frame arithmetic remains unchecked. Passing this authored
corpus does not establish arbitrary-bytecode safety. Trusted fixture inputs are
required at this stage. The partial decoder is not a public untrusted-file API.

General arithmetic (including subtraction opcodeB5), strings, typed parameters,
floating-point runtime, application commands, recorder, source compiler and
script invocation/scheduling remain unfinished. The WHILE fixture uses postfix
decrement, not subtraction. Terminal integration also requires deliberate
memory placement: the current terminal's near data/stack is already65,296 bytes.
This standalone owner must not simply be linked into that near segment.
The interactive terminal remains the previously tested731418bd image.

A fresh public-source checkout reproduces74 byte-identical outputs with all
original/install/analysis paths and previous build products absent before
compilation. See [source-build proof](validation/application-components-source-build.json).
This proves component reproducibility, not complete application reconstruction.
