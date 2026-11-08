# Qualified compiler execution and full GET memory admission

The opt-in GET interpreter now calls its already-qualified source-built
`ASPCOMP.EXE` through a small maintained DOS4B00 executor. The former Watcom
`spawnl` call pulled another general process/path implementation into a program
that already contains native process services. Removing that dependency saves
3040 bytes of minimum resident memory, without changing stack, variable, file,
help, display or serial-buffer capacities.

The complete larger keymap parent now passes the six actual GET tests, including
the retained FOPEN stream. This supersedes the startup failure in the
[MZ checkpoint](ASPECT_MZ_LAYOUT.md). It does not close full capacity, help,
nested compiler-under-terminal, package or physical acceptance gates.

## Boundary and ownership

`ASPECT_COMPILER_DIRECT_EXEC` is enabled only for the opt-in GET builder. The
default reviewed build retains `spawnl` and reproduces its previous executable.
The maintained helper is not a recovered original instruction sequence.
General DOS/RUN/SHELL execution keeps its existing native implementation.

Existing source admission still selects the interpreter's sibling compiler,
checks the source and compiler files, creates the private log, redirects standard
handles, pauses serial transmission and enters the compiler divide/vector scope.
The helper has no PATH, BAT or shell interpretation. It creates the bounded DOS
tail and two FCBs on the existing stack, requires DS=SS and interrupts enabled,
and guards against reentry. Before EXEC it saves DS, SS, SP and BP in CS-owned
storage; it restores context before using the returned stack. It waits for child
termination and uses the linked [Watcom DOS error mapper](https://github.com/open-watcom/open-watcom-v2/blob/master/bld/clib/_dos/c/dosret.c)
for failure semantics.

The effective CRT environment is packed into a temporary owned DOS block.
This preserves script PUTENV changes; inheriting the unchanged PSP environment
alone would omit them. Strings and their order are copied without filename or
OEM encoding conversion. Empty environments remain empty, and oversized input
refuses. The block is released after EXEC on success or failure; no parent heap
resize occurs. Existing serial resume, log replay/removal, cancellation and
PSP/vector checks stay in the C owner. Maximum environment pressure and failed
DOS-block release remain separate untested error boundaries.

Native PUTENV uppercases assignments, including values. The new regression
therefore checks `LIVE`, matching the existing runtime, rather than changing
PUTENV semantics to fit its fixture.

## Measured layout and verification

[The receipt](validation/aspect-compiler-exec.json) binds the current sources:

| GET interpreter | Previous | Current |
| --- | ---: | ---: |
| Resident near code | 65405 | 62751 |
| DGROUP | 44096 | 43712 |
| Page minimum including PSP | 139168 | 136128 |
| Stack | 8192 | 8192 |

GET code4079, editor code1544,206-byte field storage and the larger parent's
features are retained. Header alignment and the owned256-byte ASX read window
remain enabled. The native ASPECT arena and every help page buffer remain intact.

The expanded compiler test runs24 cases and249 checks in DOS8086. It covers
source/ASX lookup,79-character and CP437 paths, old-output preservation, effective
environment inheritance, real DOS8 refusal, foreign-DS arithmetic failure,
leaked INT0, cancellation and20 counted compiler replacements. All48 captured
stdout/stderr files match the unchanged reviewed launcher byte-for-byte; test
inputs are identical. The initial environment fixture expected lower case and
failed both launchers; it is not accepted evidence.

Seven actual DOS serial-compilation cases cover N/S/H/B flow and3200-byte
in-flight pressure in S/H/B, retaining unread bytes and checked UART/PIC/vector
state. These use a synthetic serial peer and ASIO driver, not an external BBS.
The full larger-parent matrix separately passes string, integer/long, cancellation,
float refusal and malformed operands, including exact stream content and parent
handle/history restoration. It uses DOS386/UMB and640KB conventional memory.

An isolated public-source replay rebuilds both full executables and the compiler,
reproduces the default launcher, compares the24-case outputs, reruns all seven
serial cases and the six larger-parent GET cases, plus the existing CLI, file and
MZ calibration checks. It uses no original applications, private configuration,
prior objects or ancestor Git.

Default compilers still refuse GET syntax; the optional
[GET compiler profile](ASPECT_GET_COMPILER.md) adds matching grammar and compiled
parent/interpreter cases. Full variable/stream/help co-residency,
ordinary8086 attached memory, repeated/EXECUTE GET, actual WHEN action composition,
remaining field modes/FLOAT.RTE, whole-language parity, package promotion and
physical acceptance remain open. No installed or selected package changes.
