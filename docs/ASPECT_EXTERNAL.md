# ASPECT external command frontends

The maintained host and DOS compilers now emit native DOS, RUN and SHELL records.
Their native frontends assemble and pass CPU and actual DOS ABI checks. **General
external execution is not enabled in the interpreter.** These three slots still
stop with explicit unsupported error3. The supported runtime count remains105
of215; no application gate closes.

The next step is the application executor/controller below. A direct call to a
generic spawn function would leave required display, keyboard and UART ownership
unimplemented, and is not substituted for that controller.

The [native process foundation](NATIVE_PROCESS.md) now supplies real recovered
environment/tail/spawn/EXEC with maintained allocator/trap bindings:20 actual DOS
cases/678 assertions, including real memory exhaustion and arena restoration.
It is an explicit component target; application display/UART/shared-state
ownership, production namespace binding and these three runtime slots remain unfinished.

The [namespace extension](NATIVE_NAMESPACE.md) now adds real native PATH,
COM/EXE/BAT order and SYSTEM fallback:55 DOS cases/2,053 assertions pass,
alongside the separate678-assertion core regression. Nested allocations and
far-backed arena restoration are real. Production binding of those policies
and the remaining controller ownership requirements below are still open.

## Recorded grammar and behavior

DOS and RUN take one atomic string and optionally NOCLEAR or WAIT. One comma
may precede that option. Expressions, parentheses, numeric operands, trailing
punctuation and combined options reject. SHELL takes no operands. The70 authored
original-compiler cases establish29 exact accepted ASX outputs and41 rejections;
both maintained compilers match them. The full8086 DOS compiler passes2,003
deduplicated cases:1,037 exact accepted outputs and966 rejections.

RUN skips leading bytes carrying the native C classification whitespace bit:
TAB, LF, VT, FF, CR and ASCII space. It then splits on the first literal space.
Tabs inside the filename do not split, quotes have no special grammar, and the
remaining argument string retains its spaces. DOS passes its whole input string
unchanged to the command-processor route, with a null separate argument pointer.

The shared frontend calls the application executor with five near arguments:
program, separate arguments, command-processor flag, wait flag and save-screen
flag. NOCLEAR selects save0/wait0; WAIT selects save1/wait1; absence selects
save1/wait0. Raw unrecognized option bytes retain save1/wait0, although source
compilers reject such options. DOS/RUN store the raw executor return word in
comparison.

SHELL looks up uppercase COMSPEC, passes that pointer with null arguments and
flags0/0/1, and leaves comparison unchanged. Component tests retain null/empty
COMSPEC at this boundary rather than inventing fallback behavior. The native
executor's name validation assumes a pointer; maintained admission must resolve
this before safely enabling the command.

## Recovery and verification

REA/Ghidra identifies192 exact instruction bytes: DOS/RUN wrappers and their
common parser in overlay18, plus SHELL in overlay3. Another92 bytes reuse the
already recovered strcpy/strchr. The source-generated C table preserves exactly
the observed whitespace bit; unrelated classification bits are not substituted
for other application services. Numerical original ranges/hashes and saved REA
identities bind the recovery. Ordinary builds read neither originals nor REA
databases, and analysis carriers are never executed.

The1,514 source cases and1,514 matching original comparisons cover all option
bytes, leading character bytes, whitespace, empty/trailing/doubled spaces, tabs,
quoted text, COMSPEC results and raw return words. They check complete nonstack
memory, stack cleanup, BP/SI/DI/DS=SS/ES and DF. Operand reads, environment lookup
and the five-argument application executor are explicit boundaries. This is not
a DOS process or physical UART test.

The source-built EXTERNAL.EXE executes the relocatable OMF frontends under8086
DOS:53 cases/436 assertions check arguments, flags, status, stack guards and the
near ABI. Its executor/environment bindings are authored recorders and never
launch a program. A separate DOS test compiles all70 frozen sources and checks
all29 accepted ASX products exactly, then verifies that production ASPECT rejects
each at its actual28/9B/A3 opcode. A source-built child sentinel detects accidental
launches, and a safe synthetic COMSPEC prevents an accidental interactive hang.

```sh
./tools/build test-aspect-external test-aspect-external-compiler
./tools/dev --command python3 standalone/test_aspect_external_dos.py --label NEW
```

The [ledger](validation/aspect-external.json) distinguishes native/OMF boundary
checks, compiler checks and deliberate product rejections. Existing ENiGMA login
and file workflows are regression evidence only; they do not exercise these
unpublished external commands.
All23 existing expanded ENiGMA checks pass with the new compiler, the composed
runtime still passes1,111 cases/26,686 assertions, and the tested interpreter
and terminal binaries remain unchanged. A fresh original-free snapshot reproduces
278 normal outputs byte-for-byte. The refreshed package includes the expanded
compiler; it does not turn the modeled executor into a production service.

## Required application executor/controller

The original [PROGRAM executor](PROGRAM_EXEC.md) is already recovered separately,
including COMSPEC/PATH/extension lookup, environment/tail construction and DOS
EXEC. Its UI, allocator and serial dependencies must be integrated rather than
replaced by successful no-op stubs. The declared frontend ABI is in
`src/aspect/external_runtime.h`; the production dispatch table intentionally does
not reference the new handlers yet.

1. Bind execution to the current source-owned environment, command-tail and
   namespace policies. Verify direct COM/EXE, extension/PATH and batch/COMSPEC
   routes, missing/invalid targets, raw termination/exit words and failure
   continuation. Preserve the separately recorded legacy batch behavior.
2. Own nested process/trap lifetime. Reuse the established neutral INT0 bracket
   where appropriate, preserve PSP/INT23/24/DS=SS, release only unused memory,
   retain script/session state and reject reentry before mutation. Test children
   with foreign DS, replaced vectors, abnormal exits and insufficient memory.
3. Integrate display, cursor, geometry/font and native WAIT/NOCLEAR lifecycle
   through actual recovered PROGRAM services and the admitted renderer platform.
   The current terminal controller admits mode3/80x25/page0; broader original
   views remain part of the full application requirement. Verify a child that
   changes video mode, subsequent parser output and restored parent input.
4. Add a real UART release/restore owner for an arbitrary external child. The
   compiler bracket keeps the ASPECT IRQ active and is insufficient for a child
   that takes the port or vector. Preserve the raw ring, flow ownership, DTR,
   configuration and restoration ordering. Test COM1/COM2, S/H/B/N policies,
   queued input, child port/vector changes and post-return interaction; physical
   Wi-Fi modem timing remains a separate requirement.
5. Verify six held script streams, ASX continuation, file positions, settings,
   directory/translation/render leases and environment persistence across actual
   execution. Exercise nested source compilation after return and ordinary
   parent/BBS input, plus Escape/timeout/error unwinding at the relevant boundaries.
6. Publish all three runtime handlers only after these ownership paths have real
   implementations and application evidence. Then repeat the whole runtime,
   source compiler/EXECUTE, terminal handoff and intended BBS workflows. Partial
   compiler/frontends are not completion of the external-program requirement.
