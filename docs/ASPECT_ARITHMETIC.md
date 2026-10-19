# ASPECT arithmetic execution

The standalone ASPECT owner now executes integer and long arithmetic through
recovered PCPlus instructions, including addition, subtraction, multiplication,
division, remainder, negation, compound assignment and compiler-generated
precedence temporaries. It passes 105 authored compiled fixtures: 90 finish
successfully and 15 stop with their expected distinct errors.

The complete composed diagnostic passes **295 actual DOS cases and 3,794
assertions**. It uses actual files, far-heap allocations, the recovered
interpreter routines and the recovered resident long helpers. This expands the
supported opcode table from 24 to 36 slots; the other 179 slots abort explicitly.
It remains a fixed diagnostic suite rather than a full script runner or a
terminal-integrated interpreter. All whole-application gates remain open.

[Frozen evidence](validation/aspect-arithmetic.json) binds the compiler corpus,
source, native comparisons, component tests and composed execution.

## Reproduction

Ordinary tests use the pinned Nix toolchain and require no originals:

```sh
./tools/build test-aspect-long test-aspect-arithmetic test-aspect-runtime
```

Optional comparisons use the ignored local PCPlus executable:

```sh
./tools/build test-aspect-long-compat test-aspect-arithmetic-compat test-aspect-runtime-compat
```

The public fixtures contain our authored scripts and their compiled ASX bytes.
`standalone/aspect_arithmetic_probe.py` documents the separate compiler oracle;
`standalone/freeze_aspect_arithmetic.py` verifies its provenance and publishes
independent expected bank values. Ordinary builds never invoke ASPCOMP.

## Native code and independent checks

| Recovery | Native range, ends exclusive | Checks |
| --- | --- | --- |
| Overlay 17 arithmetic | EBB1..EE4A, 665 bytes | 3,668 CPU scenarios; 29,056 actual 8086 DOS assertions |
| Resident long arithmetic | Ten units, 535 bytes | 4,626 CPU scenarios; 4,622 actual DOS checks |

The arithmetic module exports add, subtract, multiply, divide, modulo, negate,
bitwise AND/OR/XOR/NOT and shifts, plus the shared division and zero-divisor
entries. It calls the previously recovered numeric load/store services.
Its component tests control operand, long-helper, error and float boundaries.
They cover 252 of 253 native instruction addresses. EE28, a jump after a
returning floating-point service, remains unvisited because that service stops
as unavailable. Those models do not establish floating-point mathematics.

The separate resident module implements the actual long helpers and their
value-returning cores. It verifies all 248 instruction addresses, low/high-word
carry and borrow behavior, signed division truncated toward zero, remainder
sign, multiplication wrapping, and shifts. It has no callback substitutes.
The composed interpreter links these actual helpers.

Resident units are 9950..9982, 9A1A..9AB4, 9AB4..9ABF, 9AF2..9B11,
9B12..9B31, 9B90..9BAF, 9BB0..9BCC, 9BCC..9BE8, 9C7C..9D1C and
9D1C..9D27. DS=SS remains required for near stack and pointer operations.

Word shifts use native 8086 CL behavior. Unicorn applies later-x86 count
masking, so component CPU mathematical expectations cover counts 0..31;
the actual DOS 8086 suite covers every count 0..255. Long shifts use one-bit
loops and the count's low byte, including counts larger than 31 and high-byte
truncation. No 286+ masking policy is substituted.

## Compiler observations and execution

The arithmetic compiler oracle retains 88 authored cases; 86 compile and two
unary-plus cases fail C036. Independent hand-derived expectations cover all 86
accepted scripts, including input-variable snapshots as well as outcomes.
Seventy-five complete; eight stop on division by zero, two raise native word
IDIV faults, and one requests an unavailable float service.

| Source operation | Native opcode |
| --- | --- |
| Addition | 00 |
| Subtraction | B5 |
| Multiplication | 7D |
| Division | 26 |
| Remainder | 7B |
| Unary minus | 7E |

The corpus checks integer/long compound assignments, parentheses, precedence,
left-associative subtraction/division, mixed-width operands, negative results,
chained assignment and signed boundaries. Declarations determine actual operand
width: the variable-typed word minimum/-1 cases fault, whereas some literal
expressions promote to long. Long minimum/-1 wraps to 80000000; its remainder
is zero. The original compiler also accepts literal 4294967296 and emits zero;
that observation does not define the policy of a future source compiler.

The first private compiler probe had colliding authored case names. Its actual
sources/results remain retained; the canonical second probe adds a uniqueness
guard and restores the missing compound division/modulo cases. Only that second
probe supplies public arithmetic fixtures and claimed results.

## Maintained fault ownership

The recovered division handler reports native error 2 for a zero divisor.
The maintained owner maps it to `ASPECT_RUN_DIVIDE_ZERO` (11) and unwinds without
resuming the native helper's optional returning-error path.

Signed word minimum/-1 reaches native IDIV and raises INT0. Direct component
CPU tests preserve that fault. The composed owner introduces an explicit DOS
policy: save the existing INT0 vector, install a temporary handler for the run,
and restore the saved vector after the dispatcher returns. The handler changes
the saved return CS:IP to an abort trampoline and IRETs. This restores interrupt
FLAGS before the trampoline enters the existing native nonlocal abort path,
which returns `ASPECT_RUN_ARITHMETIC_FAULT` (12). It neither calls DOS on the
interrupt frame nor resumes the faulting arithmetic instruction.

Every composed case checks prior-vector restoration and IF/DF preservation,
in addition to file closure, zero live allocations, reset frames/value stack
and the near ABI. Two maintained ownership fixtures change only the global
string-count header of compiler-authored fault scripts from zero to two. Both
allocate real DOS strings, fault, free both allocations and close the file;
a subsequent assignment script succeeds. They are labeled maintained fixtures,
separately from the 105 original-compiler-produced vectors.

## Remaining work

Strings, parameters, float runtime, system/application services, source compiler,
recorder and invocation/scheduling remain unfinished. Bitwise/shift component
coverage does not establish compiler grammar or every combined script workflow.
Native unchecked index/type/frame arithmetic still limits this owner to trusted
authored fixtures. No arbitrary-bytecode safety is claimed.

The interactive terminal is unchanged at SHA256
`731418bde8f3264d5f6c987195eb54b20c86a2981259ea1c721ba252e3c9a776`.
Its 65,296-byte near data/stack segment requires deliberate memory placement
before ASPECT can be integrated. These standalone diagnostics do not close F13
or any other complete-application gate.

Current `EXECUTE.EXE` SHA256:
`a351b3255a688311dda84bf0811baa47cf3f607f27f60e154f6f74453c9a3a3c`.
A fresh original-free source checkout reproduces 76 byte-identical outputs;
see the [source-build proof](validation/application-components-source-build.json).
