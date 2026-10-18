# Live printer copy

Alt-L toggles the maintained processed-text PRN sink. It uses the recovered
09B6h logger's filtering alongside continuous text capture, with a separate
checked DOS device owner. This is printer copy of processed characters;
ANSI protocol bytes and raw-monitor bytes are excluded. The logger omits FF
and DEL. Printer CR and LF remain their literal bytes; enabling CR-adds-LF
inserts an additional LF after each CR. The capture sink retains its own
CR/LF policy independently.

The source-owned frontend uses a 128-byte queue, reserves room for the two
bytes a CR may produce, and writes at most 16 queued bytes per foreground poll.
It stops receiving more processed input when there is insufficient queue space.
An 18-BIOS-tick no-progress timeout and a separate 36-tick shutdown drain bound
prevent application-level polling from continuing indefinitely. These timers
cannot interrupt a DOS driver that blocks inside an individual device call.

Device admission opens `PRN`, verifies the character-device identity,
preserves its information word, selects binary mode when necessary, checks
INT21h/4407h readiness and submits bounded writes. Close restores the original
mode before closing. Open denial before acquiring a handle is a nonfatal UI
denial; acquired-owner errors disable printer copy and latch exit status 12.
Potentially partial writes and uncertain closes are not blindly retried.
Native unchecked FILE outcomes are documented separately
in [PRINTER_NATIVE.md](PRINTER_NATIVE.md); they are not the maintained error
policy.

## Independent DOS device probe

`standalone/test_terminal_printer_dos.py --probe --label fresh-probe` builds
an owned synthetic DOS COM program. Its actual DOS calls open PRN, query/set
binary mode, query readiness, write all 256 byte values and restore/close.
DOSBox-X `parallel1=file append:<owned capture path>` delivered exactly the
256 bytes, including NUL, SUB, FF and DEL. A second run with `parallel1=disabled`
returned DOS open error2 and produced no output. A separately source-built
BIOS key fixture verified `ADDKEY a-l` returns AX2600h. Results are retained under
`build/terminal-printer-dos/parallel-key-probe-3`.

The file-only virtual parallel configuration follows the official
[DOSBox-X printing guide](https://dosbox-x.com/wiki/Guide:Setting-up-printing-in-DOSBox%E2%80%90X).
No `reallpt`, physical device or external print program is configured. Extra
`addLF`, `addFF` and codepage conversion options are omitted, so they cannot
normalize the independent byte oracle.

## Live verification scope

The independent harness uses an explicit immutable source-built terminal hash,
fresh ignored synthetic DOS media, real BIOS Alt-L input and a real TCP UART
peer. It preserves incoming/outgoing bytes, actual protocol replies, virtual
printer bytes and before/after UART/PIC/IRQ samples. It tests ordinary close,
active shutdown, CR-adds-LF, reopening, finite queued output, active/held text
capture, monitor bypass and unavailable PRN. **All nine actual DOS cases passed**
on frozen terminal
`f2c75bf79f0aa88fe8411eb82da3866a18ac44410de0e40492d0f7ec6d0e4328`.
Each passed the exact independent printer-byte oracle, actual serial parser/
keyboard or shutdown check, and UART/PIC/IRQ restoration. There were no failed
live cases. Results are retained under
`build/terminal-printer-dos/initial-f2c7`; hashes and the linked/device evidence
are collected in `docs/validation/terminal-printer-live.json`.

```sh
./tools/dev --command python3 standalone/test_terminal_printer_dos.py \
  --sha256 f2c75bf79f0aa88fe8411eb82da3866a18ac44410de0e40492d0f7ec6d0e4328 \
  --label fresh-printer-proof
./tools/dev --command python3 standalone/record_printer.py \
  --dos-label initial-f2c7
```

The recorder requires the current executable, linked checker and all selected
live cases to share the frozen runtime hash. It separately verifies backend
and native diagnostic executable/source identities, retains per-case artifact
hashes, and requires the source-built positive/negative device probe. The
native recorder still works without `--dos-label`; it does not then claim live
evidence. PROGRAM and transfer barriers, overflow, driver faults and exact
BIOS tick/midnight bounds are covered by separate linked tests, rather than
being attributed to the nine live DOS cases.

NUL is ignored by the ordinary input dispatcher. SUB's ordinary control handler
1248h is currently an explicit unimplemented boundary, so the live text fixture
does not send it into the ANSI parser. The independent DOS device probe covers
binary SUB at the PRN boundary; raw-monitor bypass covers all 256 bytes without
claiming processed SUB support.

A virtual ready file device does not establish physical printer operation,
parallel cable/electrical timing, permanently-busy device recovery or truthful
readiness from a hostile driver. Filesystem/device fault diagnostics and linked
queue/timeouts provide separate evidence; complete PCPlus parity is not claimed.
