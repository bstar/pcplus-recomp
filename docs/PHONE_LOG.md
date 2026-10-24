# Native telephone-call logging

`PCPLUS.FON` is the telephone-call log, not a font resource. The prior feature
inventory grouped it with fonts based on its extension; that inference was
wrong. The original startup data names it at DS3320/file28C70. Overlay4's
E2A9 controller resolves and opens that filename in `at` mode and prints
name/number/date/online/offline/elapsed columns. The installed144365-byte file
is all ASCII, has no NUL bytes and1794 CRLFs, consistent with this code path.
No private names, numbers or historical call records are published here.
Actual native font selection/loading remains a separate unresolved question.

The recovered [controller](../reconstruction/phone_log/controller.asm) is258
exact original bytes, E2A9..E3AA inclusive. The
[provenance](../reconstruction/phone_log/provenance.json) binds the original
2.01 digest, overlay file offset, state/service mappings and REA dossier
`ev_8fbdeb2c8c59e1604bf53207279cda86462bc7e81ef53e858cf6bb35fb013b96`.
Ghidra assembly establishes a near callee-cleaned WORD argument (`RET2`),
DS=SS, and BP/DI preservation. Pseudocode is supporting static evidence, not
original source. The synthetic overlay image is static-only and never executed;
its injected entry caller is excluded from application call-path conclusions.

## Observed native policy

Argument0 starts a record; every nonzero WORD finishes it. Start-clock or
stop/elapsed calculation runs first, even if logging is disabled. Disabled
DS1D6A clears pending DS333A and performs no file logging.

A start always attempts an append. A finish appends only if pending is nonzero
and the resolved file is readable. A new/unreadable file gets a heading on
start. The controller calls the separate file-preparation provider, opens text
append and writes the name (maximum22 characters), number (minimum20 columns),
date and24-hour time. Finish appends offline time and elapsed text. It sets
pending to1 after start and0 after finish, then closes the FILE. There is no
trailing newline until the next heading/record starts.

Open failure formats a local notice and leaves pending unchanged. Missing-file
finish also leaves a previously set pending flag unchanged. The controller
does **not** check formatted-write or close results and updates pending before
close. Those are observed native limitations, not reliable persistence policy.
Repeated starts can also append a new incomplete record without finishing the
previous one; production lifecycle ownership must decide which transitions
generate each event.

The inspected directory callers at E182/E20A invoke argument0 after successful
dialing paths; this is distinct from the date/count patch in
[directory accounting](DIRECTORY_ACCOUNTING.md). The descriptor's thunk and
other resolved calls are retained in the REA dossier. A complete terminal
hangup/carrier/exit scheduler binding is not yet reconstructed here.

## Verification and rebuild

The [sealed receipt](validation/phone-log.json) binds258 native bytes,384 actual
16-bit policy/ABI inputs,33 actual8086 DOS checks and an exact executable
rebuild from seven declared source files. CPU cases cover enabled/disabled,
all zero/nonzero operation meanings, pending states, readable/missing file,
open failure and ignored write/close failure returns. They model external
services explicitly and validate the variadic argument ordering, BX notice
convention and RET2 stack balance.

The DOS diagnostic links the recovered OMF controller to actual CRT FILE
operations and explicit synthetic clock/date/direct-path callbacks. It checks
new-file headings, two append cycles, byte-exact CRLF records, duplicate stop,
missing-file pending behavior, disabled calls, real DOS open failure, all20 JFT
entries and an independent42-byte UART/PIC/vector snapshot. No original
executable, install file or REA database is an ordinary build input. The first
DOS fixture omitted the sampler's fixed D: mount; that failed snapshot attempt
is retained locally and excluded. The corrected fresh `phone-log-dos-02` passes.

```sh
./tools/build test-phone-log
./tools/build test-phone-log-source
# Optional explicit original-byte comparison:
./tools/build test-phone-log-compat
```

The output is `build/phone-log/PHONELOG.EXE`, a component diagnostic. It is not
the terminal application or a replacement PCPlus executable. The blank-tree
proof is `build/phone-log-source-01`; the independent recorder is
`standalone/record_phone_log.py`.

## Work still required

Bind clock/date/elapsed, PCPLUS path resolution, error notices and saved setting
import to actual application services. Recover the setting's PRM mapping rather
than assuming a DS offset is a file offset. Add checked append/flush/close and
partial-write recovery, with an explicit deviation from native unchecked
failure behavior. Queue connection events at DOS-safe foreground points while
preserving UART service; cover selected/unselected DIRECT and MODEM calls,
redial, cancellation, carrier loss, explicit hangup and final exit without
duplicate records. Include year2000-safe dates, midnight/elapsed behavior and
synthetic-contact privacy checks. Current near-code space also requires a
reviewed placement/banking choice before production integration.

This component checkpoint leaves the terminal, interpreter and compiler
binaries unchanged. F07/F10, native fonts, broader F01–F16, physical modem and
card deployment requirements remain open.
