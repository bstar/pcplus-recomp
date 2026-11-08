# Experimental ASPECT standard overlays

The expanded GET/Help/notice overlay build passes the previously failing
six-file/graphics PROGRAM workload, source compiler lending and GET recovery.
It remains ineligible for packaging: full-parent Help still refuses memory.
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

## Initial GET/Help checkpoint

The earlier GET/Help-only experimental ASPECT SHA256 was:
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

## Expanded notice overlay: PROGRAM capacity passes

The optional `--notice` relink also shares the6466-byte notice bank with GET
and Help. Its three mutable recovery words move to resident DGROUP with
SS-relative access and an entry stack check. A Help call must not erase its
caller's notice recovery frame when loading another bank. The root allocator,
mouse callback, UART, active PROGRAM controller and their return paths remain
resident. Normal non-overlay output remains byte-identical.

Expanded experimental ASPECT SHA256:
`59dba04d2fbde87a92bc5755384aed07103227d7ff9dacdaf04e58d4df65db2e`.
Exact minimum including PSP126432 bytes, page minimum126576, DGROUP40448 and
stack8192. This saves8608 minimum bytes relative to the disk-snapshot control,
including6384 beyond the GET/Help-only overlay. No stack, file-slot or512-byte
buffer capacity was reduced.

A passive386/UMB diagnostic of the earlier failure records process status4,
CRT errno12 and DOS error8 with no child started. The subsequent error notice
returns status7 (notice failure), causing outer runtime-state error10. This
establishes process memory pressure beneath that error; stream masking and
teardown completed and their owners retired. Diagnostic memory footprints are
separate from the unobserved8086 acceptance run.

The expanded build passes:

- The original unobserved8086 workload: six held files, all six ordinary file
  slots, three actual graphics children, actual WAIT Space, exact restored
  viewport cells, VT220/ANSI switching, missing-file recovery and four script
  calls within one parent. All30 final checks pass. The generic harness's
  intermediate banner check is replaced by explicit pre-reset CPR and exact
  post-reset viewport checks because EMULATE deliberately clears that banner.
- Six standalone8086 bootstrap launches and30 checks with exact output.
- Two full-parent386/UMB source compiler loans (startup and EXECUTE), exact
  compiled ASX, GET editing and continued writes through an owned open stream.
- Two full-parent386/UMB framed WHEN divide and confirmed cancellation cases.
- Independent cold source rebuild of1048 files with no originals, old objects
  or ancestor Git; exact parent, child, compiler and helper artifacts, plus
  exact replay of both source-lending cases.

The source test now requires the allocation/EXEC observer for lease acceptance.
Its stream expectation distinguishes a refusal's flushed prefix from the
successful stream's prefix plus edited GET value; it does not discard the
contents check. Early unobserved attempts and that stale expectation remain in
ignored receipts and do not count as accepted tests.

The [expanded validation record](validation/aspect-notice-overlays.json) binds
these receipts, including the failed Help run.

Full-parent Help still fails while acquiring saved mouse state: notice input
cause11, service4 (`MOUSE_MEMORY`), before Help opens. This is retained as a
failed integration receipt. Consequently actual Notice→Help bank eviction and
notice recovery are not accepted merely because their state is now resident.
Broader GET lifetime/WHEN tests, nonlocal recovery across real bank eviction,
overlay handle inheritance/failure paths, remaining Help memory pressure and
BBS/package regression gates remain open. Physical Boca/SPA2102/SynthModem/
Enigma acceptance is separate. Host remains last; no package is promoted.
