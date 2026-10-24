# Nested DOS compiler memory

The later [compact interpreter checkpoint](COMPACT_RUNTIME_FORMAT.md) addresses
the extra resident cost of the optional native-reset parent. The compiler and
its24KiB stack remain unchanged; ASPECT formatting is intentionally smaller.
The following records the earlier compiler-specific fix and its evidence.

The source-built DOS compiler now fits beneath the full helper-enabled parent
for the recorded bare 8086 serial workflows and 386 BBS workflows. Its grammar,
253-byte source-line bound and 24 KiB reserved stack are unchanged. The fix is in
ASPCOMP; terminal and interpreter bytes retain their preceding identities.

The CLI lends an 11,306-byte automatic context to the compiler rather than
allocating a second copy on the heap. The ordinary compiler API retains its
owned heap context and allocation-fault controls. A new workspace API validates
capacity, alignment, real-mode segment/physical bounds and aliases with the
report and stream objects. It never frees the borrowed context.

Numeric constants share storage for their mutually exclusive DWORD and exact
IEEE 754 payloads. Bounded tags and flags use bytes; node and symbol indices
remain words. Values shrink from 28 to 18 bytes and nodes from 34 to 24. The CLI
also uses fixed text/decimal/hex output instead of the general formatter, keeping
its existing diagnostics and staged-output naming. A 512-byte CRT growth quantum
is defined with the correct near-data qualifier before startup allocations.
This uses the runtime's [documented allocation increment](https://open-watcom.github.io/open-watcom-v2-wikidocs/clib.html#Global_Data), rather than replacing its allocator.

The executable drops from 55,850 to 51,766 bytes. Its paragraph-rounded minimum
DOS process allocation, including the PSP, drops from 79,504 to 75,216 bytes.
Those loader minima do not include every later heap, environment or caller cost.
The 24 KiB stack is not reduced to obtain these results.

## Diagnosis and discarded experiments

The earlier parent compiles a minimal source script; the helper-enabled parent
with the same interpreter, compiler, source, KEY and PRM reports ASPECT error 8.
A declared diagnostic interpreter records one compiler call, failed spawn and
pinned-CRT ENOMEM 5. Its largest DOS free block before main is 6,101 paragraphs
under the earlier parent and 4,918 under the helper parent. Those measurements
include diagnostic overhead and are not a claimed free-block sample at EXEC.

REA verifies the actual interpreter's DOS MZ load image and observes the CRT
spawn boundary reaching INT 21h/AH=4Bh. Static decompilation does not prove the DOS
runtime result; the controlled execution supplies that evidence. The native
mapping/dossier and counters are bound in the [diagnosis record](validation/nested-compiler-diagnosis.json).
The raw DOS kernel error was not captured directly; the recorded 5 is CRT errno.

Near-heap shrinking did not fix the problem and was removed. Size-optimization
and smaller-stack experiments also failed: making the compiler load could still
leave too little heap for its parser workspace. None of those experimental stack
reductions is shipped. The [earlier failure record](validation/hook-source-memory.json)
remains historical evidence rather than being rewritten into a pass.

## Verified scope

The independent [receipt](validation/nested-compiler-memory.json) checks:

- 2,043 actual DOS grammar cases: 1,077 accepted byte-for-byte against the maintained
 host compiler and 966 rejected, with existing ownership/publication faults.
- 18 maximum-line CLI expression cases with stack checks enabled on the real 24 KiB
 CLI. A 2 KiB CLI fails with the actual stack-overflow message and produces no ASX.
 The 16 KiB checked API corpus remains passing.
- 12,746 borrowed-workspace checks, including 100 reuse cycles, foreign heap and
 stream ownership, guard bytes, short/wrapping/unaligned/physically aliased spans.
- Eight bare 8086 COM1/COM2 workflows: explicit ASP, missing-ASX fallback, chained
 source with retained numeric/BREAK state, and rejected-source recovery. Exact
 ASX, absence of compiled output on rejection, post-child RX/parser/TX, PRM and
 selected UART restoration are checked. No TSR consumes guest memory here.
- Twenty-two source-lifecycle cases/223 checks and seven UART cases, including
 three 3,200-byte pressure cases. These separately exercise compiler faults,
 vectors, cancellation, repeated compilation, flow control and unread suffixes.
- Actual source login, three helper calls and unsaved stock editor return on
 Synchronet immediate and ENiGMA 30 ms, on the 386 profile. The passive screen
 observer is explicitly loaded high and its captured CS is checked against the
 raw SCRIPT.BIN; selecting LOADHIGH alone is not counted as proof of placement.
- Seven products reproduced from 713 declared sources in an empty tree, with no
 original executable, installation, image, REA database or prior object input.

The 8086 DOSBox profile limits the address bus below the emulator's UMB setup
requirement. Its observed BBS source attempts still fail when the screen TSR
occupies conventional memory. Those failures are retained. The 386/upper-memory
BBS results and bare 8086 serial results have distinct scopes; this is not a
promise about arbitrary TSRs, larger sources or every conventional-memory budget.
Stock ENiGMA's immediate-forwarding issue, native compiler families beyond the
maintained subset, full application gates and physical modem testing remain open.
The card was not remounted or changed during this source checkpoint.

## Reproduction

Use the pinned toolchain and fresh output labels:

```sh
./tools/dev --command python3 standalone/build_aspect_compiler_dos.py
./tools/build test-aspect-compiler-workspace test-nested-compiler-memory
./tools/dev --command python3 standalone/check_aspect_compiler_stack.py \
  --output build/compiler-stack-next
```

For the BBS source composition, use the existing owned loopback fixtures and
select `--source --hook-session accept --cpu 386 --observer-high` with the
helper-enabled terminal and `build/aspect-register-parent/ASPECT.EXE`.
ENiGMA's passing comparison explicitly requires `--packet-delay-ms 30`.
