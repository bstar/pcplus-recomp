# DOS compiler port

The DOS compiler is being ported from the maintained host compiler, preserving
its existing language coverage and original-compiler bytecode expectations.
The maintained host compiler grammar now has a source-built8086 DOS port,
`ASPCOMP.EXE`, producing complete ASX programs. The interpreter still reports
unsupported when an ASP needs compilation; automatic runtime compilation is the
next integration task. Original language families beyond the maintained host
subset and the recorder remain unfinished. ASPLEX/ASPINV/ASPEXP are separate
developer diagnostics.

The normal builds use the pinned Nix Open Watcom toolchain, large-model C and
an8192-byte stack for lexer/inventory and32768 bytes for recursive expression
parsing/emission and complete compilation. They read only maintained C sources
and public headers.
Neither the original compiler/executable, host ASPECT compiler, fixture database nor REA
analysis is an input to their application build.

```sh
./tools/build aspect-compiler-lexer aspect-compiler-unit aspect-compiler-expression aspect-compiler-dos
./tools/build test-aspect-compiler-lexer test-aspect-compiler-unit test-aspect-compiler-expression test-aspect-compiler-dos
```

## Streaming lexical stage

`compiler_lexer.c` borrows a binary FILE and reads one physical line at a time.
It retains the host's253-byte line bound, original source bytes, counted token
lengths and32-bit physical line/byte positions. CRLF is one line boundary;
standalone CR/LF and the remaining CP437-representable host `splitlines`
boundaries are handled explicitly. SUB is not an implicit EOF. Quoted strings
retain CP437 bytes, semicolons, carets and embedded NUL; outside quoted strings,
ASCII tokens fold to lowercase and the host's whitespace classes are retained.
The lexer recognizes the entire host token grammar, including incomplete-number
prefix boundaries, exponent/suffix combinations and longest operator forms.

No whole-file input allocation is required. A returned line/token view belongs
to the caller until the next read. Explicit token lengths prevent NUL from
silently truncating a literal before the later operand validator can reject it.
Read/length/character/position failures are sticky, and neither the reader nor
token copier closes the source. The ALX1 output from ASPLEX is a diagnostic
stream, not bytecode.

Actual DOS tests compare all1164 unique corpus/boundary sources with the host
regex, including accepted lexical forms inside grammatically rejected sources.
The comparison covers92324 physical lines,75247 tokens and2131983 output bytes.
It checks exact normalized bytes, spans, original source positions, four actual
CLI outcomes, source offsets/line counts beyond65535, reader errors, unchanged
output on rejected token copies and borrowed FILE lifetime. The diagnostic
reports2389 DOS checks. This is lexical evidence, not language acceptance.

## Declaration and procedure inventory

`compiler_unit.c` allocates owned declaration/procedure records, global indices,
local offsets and parameter offsets, plus source ranges for declarations,
hoisted initializers and executable body lines. It retains procedure order,
local/global shadowing, per-type global limits, local limits, reserved builtin
names and the host's parameter-layout arithmetic. Parameter words retain their
wire-width wrap; this is not evidence that an oversized parameter frame is safe
to execute. Every declaration line remains available to the validation pass,
including a trailing part the host inventory did not materialize.

Names and ranges do not borrow the lexer's reusable line buffer. One owned
allocation registry retires partial or complete units. Failure preserves the
borrowed FILE and diagnostics, clears public references and releases each
allocation. A loaded unit rejects another load until retired; disposal is
idempotent. Large-model pointers allow records to use memory outside DGROUP.
The AUN1 stream from ASPINV is an inventory diagnostic, not ASX.

The1174 actual DOS first-pass cases compare with the maintained host's
collection pass with emission disabled.1133 produce an inventory and41 fail in
this pass. Comparisons cover complete symbol/procedure order, type/space/index,
frame size, parameter bytes, initializer token slices/chaining and all retained
source ranges. Unknown or malformed body expressions can legitimately pass an
inventory; every body and initializer still needs validation before compilation.

Eighteen allocation-failure positions and200 successful load/dispose cycles
restore independently observed heap allocation addresses and sizes. A foreign
block and the borrowed source stay live. Six controlled heap corruptions or
capacity failures test the observer's rejection paths. The final suite performs
3346 checks, including actual ASPINV CLI children.

## Pinned CRT heap-check boundary

A separate malloc-only DOS program reproduces a far-heap-check failure before
any frontend code is linked: the pinned `_fheapchk` reports3 with one ordinary
allocation and after it is freed. An independent read-only observer sees a valid
heap with used count1 then0. The native near-heap checker remains part of the
ownership test; the allocator and production CRT have not been replaced.

REA/Ghidra observation
`ev_d1a5f2f22b386770e1316405e3db283a854074f3496c79f5004bb421f01b9b66`
recovers the linked267-byte `__HeapWalk` in the retained malloc-only probe artifact. Its
NULL-entry path depends on the nonzero heap segment, bypassing the expected
entry-offset check. This is a static observation of that pinned binary, combined
with the separate DOS reproducer; it does not claim an upstream fix or diagnose
every Watcom release. The upstream implementation uses based pointers in its
[far-heap walker](https://github.com/open-watcom/open-watcom-v2/blob/master/bld/clib/heap/c/heapwalk.c).

`standalone/compiler_heap_snapshot.c` avoids based-pointer null conversions.
It checks the actual segment chain,22-byte headers, tagged block boundaries,
four-byte end marker, allocation/free counts and circular free-list links and
sizes. It records used blocks without allocating or changing the heap. Cached
rover/largest-block hints are outside this observer's validation scope. Failed
observer attempts, the corrected diagnosis and complete REA evidence remain in
ignored local history; current reports bind the successful observer and its
isolated reproducer separately.

## Expressions and operand fragments

`compiler_expr.c` parses the maintained host precedence and associativity into a
caller-owned bounded AST. It resolves global/local/parameter symbols and typed
builtins, validates lvalues and atomic command operands, and retains the special
unsuffixed integer boundary `-32768`. Parentheses, prefix operations, coercions,
chained and compound assignments, temporary slots and short-circuit expressions
retain the host's wire behavior. Branch lists use an indexed pool outside the
recursive stack; nested boolean emission recycles patched entries.

`compiler_output.c` writes little-endian bytes/words/DWORDs to a borrowed FILE,
checks DOS signed seek limits, preserves the append cursor around patches and
retains sticky range/I/O errors. `compiler_emit.c` emits typed operands and
position-dependent CP437 string encoding directly to that stream. Fragments at
prefixes65535,65536 and70000 compare exact absolute branch targets and strings.

`compiler_decimal.c` converts decimal literals using bounded2048-bit integer
arithmetic and exact rational division with nearest/even IEEE754 rounding. It
handles subnormals, underflow, overflow and long exponents without a floating
point instruction or library conversion. Unary negation preserves negative zero.
A real DOS test found the pinned CRT `strtod` rounded
`100591108740498876e-335` one bit below the host result; that failed case is now an
explicit regression. The compiler uses the integer converter instead.

Actual8086 DOS tests with the emulated FPU disabled compare3459 expression and
assignment cases against the maintained host:2530 accepted fragments match
byte-for-byte and929 reject. Cases include existing source corpus assignments,
seeded mixed expressions, integer wrap with original boolean truth, all typed
symbol spaces, invalid destinations, string bounds/NUL/CP437, recursive bounds,
temporary255/256, decimal rounding ties and overflow/underflow boundaries.
The original compiler rejects the malformed WORD operand `-32768.0` with C021.
Both maintained compilers now return a typed rejection; the earlier host
`TypeError` is corrected using that independent DOS oracle.

Separate1356 DOS API checks exercise patch bounds, real offsets above64KiB, cursor
restoration, read-only output, sticky write errors and caller FILE ownership.
One hundred alternating successful/rejected compilations preserve independently
observed allocated block addresses/sizes and a foreign allocation. Six actual
ASPEXP CLI children cover successful expression output, typed rejection, negative
and overflowing line numbers, missing source and usage rejection.

ASPEXP's `AEX1` header and following expression/assignment bytes are a developer
fragment protocol. They are not a loadable ASX program. No statement compiler or
runtime source fallback is enabled by the fragment tool. A fresh source checkout
without originals or analysis reproduces153 normal outputs, including ASPCOMP;
production TERMINAL/ASPECT executables retain the previous checkpoint's bytes.

## Complete maintained DOS compiler

`compiler_program.c` combines the inventory, expressions and real FILE writer
with complete maintained statement and procedure emission. `compiler_commands.c`
ports all current command/setting/FETCH/WHEN forms. Typed calls retain parameter
order and frame cleanup. IF/ELSEIF/ELSE, WHILE and SWITCH keep exact implicit CASE
fallthrough, DEFAULT and nearest-loop exit/continue behavior.

The compiler validates every body and initializer before discarding procedures.
An independent ten-case original DOS compiler probe confirms rejection of
unmatched declaration parentheses, including global/parameter declarations and
unused procedures, and the real WORD boundary above. Two accepted declaration
cases retain frozen original ASX bytes. Both host and DOS compilers validate all
retained declaration lines so a trailing malformed part cannot disappear in the
inventory pass. The inventory diagnostic itself deliberately remains a first
pass and is not a whole-program acceptance check.

Procedure selection repeatedly removes zero-reference procedures, preserving
MAIN and mutually referenced dead cycles. Declaration order and the initial
jump when the first declaration is not MAIN remain exact. An initial full
validation emission is discarded and truncated before the final selected pass,
so removed tails cannot survive in ASX. Procedure/condition/CASE targets remain
32-bit, including actual outputs beyond64KiB.

The1173 actual8086 DOS program cases match the host:718 complete accepted ASX
files are byte-identical and455 reject. Cases include the entire existing source
corpus, native declaration edges, typed parameters, nested loops, dead chains and
cycles, invalid unused initializers/bodies, large pruned tails and complete
program/conditional/call targets beyond64KiB. The suite runs with FPU disabled.

There are1693 additional API/publication checks. Twenty-six program allocation
failures and29 inventory allocation failures restore live allocation identity
and sizes, preserve a foreign allocation and leave borrowed FILEs owned by the
caller. One hundred successful full compiler cycles repeat that ownership check.
Same-FILE source/output is rejected, writable scratch output is truncated, and
read-only output returns an I/O error.

The CLI compiles into an exclusively reserved sibling staging name, closes the
source and compiled file, then publishes the validated result. Replacement keeps
a backup until rename succeeds, restores it on a failed publication rename and
reports its path if restoration fails. Eleven actual CLI children cover default
and explicit output, replacement, syntax/missing-input errors, source collision,
missing output directory and directory targets. Two additional diagnostic CLI
children force the publication rename to fail: one verifies actual DOS rollback,
and the other also fails restoration and verifies that the backup retains the
previous bytes. The latter backup is restored by the test caller. Normal ASPCOMP
links no fault hook. Tested failures preserve source and prior ASX data; all
temporary files and successfully retired backup names are checked.

A DOS-produced69-byte ASX then runs in the actual maintained ASPECT interpreter,
printing0,1,2 and COMPILED IN DOS through arithmetic, looping, conversion and a
procedure call. This verifies explicit compilation and execution, not automatic
ASP loading, serial ownership or physical modem behavior.

The package now includes ASPCOMP. Inside DOS, from the staged program directory:

```text
ASPCOMP HELLO.ASP
ASPECT HELLO.ASX
```

An explicit output is also supported: `ASPCOMP HELLO.ASP DEMO.ASX`. Output must
be a distinct `.ASX` path. Normal application builds do not read original
compiler executables, host compiler code, fixtures or REA databases.

## Remaining compiler work

1. Integrate explicit ASP and missing-ASX ASP fallback into the checked loader.
   Preserve UART lease, flow/error handling, settings, filename label,
   file/global cleanup and source namespace across compiler invocation.
2. Scope INT0 ownership across nested compiler EXEC so a compiler fault cannot
   reenter an interpreter trap with the compiler's DS/SS. Verify child PSP,
   vector restoration, errors/cancellation and the actual DOS/BBS workflows.
3. Expand beyond the maintained host grammar to full original compiler coverage,
   add the recorder and finish the remaining application services. Additional
   malformed/native language edges still need independent original evidence.

No F01–F16 whole-application gate is closed by this compiler checkpoint.
