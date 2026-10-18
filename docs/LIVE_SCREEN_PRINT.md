# Live CSI screen printing

The maintained terminal supports CSI media-copy `i` through the ordinary UART
parser. These CSI sequences are bytes received from the remote terminal
connection, not DOS commands to type at a prompt or local hotkeys. A separate
local screen-print key binding has not been verified. No parameter or parameter
0 prints the selected screen, adding a final
formfeed when mode18 is set. Parameter1 prints the current row without a final
formfeed. Multiple parameters are applied in order. Mode19 set selects the full
25-row view; mode19 reset selects the inclusive scrolling margins established
by CSI `r`. Mode18 reset disables the selection's final formfeed.

Screen printing emits all 80 character bytes of each selected row, including
trailing blanks, then CR/LF. Attributes are excluded. This differs from Alt-G
screen snapshots, which trim trailing blanks. The live geometry is fixed to
supported 80-column mode3/page0; original/native diagnostic contracts are
separate in [PRINT_SCREEN_NATIVE.md](PRINT_SCREEN_NATIVE.md).

CSI `?5i` enables processed-text printer copy and CSI `?4i` disables it. An
unprefixed parameter5 remains an explicit unsupported original D0D0 controller
service. This does not introduce a local Alt-P binding.

The maintained path freezes character bytes before device output, uses the
checked printer owner and services UART/flow while output progresses. An
existing printer-copy owner remains active across screen printing; a temporary
owner is closed before completion. Unlike the original native writer, it does
not replace a live FILE pointer or emit formfeed through a closed pointer.

## Independent DOS verification

`standalone/test_terminal_screen_print_dos.py` prepares deterministic ANSI rows,
colors, a full 80-column row, leading/interior/trailing spaces and CP437 text.
Its expected print bytes are generated from those independent row fixtures,
not from product output. It sends actual CSI requests through a TCP UART peer,
checks real CPR/DSR and keyboard responses, samples B800 and BIOS cursor data,
and compares file-only DOSBox-X virtual PRN output exactly. The virtual port
uses `file append:<owned path>` without codepage/newline/formfeed conversion or
physical printer access.

Cases cover default/explicit full-screen selection, current row,
inclusive margins, formfeed off, ordered multiple parameters, existing copy
before/after print, private copy controls, unavailable PRN, active/held capture
and subsequent snapshots. **All 11 actual DOS cases passed**, without failed
attempts, on frozen source-built terminal
`d4cfa4dcb27edd375195ccd9345dd1513844855840f3e673ab9a2ac7288cf16a`.
Each case passed its exact byte oracle, real CPR/DSR and keyboard return, B800/
BIOS cursor checks and UART/PIC/IRQ restoration. Three existing stream-copy
regressions (processed filtering, active shutdown and 512-byte queued output)
also passed on that same executable under `screen-d4cf-regression`.
The active-copy case proved
printable text reached the same owner before and after screen printing;
active/held capture retained its own bytes, and subsequent Alt-G snapshots
matched their independent trimmed-row oracle.

Artifacts remain under `build/terminal-screen-print-dos/initial-d4cf`, including
wire bytes, virtual PRN bytes, exact expected bytes, video/hardware samples,
key schedules and per-case results. The public hash-bound index is
`docs/validation/terminal-screen-print-live.json`; it also retains the separate
linked checker's nine groups / 2,037 inputs for the same executable.

```sh
./tools/dev --command python3 standalone/test_terminal_screen_print_dos.py \
  --sha256 d4cfa4dcb27edd375195ccd9345dd1513844855840f3e673ab9a2ac7288cf16a \
  --label fresh-screen-print
./tools/dev --command python3 standalone/record_printer.py \
  --screen-dos-label initial-d4cf \
  --printer-regression-label screen-d4cf-regression
```

The recorder requires all selected cases and linked checks to match the current
executable, verifies the source manifest, and hashes retained artifacts. Native
printer recording and live stream-copy recording remain separate scopes.

The ordinary UART input dispatcher ignores NUL and has an unresolved SUB
control handler. Those bytes are therefore not injected into the displayed
fixture. Separate native and linked tests execute the actual video reader and
screen-print instructions with literal NUL/SUB/FF screen bytes; the linked
tests model DOS device boundaries. A file-only virtual PRN
also does not establish physical printer readiness, hostile driver call-time
bounds, electrical behavior or complete PCPlus controller support.
