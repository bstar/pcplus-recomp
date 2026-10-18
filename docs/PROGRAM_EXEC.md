# Native PROGRAM execution

This module recovers **3,102 exact original bytes**:3,072 instruction bytes,
ten CS-owned writable save bytes and a20-byte DOS-to-CRT error map. Source
covers resident433d application executor,896a command-processor route,8e12
environment lookup,65ca environment/command-tail construction, extension/PATH
resolution,6a22 DOS EXEC and shared string/error helpers. Flat NASM output
matches SHA-pinned regions from PCPlus2.01 original6401ccfd…7196904.
Provenance distinguishes resident code offsets from the overlay32 data table
and records saved/current REA evidence IDs.

`PROGRAM_EXEC_OMF` produces relocatable objects. Ordinary builds use source and
recorded digests only; `recover.py` is an explicit analyst operation requiring
the ignored original. Some string/name helpers duplicate independently tested
META recovery ranges; do not add overlapping ranges twice when measuring total
unique application recovery.

This is an executable recovery with explicit dependency gaps, not complete
live PROGRAM support. The original heap/farheap allocator, external screen/UI,
mouse/vector and serial services remain named external interfaces. The source
DOS diagnostic uses the original low-level EXEC core, with a maintained startup
memory shrink, and launches only its synthetic source-built CHILD.COM.

## Near ABI

DS=SS and DF clear. Listed arguments follow the return address. Unless stated,
caller removes arguments. All exported original entry points are near calls.

| Export | Arguments / return |
|---|---|
|program_execute|program,command line,command-processor flag,wait flag,save-screen flag; caller10; BP/SI preserved by its own frame; AX child/service status,1 invalid name,ffff already busy or spawn failure|
|program_system|command pointer; caller2; routes through COMSPEC; command0 queries interpreter availability using file access and returns1/0|
|program_getenv|name pointer; caller2; AX pointer after matching `NAME=`, or0; case-sensitive name match; BP/SI/DI preserved|
|program_spawnv|mode,filename,argv pointer,environment pointer; caller8; adds/searches extensions and invokes extension-specific route|
|program_spawn_search|mode,filename,argv,environment; caller8; retries bare missing filename through PATH|
|program_spawn_extension|mode,filename,argv,environment,extension kind; caller10; kind0 is batch route through COMSPEC; other kinds run filename directly|
|program_environment_tail|argv,environment,result allocation pointer,result aligned-environment pointer,tail buffer,extra environment executable-name pointer,batch filename pointer; caller14; AX environment byte count orffff, outputs pointers and byte-counted CR-terminated DOS tail|
|program_exec|mode,filename,byte-counted command tail,aligned near environment offset; caller8; mode0 calls4B00, mode1 calls4B04; other modes returnffff/errno22 before DOS; AX receives4D child status orffff on failure|
|program_spawnl|mode,filename,argv0,...,0; variadic caller cleanup; delegates through recovered spawnlp/search path|
|program_map_error|AX DOS error; no stack arguments; stores low raw DOS error and maps to original CRT errno|

The EXEC core preserves BP/SI/DI, restores its own SS/SP/DS after DOS, and
restores a four-byte pair at original DS002e/0030. ES and other working registers
are volatile. It does not promise to preserve the caller's IF: its recovery
sequence uses CLI, restores SS/SP, then STI. Internal error epilogues and the
stack-probe helper require their original calling frames and are not ordinary
standalone APIs. The documented MODE1 4B04 path has CPU instruction coverage
only; DOS kernel compatibility for that mode is not claimed.

`program_saved_sp/ss/pair_low/pair_high/ds` belong to the **code segment**, not
DGROUP; the original code writes them using CS overrides. The OMF data/map
state aliases must be linked into the same near-code environment. This shared
scratch makes the helper non-reentrant. The parameter block and FCB state are
explicit DS linker symbols, with offsets/segments populated before EXEC.

## PROGRAM versus HOOK versus TEXT

Native KEY kind1 calls433d with text,0,1,1,1. Its stored string passes unchanged
to896a and the command processor: **no TEXT caret expansion or pause processing**
applies. Native KEY kind2 HOOK uses the separate414c generated pointer protocol
and433d's direct spawn branch. TEXT's4934 grammar is unrelated.

The command-processor route looks up uppercase `COMSPEC`. It builds argv from
the interpreter name, `/c` and the exact stored command. If COMSPEC is absent,
it tries `command.com`. If the first attempt returnsffff, fallback occurs only
when **CRT errno is2 or13**, not when raw DOS error equals13. The original error
map sends DOS2/3 to CRT2 and DOS5 to CRT13; raw DOS13 becomes CRT22 and does not
trigger that retry. The recovered20-byte mapping table closes this distinction.

The native environment lookup is case-sensitive and requires an exact name
followed by `=`. Path lookup also uses uppercase `PATH`; its parser separates
entries at semicolons, with no invented shell quoting or modern path grammar.
Filename extension resolution tries `.com`, then `.exe`, then `.bat` when no
extension was found after the last slash/backslash. Direct batch invocation
uses COMSPEC and `/c `, and the tail builder overwrites the last four filename
bytes while appending arguments: `OWNED.BAT /Q` becomes `/c OWNED /Q`. This
legacy behavior is preserved separately from normal SYSTEM, whose stored
command string remains intact.

## Tail, environment and memory ownership

Builder65ca joins argv entries after argv0 with spaces, including an initial
space when arguments exist. It writes a length byte followed by those bytes
and a carriage return. Its original maximum is **125 tail bytes including
spaces**; a126-byte composed tail returnsffff with CRT errno7/raw error10.
A maintained DOS backend may deliberately choose a different explicit limit;
that does not change the native comparison baseline.

The environment builder copies the selected/default near environment vector
into an aligned block. Depending on original runtime state, it can add encoded
`_C_FILE_INFO` handle metadata and the DOS environment executable-name suffix.
It uses the original near allocator and a farheap fallback/scratch path. This
module recovers the actual builder but leaves heap implementation external;
CPU tests use a declared bounded arena recorder, not an invented CRT heap.
Allocation failure, tail overrun and ordinary free paths are covered. The
special farheap-success copy/free branch and inherited handle metadata need
further full-runtime validation.

The low-level6a22 helper:

1. Prepares environment, tail and FCB far pointers; invokes DOS29 filename/FCB
   parsing twice.
2. If gate DS8e24 equalsd6d6, invokes the original indirect overlay callback
   with BXffff. The callback implementation/meaning is unresolved here.
3. Saves SS/SP/DS and the DS002e/0030 pair in its CS-owned save cells, calls DOS
   4B00 for mode0, then restores its own stack/data context even if DOS clobbered
   it.
4. Calls DOS4D on successful EXEC, or maps the DOS error on failure. The runtime
   execution-active flag DS7b4a returns to zero.

It does **not** shrink the parent memory block. Original CRT startup815c uses
DOS4A, and runtime helper9338 can resize a block. A new MZ with maxallocffff
usually owns the remaining conventional-memory allocation; a maintained host
must first shrink its PSP-owned allocation while retaining every resident code,
data, BSS, stack and ISR byte. The diagnostic does that in its own startup.
It does not recover the original CRT heap manager or claim automatic parent
heap expansion after the child returns.

## Application handoff dependencies

The larger433d wrapper performs work beyond DOS EXEC. It rejects empty or
leading-`[` names through4748, then rejects re-entry while DS333c is set. It
saves cursor/display dimensions, handles optional screen snapshots, selects
command-processor/direct execution, optionally waits for a local key, and
restores display/cursor/UI state. It handles dimension changes and selected
error/exit statuses before clearing its busy byte.

These original service boundaries remain explicit:

- 6b5a/6b42 save/restore cursor position;6bbe/4870 snapshot/restore screen;
 6d1a re-reads BIOS display state; additional display/UI functions remain external.
- 76b4 probes/resets mouse state;76ea restores mouse configuration.
- 758a restores saved INT1B/INT23 vectors and Ctrl-Break state before the child;
 7508 reinstalls the application's handlers afterward when requested.
- 03a7 reinitializes the selected UART/driver state after the child. Its saved
 export calls existing UART configuration routines, but the complete surrounding
 application port/vector policy is not supplied by this module.

The standalone assembly makes unresolved services trap rather than silently
skip them. CPU comparisons intercept those declared boundaries only to record
arguments/order. A maintained live host must implement and validate its own
suspend/resume policy before offering arbitrary PROGRAM actions. The generic
source-owned process backend is a separate component, not a substitute claim
that all original application services have been recovered.

## Verification

```
./tools/dev --command python3 standalone/build_program_exec.py
./tools/dev --command python3 standalone/check_program_exec.py
./tools/dev --command python3 standalone/check_program_exec.py --original
./tools/dev --command python3 standalone/test_program_exec_dos.py
```

Five CPU groups cover55 cases and55 optional genuine-original comparisons:
125/126-byte tail boundaries, actual environment copying and allocation failure,
environment matching, COMSPEC availability/fallback, PATH/extension/batch rules,
DOS/CRT error distinctions, child status and errors, invalid EXEC modes, and
stack/DS restoration when the modeled DOS call deliberately clobbers SS/SP/DS.
The433d tests record its UI/vector/mouse/UART service sequence and guard/flag
behavior; they do not emulate a complete screen manager or physical serial port.

The actual DOSBox-X8086 diagnostic executes recovered4B00/4D code and a source-
built CHILD.COM. The child verifies its command tail and explicit
`LABVAR=OWNED` environment, writes owned CHILD.OUT and exits37. The parent checks
return status, saved pair and execution flag, then verifies missing ABSENT.COM
returnsffff/CRT errno2/raw DOS error2 safely. No original or synthetic analysis
executable is launched; only the source-built diagnostic and owned child run.
