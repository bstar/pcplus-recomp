# ASPECT procedure parameters and string execution

This document records checkpoint `5bd8aa5`. The
[current string-command extension](ASPECT_STRING_COMMANDS.md) expands the
standalone runtime to 50 slots and 184 compiled fixtures. Counts and identities
below describe the parameter/string checkpoint.

The standalone owner now executes typed procedure arguments and string
assignment using recovered PCPlus instructions. Compiled fixtures verify mixed
integer/long/string arguments, nested calls, caller and callee locals, by-value
parameter mutation, empty strings and 80-character strings.

The composed suite passes **320 actual 8086 DOS cases and 4,760 assertions**.
It executes 132 authored original-compiler fixtures: 113 complete and 19 reach
their expected error boundaries. The supported table grows from 36 to 39 slots
with string assignment AC and parameter pushes CC/CD. All other 176 slots
abort explicitly. This remains a standalone diagnostic composition; complete
ASPECT, source compilation and terminal integration are unfinished.

[Frozen evidence](validation/aspect-parameters.json) binds source, compiler
provenance, component comparisons and actual DOS file/heap execution.

## Build and verification

Ordinary original-free tests use the pinned Nix toolchain:

```sh
./tools/build test-aspect-parameters test-aspect-strings test-aspect-runtime
```

Optional native byte comparisons require the ignored local executable:

```sh
./tools/build test-aspect-parameters-compat test-aspect-strings-compat test-aspect-runtime-compat
```

The first string DOS run exposed an uninitialized guard byte in the diagnostic
assertion. Its failed record is retained locally; initializing the guard corrected
the fixture, with all 617 native bytes unchanged. The corrected CPU and DOS
results are the evidence cited here.

Normal builds use authored source and frozen compiled fixtures. They do not
invoke ASPCOMP, read the original executable/install or require REA databases.
`EXECUTE.EXE` runs the fixed suite; it is not a general command-line script
runner. The original compiler remains an optional oracle rather than the final
source toolchain.

## Native recovery

| Component | Native bytes | Verification |
| --- | ---: | --- |
| Parameter primitives | 66 | 3,901 CPU scenarios, all 30 instruction addresses; 9,731 actual DOS assertions |
| String operands and assignment | 617 | 2,251 CPU records, including 1,920 literal contexts; 14,441 actual DOS checks |

Parameter entries D1B0..D1F2 implement stack-relative address calculation,
numeric argument pushes and string argument pushes. Integer, long, float and
string widths are 2, 4, 8 and 81 bytes. The numeric push caches its raw token,
checks integer/long classes and routes every other class to the float service.
That fallthrough does not establish parser acceptance of arbitrary tokens.
Component float/string readers supply opaque buffers; composed string fixtures
instead use the recovered decoder and actual DOS storage. Float remains an
explicit unavailable service.

String recovery covers DF04..E0CC, DD68..DD9C, DE11..DE1C, E0E4..E0F1,
resident 9286..92A4 and 76B0..76B3, and overlay 17 EEF0..EEFF and EF1D..EF42.
Ends are exclusive. These routines select builtin/local/global strings,
decode literals, manage scratch buffers, copy between near/far memory, bound
optional lengths and assign strings. DS=SS and DF=0 remain required.

Eleven 81-byte scratch buffers rotate modulo 11. A global read copies its real
far allocation into one scratch buffer. A destination read also records the
pending far pointer and scratch address; assignment flushes all 81 bytes back
and clears the pending address. The scratch pointer preserves native E104
aliasing with the dispatcher next-script pointer; CHAIN/state999 ownership
remains unsupported. Local strings and parameters use near frame
addresses. The native far-copy and get-DS instructions execute in both the
component and composed tests.

The literal tests cover lengths 1..80, all 12 strides and both parities using
independently encoded payloads. The transform constants are the recovered
algorithm constants already used by [the literal codec](ASPECT_LITERAL.md).
Scratch rotation, far writeback, valid/invalid selectors, default/explicit copy
lengths and returning/stopping range errors remain separate test groups.

The original empty-string builtin is index 19. Its dispatch table routes to
resident thunk C2C7 and overlay 16 DAFB, returning a pointer to NUL at DS:4942.
The maintained bridge supplies its own fully readable 81-byte zero buffer.
Other string builtins remain unsupported; no factory string table is embedded.

## Compiler observations

The canonical parameter/string oracle contains 40 authored cases: 27 accepted
and 13 rejected. It reproduces all 24 accepted outputs from the earlier
canonical corpus. The accepted fixtures have independent hand-derived expected
bank values and string contents: 23 complete; two stop on unavailable floats,
one on division by zero, and one on native value-stack overflow.

The original syntax declares formal arguments with `intparm`, `longparm` and
`strparm`, and passes actual arguments after `WITH`; commas are optional in the
tested forms. Numeric formal selectors 97/98 and string selector 96 carry
16-bit frame-relative offsets. Calls use framed C8 targets and adjust the
argument area afterward. Parameter mutation changes the callee's copy, while
the caller's globals retain their values.

Direct arithmetic actual arguments fail in the tested spaced, unspaced,
parenthesized and bracketed forms. Precomputing into a typed variable works.
Malformed count/type/WITH cases retain their original compiler diagnostics.
String assignment uses AC, with global selector 8C or local/formal selectors
A0/96; the tested ordinary assignment records end in a zero option byte.
Compilation observations and successful execution remain distinct evidence.

## Ownership and failure paths

Actual DOS far allocations and files remain owned by `runtime.c`. Diagnostic
builds snapshot string values before native release, so tests can check outputs
after real frees. The snapshot storage is absent from non-diagnostic builds.
Initialization clears scratch and pending state; finish clears pending near/far
references and scratch cursors after success or nonlocal abort. Length-range
checking is enabled by the maintained owner, whose errors always unwind.

Three compiled fault fixtures exercise active parameter state with a live
global string: recursive string arguments hit native error 105 after 376
instructions; division inside a typed callee returns error 11; an unavailable
float argument returns error 4. All preserve the committed string snapshot,
free the far allocation, close the file and reset frames/value-stack state.

A separately labeled maintained fixture removes the final option/return bytes
from a compiled two-global assignment script. The checked file bridge aborts
before writeback: the first global remains `HELLO`, and the second stays empty.
The pending destination is discarded and both allocations are freed. A
subsequent ordinary assignment succeeds. Every composed case also verifies
interrupt-vector restoration, IF/DF preservation and near ABI invariants.

Native literal decoding ignores a short fread result and can decode leftover
scratch bytes. The component suite preserves that behavior as a named quirk;
the composed checked file bridge aborts short reads. Index, frame, type and
scratch arithmetic remains unchecked in recovered code. These authored fixtures
do not prove arbitrary-bytecode safety or full rollback of native state.

## Remaining scope

String command families, other builtins, floating-point mathematics, the source
compiler, recorder and application invocation/scheduling remain unfinished.
Near-memory placement must be resolved before terminal integration. All
F01–F16 whole-application gates remain open, and the interactive TERMINAL image
remains unchanged at SHA256
`731418bde8f3264d5f6c987195eb54b20c86a2981259ea1c721ba252e3c9a776`.

Current `EXECUTE.EXE` SHA256:
`b320b02b1ccbc847c9fe1292d284377eb81cbd364437b11b981b5518d7eb986a`.
A fresh original-free source checkout reproduces 78 byte-identical outputs;
see the [source-build proof](validation/application-components-source-build.json).
