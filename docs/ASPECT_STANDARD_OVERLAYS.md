# Experimental ASPECT standard overlays

The expanded GET/Help/notice overlay build passes the previously failing
six-file/graphics PROGRAM workload, source compiler lending and GET recovery.
It remains ineligible for packaging: full-parent Help still fails during admission/service.
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

The earlier full-parent Help receipt reports notice input cause11, service4
(`MOUSE_MEMORY`), before a captured Help frame. That mapped code also covers
Help model and screen allocation failures; it did not establish a saved-mouse-
state failure. This is retained as a failed integration receipt. Consequently
actual Notice→Help bank eviction and
notice recovery are not accepted merely because their state is now resident.
Broader GET lifetime/WHEN tests, nonlocal recovery across real bank eviction,
overlay handle inheritance/failure paths, remaining Help memory pressure and
BBS/package regression gates remain open. Physical Boca/SPA2102/SynthModem/
Enigma acceptance is separate. Host remains last; no package is promoted.

## Help admission follow-up: allocations pass, service gate remains open

The later [Help-admission record](validation/aspect-help-admission.json) narrows
the earlier cause11/service4 failure. Service4 is a mapped `MOUSE_MEMORY` value,
also returned for Help model or saved-screen allocation refusal. The mouse
callback was already active and the notice was visible. It was incorrect to
identify the earlier receipt as failure to allocate saved mouse state.

An optional passive INT21 observer records requests after Help-key admission,
their actual carry/AX/BX results, PSP, DS, caller and near-heap boundary. In the
original notice-overlay child, the model allocation requests AH4A/BX8142,
but DOS returns error8 and largest extent7933 paragraphs, with curbrk40960 and
nheapbeg40448. This is a contiguous PSP growth refusal; no Help screen request
has occurred. Separate DOS allocations pin the near heap's ceiling.

`early_help_model=True` reserves the unchanged model before notice input takes
its separate mouse/window DOS blocks. A failed reservation still permits the
error notice, and its later Help request reports failure explicitly. Failed
mouse admission releases an unused reservation; a retained mouse owner retains
its backing until normal close/recovery. Missing-file fallback releases the
model before using authored static pages. Existing view/model release guards
still retain backing until both file and borrowed view have retired.

This resolves model admission: curbrk reaches44298. The next observed refusal is
then the actual4032-byte saved screen (AH48/BX252, largest free165 paragraphs).
The experimental `--program` relink also shares the synchronous PROGRAM
controller's1463 code bytes. Its mutable state already resides in DGROUP;
platform, keyboard/UART interrupt code and native external checkpoint remain
resident. This releases another1392 minimum bytes. All stack and buffer
capacities remain intact.

The resulting production-layout prototype is
`822897f0b67dfbfbe98bed8711cb1071417705ad9a75fdcd5138c88679fc7c05`,
minimum125120/page125200, DGROUP40464, stack8192:9920 minimum bytes below the
disk-snapshot control. Its saved-screen request succeeds. The same unobserved
8086 six-file/three-graphics/WAIT workload remains green. The reservation
component passes91 DOS checks, including admission failure, idempotence,
active-owner refusal, exact screen/JFT restoration, release retry and repeated
resource search/lifetimes. Disabled production bytes remain exactly the prior
disk-snapshot control.
Two full-parent source compiler loan/GET/open-stream cases and six standalone
bootstrap launches also pass. A clean1048-file export reproduces the exact
parent/child/compiler/helpers and replays both compiler cases. These passing
checks do not override the failed Help integration.

Full Help is still rejected. The diagnostic `program_result_probe` profile now
records the notice service failure's source and execution context. With BIOS
input fallback, after successful4032-byte screen allocation, speaker polling
returns STATE4 with DS=SS37608, FLAGS7006h (IF clear), and UART status0. This is
NOTICE_SERVICE6, subsequently presented by the existing PROGRAM adapter as
serial error14/status4. It does not establish a UART failure. The first point
where IF becomes clear, and the associated unsupported INT10 calls in the
emulator log, remain unresolved. The diagnosis uses a larger marked diagnostic
child and BIOS fallback, not mouse-enabled capacity acceptance.

Do not fix this by unconditionally enabling interrupts or weakening the
speaker/context guards. Trace the first bad transition through Help paint,
bank return and notice service. No actual captured Help page, paused timer,
search/F3 sequence or exact notice restoration is accepted yet. Packaging,
BBS/physical tests and full feature parity remain open.
