# Cancellation before first CONNECT: controlled DCD lab

The [independent old/new lab audit](validation/manual-cancel-lab.json) now
checks Escape cancellation under XOFF before the first CONNECT, then Alt-D retry,
on actual 8086 DOS programs. SOFT and BOTH pass with parent1600a5b3: the first
attempt's DCD and carrier-history samples stay zero, its pause retires at idle,
and the retry reaches CONNECT, manual typing and an ANSI query. The older
parenta31eb517 remains paused and transmits no retry initialization.

This uses an explicitly patched UART test backend. It is not stock-emulator or
physical-modem acceptance, and the receipt marks both scopes false. No PCPlus
product source change was needed beyond the existing MODEM completion fix.

## Backend and provenance

The pinned stock
[DOSBox-X nullmodem source](https://github.com/joncampbell123/dosbox-x/blob/dosbox-x-v2026.07.02/src/hardware/serialport/nullmodem.cpp)
uses ordinary FF control flags for CTS, DSR and BREAK; TCP attachment controls
DCD separately. Those existing flags cannot hold DCD low on an attached test
transport. The initial plan to use the DSR flag for DCD was rejected by source
inspection before any acceptance claim.

The separate Nix lab package adds one opt-in line-control operation:
bit7 enables DCD control from bit3. Ordinary unmarked FF frames retain their
existing behavior. The owned peer sends FF81 for CTS high/DCD low, then FF8B
for CTS/DSR/DCD high only when the retry dial completes. PCPlus reads the actual
emulated MSR and executes its normal IRQ/controller code. No product memory,
handler result or CPU instruction is substituted.

The package inherits DOSBox-X2026.07.02 from the repository's locked Nixpkgs
revision. It lives behind an ignored build link and does not replace the normal
DOSBox-X package or install anything globally. Build/current-test commands:

~~~sh
./tools/build-dcd-lab > build/dosbox-dcd-lab-build.json
./tools/dev --command python3 standalone/test_manual_cancel_dos.py --label cancel-check
~~~

The auditor binds the actual Nix derivation's output and patch bytes, the
wrapper/wrapped binary hashes, recipe, lock and test captures. The Nix store
output stays rooted by the build link; raw DOS products and evidence are frozen
in the accepted local cohort. Original PCPlus binaries are not inputs.

## Observations and controls

The owned peer sends XOFF after the first initialization byte, never sends XON,
and observes the actual DTR fall/restore control frames. It discards its partial
command buffer when DTR falls. That is an explicit fixture modem policy;
retained partial-command behavior and cancellation recovery on the Boca remain
separate tests. This lab does not establish that every modem clears its command
parser on DTR. A read-only guest TSR
records parent state and MSR samples after the owned PRM open establishes the
parent DS. Before first cancellation completes, both DCD-high and carrier-seen
counters are zero. It observes29 paused initialization ticks and18 DTR-low ticks
in each accepted case. Old idle pause is1; corrected idle pause is0. The corrected
cases then spend139 sampled ticks online, with exact init/dial/ANSI/manual/
hangup bytes and one native directory accounting update.

Independent vector probes before installation and after collection verify INT21
and INT1C restoration; the ordinary42-byte hardware snapshot also matches.
The audit independently decodes transport status frames to recover UART bytes.
[Six corrupted-evidence controls](validation/manual-cancel-audit-guards.json)
are rejected despite green producer flags and updated hashes: false first DCD,
retained pause, wrong vector, lost init byte, stock-backend mislabel and forged
patch provenance.

Accepted raw pairs are manual-cancel-dos/baseline-03 and fixed-03. The first
corrected fixture retained CR in its peer command comparison and rejected valid
ATZ; that failed attempt remains preserved. The second pair corrects that peer
parser; the third adds the independent observer-vector restoration check.
These fixture changes do not alter PCPlus behavior.

The normal backend separately passes current-parent stock Synchronet/ENiGMA
recorder/window workflows. DTR-disabled or ineffective hangup, other DCD timing,
sustained RTS/RX, physical Boca/SPA2102 integration and every full F01–F16
requirement remain open. This lab provides no V.8 or 14.4-kbps negotiation result;
see ANALOG_MODEM_INTEGRATION.md and BOCA_COMMISSIONING.md for that target.
