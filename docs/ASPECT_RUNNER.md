# DOS script execution and terminal launch

`ASPECT.EXE` now runs compiled scripts as a source-built DOS program. The terminal
has a File → A → Run script action that prompts for a DOS filename, launches
the sibling interpreter and returns through the existing PROGRAM handoff.
Scripts run as a separate DOS process. Live serial scripting and complete
ASPECT/application integration remain unfinished.

The [frozen validation record](validation/aspect-console.json) binds current
sources, native comparisons, compiler/runner results, terminal launch checks
and the package. A fresh [source-only rebuild](validation/application-components-source-build.json)
reproduces 85 outputs byte for byte, including the current terminal and runner,
without original installations, analysis databases or prior build outputs.

## Build and use

```sh
./tools/build package
```

The generated `build/dos-package` directory contains `TERMINAL.EXE`, `ASPECT.EXE`,
`PRMEDIT.EXE`, `XLTEDIT.EXE`, a source-authored `HELLO.ASP` and compiled
`HELLO.ASX`. No original executable or private profile is included. Place these
programs together on the test DOS drive. In DOS:

```text
TERMINAL COM1 38400 8N1 SOFT
```

Open Alt-Z, select File, then A Run script, and enter `HELLO.ASX`. Press a key
after the script finishes to restore the terminal. The menu services incoming
serial traffic while the filename prompt is open. The selected path is limited
to 57 displayable characters and validated DOS 8.3 components. The child is
resolved beside the running terminal; no COMSPEC/PATH fallback selects another
interpreter.

The interpreter can also run directly:

```text
ASPECT HELLO.ASX
ASPECT HELLO.ASX 20000
```

The optional instruction budget is 1..65535, default 10000. Escape requests
cancellation. Error exits report the opcode, step and original native error
number where available. A nonzero child exit produces the parent PROGRAM
failure notice. The DOS runner rejects device leaf names and malformed command
arguments; the native instruction handlers still retain unchecked operand,
frame and pointer behavior. Use trusted scripts compiled from local source.

Compile source on the host through Nix:

```sh
./tools/dev --command python3 src/aspect/compiler.py HELLO.ASP -o HELLO.ASX
```

## Runtime extension

EXIT (33), MESSAGE (76) and PAUSE (88) now execute recovered instructions.
The new console module contains 296 exact bytes for these commands, caret
decoding, print loops, bounded pause operands and the BIOS timer delay.
Its component diagnostic passes 459 CPU scenarios, 9,384 actual DOS assertions
and all 145 instruction addresses. Optional comparison checks all 44 linked
component ranges against the original.

MESSAGE defaults to CRLF, as established by the original overlay2 D6EA reset
storing 1 at DS:E38A. It retains the native caret transform: `^M` is CR, `^J`
is LF, `^@` is FF, `^^` is 1E and `^^^` is a literal caret. A trailing caret
retains native unchecked behavior. The native output primitive is a complex
terminal renderer; this standalone owner's explicit backend writes raw bytes
to DOS stdout, including redirected files. It does not claim original renderer
equivalence.

PAUSE uses the exact BIOS-clock helper. A requested second waits 19 timer
transitions, and Escape is polled between waits. The native helper enables
interrupts and clobbers ES; its callers preserve their documented ABI. Pause
operands must be 0..32767 at runtime. Negative source literals compile but
produce native range error1, mapped to maintained operand error7.

RSTRCMP already had native runtime support. New compiler probes establish its
two-string/optional-count grammar and test raw unsigned-byte comparisons.
An omitted count compares 80 bytes, including padding beyond NUL; it is not
ordinary strcmp. TRANSMIT and WAITFOR emission is established, but their
runtime services still fail explicitly as unsupported.

## Verification and remaining scope

The maintained compiler matches 270 frozen accepted outputs and 270 renamed/
reformatted variants. The console corpus records 55 original compiler attempts:
33 accepted, 22 rejected. Three long pauses are compiler-only; 30 new vectors
execute in the DOS diagnostic. The historical PAUSE7 fixture now expects success
instead of its earlier unsupported-command stop. Its authored source/ASX bytes
remain unchanged.

The composed suite passes 437 actual DOS cases and 6,996 assertions over
267 source-compiled fixtures. Fifty-seven of 215 opcode slots are wired;
158 still abort. Consolidated diagnostic helpers avoid the 64 KiB code overflow
caused by repeating value/output checks at every fixture. The recovered code
and observed expectations remain unchanged by that diagnostic refactor.

Production CLI tests spawn the real interpreter 16 times, verifying exact
stdout/stderr, exit codes, missing/bad inputs, instruction budget, Escape,
native delay and restored INT0 vectors. Four independent terminal DOS cases
cover script output, unsupported bytecode, missing helper and prompt cancellation,
then verify ordinary typing, terminal replies, screen, UART and configuration
restoration. Linked launch checks cover 30 inputs; menu and far-ABI regressions
also pass. The terminal uses 65,344 near data/stack bytes, leaving 192 bytes.

The parent preserves DTR and uses its established flow/IRQ handoff during the
child. It does not service normal terminal receive traffic while the DOS child
runs. Flow NONE cannot guarantee preservation of incoming data during that
interval. Script-driven UART/UI scheduling, other command families, floats,
recorder, full compiler compatibility, Host mode and physical modem validation
remain required. All F01–F16 whole-application gates remain open.
