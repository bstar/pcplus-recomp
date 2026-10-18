# Native printer-copy routines

The recovered PCPlus2.01 printer-copy unit preserves **79 original instruction
bytes**: resident36fc..3716 (27bytes) and1a76..1aa9 (52bytes). Flat assembly
matches the recorded original span hashes; OMF assembly replaces addresses
with named integration interfaces. Provenance is in
[reconstruction/printer/provenance.json](../reconstruction/printer/provenance.json).
The baseline EXE SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Neither the ordinary build nor the DOS diagnostic reads that executable.

This unit also exercises the previously recovered132-byte09b6 character logger.
Those132 bytes remain counted with input dispatch, not again as new printer
recovery. The broader original call-path inventory is
[CAPTURE_NATIVE_INVENTORY.md](CAPTURE_NATIVE_INVENTORY.md). The inventory is a
historical evidence ledger; its old live-integration status does not describe
later maintained capture or snapshot work.

## ABI and state

All services are16-bit near calls. C-style arguments are caller-clean words;
DS=SS is required by the small-model diagnostic and reused near-pointer code.

| Export/interface | Contract |
| --- | --- |
| `printer_byte_original(character)` |36fc; caller removes2bytes. Calls putc then flush unconditionally. BX is scratch; BP is restored. AX follows the flush callback and is not a checked putc result. |
| `printer_toggle_original()` |1a76; no arguments. Changes the flag/open or close state, then tail-jumps to status. There is no independent success result. |
| `printer_putc(character,FILE*)` |Original8436 boundary; caller removes4bytes. |
| `printer_flush(FILE*)` |Original8c54 boundary; caller removes2bytes. |
| `printer_open(name,mode)` |Original841a boundary; caller removes4bytes, AX is the FILE pointer. |
| `printer_close(FILE*)` |Original8318 boundary; caller removes2bytes. |
| `printer_status()` |Original2fb8 boundary; final tail-call of both toggle branches. |

The state aliases are `printer_enabled` (originalDS3988), `printer_stream`
(8ff0), `printer_device` (1d50, literal`PRN`) and `printer_binary_mode`
(4688, literal`wb`). The stream is a near CRT FILE pointer, not a DOS handle
number. Capture has separate enabled/hold/FILE state.

The raw keyboard route is Alt-L, BIOSAX2600h (scan26h), to1a76. This
recovery does not itself add that command to the maintained terminal.

The byte wrapper contains no filter or newline translation of its own. It
passes the supplied word to putc with8ff0, then calls flush on8ff0. Direct calls
withFFh or7Fh therefore still reach those services. The filtering described
below belongs to the logger which normally calls this wrapper.

## Processed-character policy

The recovered09b6 logger compares the full input word against00FFh and007Fh;
those two values return before either capture or printer output. This is an
exact word comparison, not a universal filter on every value whose low byte
matches. Ordinary delivered terminal characters are in the byte range.

When printer-copy flag3988 is nonzero, other delivered characters reach36fc.
CR000Dh is always sent to the printer. When CR-adds-LF word1d24 is nonzero,
an additional LF000Ah is sent and flushed separately. LF otherwise remains a
single delivered character. The stream was opened in binary mode, so this
wrapper does not request text-mode LF-to-CRLF conversion.

Printer copy precedes the independent capture branch. Holding capture398c
does not hold printer output. Capture may omit CR or replace it with LF under
its own native policy; that must not be substituted for the printer policy.
This is processed-character forwarding. It does not establish raw UART/ANSI,
file-transfer payload, modem-command or local-program transcript capture.

## Native unchecked outcomes

The exact toggle intentionally preserves several unsafe original behaviors:

- Enabling sets3988 to1 **before** `fopen("PRN","wb")`, stores AX to8ff0 and
  refreshes status. A zero open result leaves the flag enabled and pointer zero.
- Disabling clears3988, calls fclose on the current8ff0, ignores its result and
  leaves the pointer word unchanged. A null/stale pointer is not screened here.
- The byte wrapper flushes even when putc returnsFFFFh. It tests neither putc
  nor flush for failure, and establishes no retry, timeout or availability test.
- The toggle tail-calls status on both branches, including failed open/close.

The fixture can record these null and failure cases safely. It does not execute
a real CRT dereference of a null FILE and cannot establish the downstream
memory damage, DOS/device error or blocking behavior that would follow on a
particular machine. A maintained live printer owner must report open/write/
flush/close failures truthfully rather than reproduce these unchecked states.

The native screen-print helpers12:e2f8/e3ca also use8ff0. They are not part of
this79-byte recovery or its DOS test. Their reuse of the same pointer, row/mode
selection and optional form-feed need separate ownership integration. Script
printer control18:e8be and complete ASPECT grammar also remain separate.

## Verification and boundaries

Build and run with the pinned Nix toolchain:

```sh
./tools/dev --command make test-printer
```

The default target builds and tests from public maintained sources. It needs no
original application, original installation, customized PRM/KEY file or REA
database. The optional analyst comparison explicitly requires the ignored,
SHA-verified local baseline and compares only selected original instructions
under the same declared callback model; it does not launch the original app:

```sh
./tools/dev --command python3 standalone/check_printer.py --original
```

Final validation passed66 linked CPU cases and66 optional original comparisons.
The separate source-built8086 DOS selfcheck also passed, including direct byte
output versus logger filtering, both CR options, null-open state and later null
use, ignored error returns, SP/BP/SI/DI/DS=SS assertions and buffer canaries.
The CPU table additionally checks full-word01FFh/017Fh/010Dh, inactive/held
capture independence, stale pointer after disable and ordered callback traces.
These are66 CPU comparisons, not66 separate DOS/device tests.

The final diagnostic SHA256 is
`2b699e0a2646abdf9b61c50277725d69932a6d29afdd8fb77308aa5d268eec90`.
Actual DOS proof is retained under`build/printer-dos/native-8086-final/` with
`PRINTER PASS`, DOS exit0 and per-artifact hashes. The earlier preliminary
`native-8086-1/` proof remains separate and belongs to its earlier binary.

The DOS runner executes only source-built `build/printer/PRINTER.EXE` using
DOSBox-X's8086 CPU model with all serial ports disabled. Its C driver invokes
actual recovered instructions through a memory-FILE/CRT/status diagnostic
boundary. It redirects the driver's report to an owned regular file, requires
both DOS success and the explicit `PRINTER PASS` report, checks the executable
against its build manifest and verifies that the build directory gains no new
files. Every run keeps a fresh `build/printer-dos/<label>/` folder, including
failures; `build/printer-dos/result.json` points to the latest result.

No physical PRN/LPT device, BIOS printer interrupt, DOS printer-driver timeout,
spooler, cable or printer is exercised. No original application or analysis
executable is launched. The diagnostic does not by itself make printer copy a
live terminal feature or establish complete screen printing.
