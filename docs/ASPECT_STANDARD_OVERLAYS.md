# Experimental ASPECT standard overlays

The optional GET/Help overlay build now starts and passes a full-parent GET
editing test plus two GET divide/cancellation recovery cases. It remains
ineligible for packaging: the six-file/graphics PROGRAM workload still fails.
No installed package, selector, private configuration or call history changes.

This is maintained memory-layout work, not recovered vendor overlay code.
It follows the [disk snapshot experiment](DISK_SNAPSHOT_EXPERIMENT.md).
The [validation record](validation/aspect-standard-overlays.json) binds the
exact experimental binary and its passing and failing receipts.

## Layout and lifetime rules

`overlay_ready=True` in the process builder prepares separate GET root and bank
adapters and a separate Help code bank. It does not itself enable disk overlays.
`standalone/build_aspect_standard_overlay.py` relinks that prepared build with
Watcom's standard far overlay manager, sharing a code area between GET and Help.
All input objects are source-built; original executable inputs remain absent.

GET's six mutable checkpoint words move from replaceable CS into resident
DGROUP, using SS-relative access so an owned-stack native fault with foreign DS
can recover. Entry checks require the resident data stack. This is not a claim
of safe handling of arbitrary foreign SS. Keyboard, mouse callbacks, UART,
process and ordinary runtime code remain resident. Help's near allocator calls
use explicit far adapters to the resident allocation owner.

The overlay file has a root MZ image and a separate trailer. The experimental
builder measures and hashes both without applying ordinary no-trailer header
padding. It checks root manager/table/vector bounds and shared CS, resident
checkpoint bounds, far editor storage before DGROUP, `_NULL` first in DGROUP,
BSS before the final unchanged8192-byte stack, and a206-byte editor state.
These are checks of trusted linker output, not a general overlay-file parser.

## Two startup failures diagnosed

The first application layout exited255 before C main. A separate DOS CRT-spawn
witness captured stderr as `incompatible overlay manager` from both C: and D:.
The manual class order placed tables/vectors after a different resident bank,
outside the manager's CS. Putting the manager last fixed that first failure.

That intermediate build passed CLI help/usage but a simple script returned
runtime-state error10 at opcode00/step0. Its preloaded data section had `_NULL`
after the stack and far editor storage mixed into DGROUP's range. Removing the
manual ORDER lets overlay-aware DOSSEG order both code and preloaded data.
The final build passes help, invalid arguments and an actual simple script with
exact redirected stdout/stderr, expected exit status and preserved INT0 vector,
from both drives. These are standalone bootstrap checks, not ASIO acceptance.

The upstream loader's version check and DOSSEG rules are documented in
[Open Watcom loader source](https://github.com/open-watcom/open-watcom-v2/blob/master/bld/wl/ovlldr/c/ovlldr.c)
and the [Linker Guide](https://open-watcom.github.io/open-watcom-v2-wikidocs/lguide.html).

## Current evidence and remaining gates

Final experimental ASPECT SHA256:
`b57eeb6b9f731a3c261de5ef50b186e88d7721323f71d8cb8931e591d7b34da9`.
Near code64340, GET4079, editor1544, Help6529, DGROUP40448, stack8192;
exact MZ minimum including PSP132816 bytes (page minimum133088).
The disk-snapshot control is byte-identical to its previous135040-byte minimum
build, giving2224 bytes of measured minimum-allocation saving. This does not
measure free runtime heap or prove nested-child capacity.

- Actual8086 standalone bootstrap: six launches,30 checks, exact outputs.
- Full parent386/UMB: GET editing with a retained open stream passes; framed WHEN
  divide and confirmed cancellation also pass with normal parent return.
- A separate8086 near64K-root probe passes600 callbacks, including reentry into
  sibling B before returning to A. This is a narrow ABI prerequisite.
- Heavy unobserved8086 workload reaches all six held files (`ACK6`) but returns
  runtime-state error10 at PROGRAM opcode9B/step20. It fails the required three
  graphics children, viewport, stream and same-process recovery acceptance.
  The origin of that state refusal is still unresolved; do not call it a proven
  memory failure or successful PROGRAM integration.

Full-parent Help, broader GET lifetime/WHEN tests, source compiler lending,
overlay handle ownership during nested EXEC, nonlocal recovery across actual
GET/Help eviction, independent cold rebuild, and the heavy workload remain
open. BBS/package regressions and physical Boca/SPA2102/SynthModem/Enigma
acceptance follow those gates. Host remains last in the full parity plan.
