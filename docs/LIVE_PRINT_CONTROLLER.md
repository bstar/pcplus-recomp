# Live dedicated-print controller

Unprefixed CSI5i enters the maintained dedicated-print owner. CSI sequences here
are bytes received from a remote connection, not DOS commands or local key
bindings. Private CSI?5i retains ordinary processed-text printer-copy behavior.

While dedicated printing owns receive processing, bytes go to the checked PRN
owner instead of ANSI rendering or processed-text capture. NUL and DEL are
omitted. Other bytes, including FF, SUB, CR/LF and DC4, remain literal. DC4 is
emitted once; the native controller's accidental double print is not retained.
Profile31's DC4 exit behavior is a separate profile-specific policy; the
actual DOS cases below use the ANSI profile and do not validate profile31.

The ANSI-family termination grammar retains the native digit flags: ESC[4i
stops, as do ESC[14i and ESC[4;5i, because any digit4 plus a bracket and final i
qualifies. ESC[0i and ESC[5i are suppressed. Unknown sequences replay literally.
The maintained escape-prefix buffer is bounded to 32 bytes and replays on
36 full BIOS ticks measured from the first byte, preventing an indefinite wait.
No final formfeed or DC4 is fabricated on close.

Output drains before normal receiving resumes. A temporary printer owner is
closed and checked; an existing healthy Alt-L copy owner is borrowed and kept
usable afterwards. Existing active or held text capture remains independent
and receives no raw controller bytes. Ordinary keys/network bindings still
transmit. Two keyboard Escapes exit: the first is transmitted, the second is
consumed locally. Alt-X/hang-up stop the controller before their ordinary
cleanup. Nested capture/snapshot/macro/PROGRAM/transfer owners are denied.

The frozen build also passes all35 commands from the terminal regression
target and23 linked YMODEM inputs. A fresh source-only checkout reproduces
all57 component outputs byte for byte. See
[terminal regression evidence](validation/terminal-controller-regression.json)
and [source rebuild evidence](validation/terminal-source-build.json).

## Independent actual DOS harness

`standalone/test_terminal_print_controller_dos.py` uses fresh ignored synthetic
media, an explicit immutable source-built runtime hash, actual BIOS keys and a
TCP UART peer. DOSBox-X's file-only virtual parallel port receives real DOS PRN
calls; no physical printer, fake terminal replies or replaced product callbacks
are involved. Independent expected bytes cover all256 values, filtering,
fragmented terminators, native digit4 grammar, suppression/unknown replay,
prefix overflow, first-byte timeout, copy/capture coexistence, unavailable PRN,
double Escape, Alt-X and nested-owner denial.

The peer lays out known ANSI rows before entry, supplies no queries while raw
printing owns input, and checks actual cursor/status replies afterwards. It
compares virtual PRN bytes exactly, validates active/held capture contents,
samples B800 and BIOS cursor/geometry, and compares UART/PIC/IRQ before/after.
**All 14 actual DOS cases passed**, with no failed live attempts, on frozen
source-built terminal
`51b94da6b6c8f489fa646a220e7d7a77457459f96e73bec98687b19a1f338c90`.
Exact output includes all 254 retained values from the all256 fixture, one
literal DC4, unknown escape replay and no terminating-sequence bytes. The
keyboard case verifies exactly one Escape forwarded before normal CPR/DSR
resumes; Alt-X observes actual serial closure. Active/held capture and the
borrowed copy owner remain usable, and sampled video/cursor/UART/PIC/IRQ
state checks pass.

Current artifacts are retained under
`build/terminal-print-controller-dos/carrier-51b9`. The earlier fourteen passing
cases on560bb5b9 remain under `initial-560b` and are included as history, not
attributed to the current executable. The report selects fourteen current
passes from28 retained actual DOS runs; neither batch had a live failure.
The hash-bound public index is `docs/validation/terminal-print-controller-live.json`,
including the independent linked checker's eleven groups / 300 inputs. It keeps
these evidence scopes separate: the actual DOS timeout case waits2.3seconds
and verifies literal prefix replay; linked tests verify the exact36-full-tick
first-byte deadline and wrap behavior. The linked development history retains
a real earlier bug where BIOS011Bh Escape was consumed rather than forwarded;
that was corrected before these actual DOS freezes. A later real carrier-entry
race was also fixed before51b9: when the connection engine observes an existing
carrier disappear and transitions online6 to idle0 after admission, before its
first controller poll, the controller must not consume queued receive bytes. The linked regression
uses the real connection poll, preserves all eight pending bytes and closes
once. It separately confirms that an idle/direct connection which has never
observed carrier remains usable; a low DCD bit alone is not treated as a loss.
The passive-COM DOS suite above does not simulate that connection-engine race.

```sh
./tools/dev --command python3 standalone/test_terminal_print_controller_dos.py \
  --sha256 51b94da6b6c8f489fa646a220e7d7a77457459f96e73bec98687b19a1f338c90 \
  --label fresh-controller-proof
./tools/dev --command python3 standalone/record_printer.py \
  --controller-dos-label initial-560b --controller-dos-label carrier-51b9
```

The recorder requires selected live cases, linked checks, current executable
and source manifest to agree, and hashes all retained case artifacts.

This does not prove physical printer timing, arbitrary driver-call time bounds,
profile-complete original controller behavior or complete PCPlus parity. The
native Alt-B break helper is documented in [BREAK_NATIVE.md](BREAK_NATIVE.md),
but its duration conversion and maintained live implementation remain unproved;
ordinary key forwarding does not establish serial break support. Native
source/ABI diagnostics and linked fault/time tests are separate evidence; see
[PRINT_CONTROLLER_NATIVE.md](PRINT_CONTROLLER_NATIVE.md).
