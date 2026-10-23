# Composed PROGRAM controller

The [native notice-input component](NOTICE_INPUT.md) now accepts66 actual DOS
checks with guarded non-consuming mouse/BIOS input and retained driver ownership.
Fresh REA corrects the direct dependency: mouse/BIOS plus the contextual Alt-Z
display hook, with KEY macro dispatch separate. Attached ASPECT input, original
shared UI and full PROGRAM/application acceptance remain open.

The source-built `PROGRAM.EXE` diagnostic now combines real recovered DOS
namespace/EXEC, far-backed screen snapshots, PROGRAM display services and the
gated external UART owner. This is an application-integration component;
ASPECT DOS/RUN/SHELL remain unpublished and no whole-application gate closes.

The [validation ledger](validation/native-program.json) binds eight actual
8086 DOS cases, COM1/COM2 crossed with N/S/H/B flow, to 381,336 assertions.
Each case runs multiple real children. Most assertions compare complete screen
cells and the VM arena; the count is not a count of distinct user workflows.
An independent TCP peer checks the exact outgoing data/flow bytes and supplies
binary input before, after and at the end of execution.

## Execution and recovery

`src/process/native_program.c` owns the combined synchronous lifetime. It rejects
reentry, foreign snapshot/process/UART ownership, invalid flags and IF0 before
handoff. The native process layer enforces DS=SS, current C environment, bounded
tail/name inputs and its established DOS COM/EXE/BAT/PATH/COMSPEC policies.
The controller clears CRT/DOS error storage before entering the process layer,
as native PROGRAM does, so an earlier missing target does not become a later
successful command's error notice.

Thirteen linked CPU admission cases forbid BIOS/DOS/port IO and compare all
non-stack data on rejection. A foreign SS case checks the entire DS image,
including its usual stack range, proving rejection before any near pointer to
a stack local reaches the CRT. BP/SI/DI and DS are preserved; ES is volatile
across the outer Watcom C/CRT ABI, as distinct from the individual UI adapters.

The controller captures the parent cursor and optional screen, drains/pauses
flow, releases the UART/vector, and calls the recovered process backend.
On return it reclaims UART ownership **before WAIT**, keeping the original ring,
unread rollback and startup baseline. This intentionally replaces the original
PROGRAM reset path that can discard RBR input. Serial failures remain typed.

The 439 exact UI bytes in `reconstruction/program_ui/` provide native text,
scroll, clear/fill, cursor position/shape, mode/scan-line helpers and WAIT
drawing. Fourteen function records and fourteen independent file mappings in
the retained REA bundle bind the SHA-pinned recovery. The ordinary build checks
the committed flat-region hashes and assembles relocatable objects; it never
reads an original executable or REA database. `recover.py` is analyst-only.

WAIT uses the native drawing routine with a platform-owned message pointer and
a maintained BIOS keyboard input binding. A real timer interrupt samples its
visible prompt, retained child output, restored UART framing/vector/PIC and
reentry rejection, then places two keys into the BIOS queue. WAIT consumes the
first; the second remains available. There is no successful keyboard stub.

Saving the screen always recreates standard parent mode/font geometry before
restoring all saved cells and the full cursor shape/position. Matching text
output remains visible while waiting; a graphics child is normalized before
the prompt can be drawn. NOCLEAR preserves same-geometry child output. A child
that changes geometry causes mode recovery and a `view_reset` result for the
future application renderer owner, rather than a fabricated renderer success. The original special raw child exit247
also requests a NOCLEAR view reset without discarding the visible text.

## Actual DOS checks

- Real children verify the native command tail, current inherited environment,
  cleared versus preserved screen, and released UART state, then leave graphics
  or changed text plus a replaced vector, baud/LCR/MCR and unrelated PIC bit.
- All parent cells and cursor restore in 80x25, 40x25, monochrome 80x25, VGA 80x43
  and 80x50 views after a graphics child. NOCLEAR retains a text child's mark.
- Six real open streams retain positions/data; the entire live VM arena and
  environment survive repeated process calls and an actual arena-backed
  environment fallback while a far screen snapshot is held.
- Missing targets, injected near/far-screen allocation failures, a foreign
  flow/snapshot owner, graphics/page admission failures and invalid flags return
  through explicit cleanup. A closed-UART command-processor route also works.
- Binary queued data and one-shot unread survive; independent post-return input
  works and final close restores startup hardware, IRQ and PIC state.

The earlier `native-program-01` and `-02` attempts had passing DOS assertions
but missed the final F on the independently observed wire, so neither counts
as acceptance. The harness now requires an END! acknowledgment and allows
DOSBox's separate nullmodem flush timer one BIOS tick after hardware drain,
then reads through socket EOF. Both failed captures remain retained.

A fresh tree containing only declared source inputs reproduces 20 DOS products
byte-for-byte, including PROGRAM, the display/process/UART diagnostics and their
owned children. The existing 963 display CPU/original comparisons and 13,045 DOS
display assertions also pass; the old DISPLAY executable remains byte-identical.

```sh
./tools/build test-native-program
./tools/build test-native-program-source
```

## Remaining application work

This historical component proof uses ordinary C streams. The later
[VM binding](ASPECT_PROCESS.md), [parent integration](ASPECT_PARENT_PROCESS.md)
and [foreground unwind](ASPECT_UNWIND.md) supply actual ASPECT streams/ASX,
selected resources, renderer leases and synchronous nonlocal recovery in separate
experimental builds. Original macro keyboard, mouse/window and error-notice
services still need composition before normal publication.
The [mouse primitives](NATIVE_MOUSE.md) now provide exact probe/init/callback
source and actual foreign-DS/SS execution. The later [composed owner](MOUSE_KEYBOARD.md)
adds initial configuration, native event consumption and driver suspension/
restoration through independent DOS children. Binding it into this controller,
the actual parent/fault paths and UI remains required.
Standard BIOS ROM font geometry is covered; arbitrary downloaded fonts, other
adapters, original additional views and physical Wi-Fi modem timing remain open.
The current terminal renderer still admits 80x25 mode3/page0. The new component
does not expand that production admission or publish an external command slot.

## Timed notice controller

The original PROGRAM error-message route passes BX to resident 427f, which
selects the bell form of 429a. Resident 4288 accepts a stack message and selects
the alternate tone form. The recovered
[controller source](../reconstruction/program_notice/core.asm) rebuilds all 190
bytes exactly, bound by independent MZ mapping and REA read/function evidence in
[provenance](../reconstruction/program_notice/provenance.json). It reuses 27
strlen and 44 DOS time-extraction bytes already recovered elsewhere.

The core computes horizontal placement around column 40 using native signed
16-bit division, updates the descriptor's left/right words, saves the window,
writes the text and restores the saved window. It returns after a key or three
observed changes in DOS seconds. A second key poll determines whether to consume
a key: an earlier transient key indication alone does not force a read. Each
observed clock change counts once, including backward changes and minute wrap.
It does not measure three elapsed seconds independently of clock behavior.
The native strlen requires the caller's forward string direction, and stack
arguments require DS=SS.

[Independent component receipt](validation/program-notice.json) accepts 495 CPU
cases and 495 matching genuine-original comparisons across all entries, message
length boundaries, sound selection, key arrival/disappearance and time changes.
Screen, sound and key callbacks are explicit modeled dependencies in these cases;
the actual recovered strlen and DOS time conversion execute. In 99 stopped-clock
cases the native wait intentionally remains active at the instruction bound.
Those are reproduced counterexamples, not successful bounded UI behavior.

Six actual 8086 DOS cases cross the three entries with a real BIOS queued key or
real DOS-clock completion. They verify native stack cleanup, text coordinates and
exact restoration of the screen captured by the maintained diagnostic platform.
Sound is an explicit no-op test boundary. The diagnostic does not supply the
original 3fc7/4015 window allocator/drawing or macro keyboard. A fresh directory
containing only seven declared source/provenance files reproduces all five
component products, with original executables and analysis absent.

```sh
./tools/build test-program-notice
./tools/build test-program-notice-source
# Analyst-only; requires the ignored genuine original executable.
./tools/build test-program-notice-original
```

The native controller is not published to the live application yet. Its long
message arithmetic can produce invalid window coordinates, and its stopped-clock
wait has no foreground UART service. The guarded component below now supplies native window storage/drawing. Real
keyboard/scheduler ownership and binding error notices into PROGRAM's normal
and unwind paths remain required. These requirements and the other macro/mouse/UI/geometry
requirements still precede normal external-command publication; all full F01-F16
gates and physical modem acceptance remain open.

## Native notice-window ownership

The original notice window pair at 3fc7/4015 now composes with its actual
frame, shadow, expansion/collapse, cell-copy and cursor-stack instructions.
[Provenance](../reconstruction/notice_window/provenance.json) binds twenty regions
(1,940 bytes) to independent MZ source mappings and complete REA byte reads.
Another 353 bytes reuse existing native full-screen snapshot/restore and display
helpers. The algorithms preserve native animation, shadow and pacing branches;
flat products remain byte-identical to the selected original.

The save routine snapshots the entire text screen before drawing its window.
When that allocation returns NULL, the native alert returns and drawing continues.
The matching NULL restore alerts without restoring pixels. Two explicit linked
counterexamples retain that destructive behavior; they are not accepted ownership.

The [source-owned owner](../src/ui/notice_window.c) first validates a complete
near input extent, stages its fields, checks mode3/page0/80x25 and reserves the
4,000-byte snapshot with two sixteen-byte guards. Only then can native cursor or
screen mutation begin. The native allocator consumes that reservation exactly
once; native restoration releases the real far-heap allocation. Invalid bounds,
undersized rectangles, wrapping input, attributes above 255, unsupported geometry,
reentry and allocation denial reject before drawing. Close retains the allocation
on guard failure or changed geometry; repairing that condition permits cleanup.
The private cursor/frame state and cdecl adapters explicitly use DGROUP and DS=SS.

[Independent receipt](validation/notice-window.json) accepts 98 linked cases with
98 genuine-original comparisons. Native snapshot/frame/shadow/animation/cell-copy
instructions execute against guarded video and heap regions; heap, BIOS scroll/
cursor, sound and CRTC I/O are declared model boundaries. The actual 8086 DOS
owner suite passes 771 checks and 114 allocations/frees. It uses real DOS far
heap and VGA text memory across six rectangles with animation on/off, rejection
and repair paths, and one hundred repeated lifetimes. Every completed lifetime
restores the screen/cursor and returns the used far-heap total to baseline.
The ordinary owner also compiles without diagnostic hooks.

The first two DOS integration attempts failed before emitting the C diagnostic result: local
data fixups used _DATA offsets while DS held DGROUP. Adding the explicit GROUP
fixes that adapter. A fresh controlled build that removes only that declaration
still has thirty identical raw native products but fails the actual DOS probe.
It remains rejected evidence. This demonstrates why flat byte matching alone
cannot prove a linked application's data context. Both initial failed DOS
captures and the controlled failure are retained in the audit custody directory.
Forty source/provenance files in a fresh tree reproduce all thirty-one products,
including WINDOW.EXE, with originals and analysis absent from the tree.

```sh
./tools/build test-notice-window
./tools/build test-notice-window-source
./tools/build test-notice-window-group-control
# Analyst-only: requires the ignored genuine original executable.
./tools/build test-notice-window-original
```

This is a component owner, not the normal application's error window yet.
Its admitted live component configuration disables sound; a reached sound or
alert dependency exits explicitly rather than pretending success. Native sound
policy, original shared-window/parent leases, other live geometries and physical
video timing remain unfinished. The serviced composition below now connects this owner to the timed notice
controller and foreground transport service. Actual PROGRAM normal/error/unwind
ownership remains required. The normal ASPECT dispatcher still rejects
DOS/RUN/SHELL; all full F01-F16 and physical modem requirements remain open.

## Serviced timed notices

The [notice runtime](../src/ui/notice.c) now composes the exact native timed
controller, window algorithms and text writer through explicit cdecl/callee-pop
adapters. It stages a NUL-terminated near message of at most 74 bytes and validates
all option/result extents before admission. Native centering therefore stays
inside the supported 80x25 window. Empty text and high CP437 bytes retain native
writing behavior. The caller may select animation, attribute, a bounded foreground
service callback and a sound callback. A NULL sound callback selects quiet
operation; the diagnostics record sound selection/errors and do not implement
or establish the original speaker policy.

Normal completion still follows three observed DOS-second changes or a real
BIOS key. Escape and extended keys have explicit result words. An independent
atomic BIOS tick sample enforces a configurable deadline, with midnight wrap and
invalid samples handled explicitly. A positive DWORD poll budget provides another
exit path without depending on time advancement; checking before increment avoids
unsigned wrap at the maximum budget. Defaults are attribute70h, no animation,
74 BIOS ticks and one million polls. Budget/service/clock failure unwinds through
an owned recovery frame and closes the real snapshot. No synthetic key is inserted
to make the original loop return. The callbacks must return in bounded time.

Cleanup retains the active notice when window guards or geometry prevent close;
after repair, `notice_recover` retries cleanup and preserves the original cause.
Recovery attempted from the running notice callback rejects. Window identities
also carry an open generation: a replacement window detected during a callback
stays with its current owner, including when the far allocator reused an address.
The tested callbacks must preserve queued display/input bytes rather than render
into the popup's saved screen.

[Independent receipt](validation/serviced-notice.json) accepts 583 actual 8086 DOS
checks and 69 matched window allocations/frees. Coverage includes native key
completion, Escape, extended keys, empty and maximum-length CP437 text, reentry,
sound/service errors, memory denial, guard/geometry retention and repair, foreign
window replacement, poll limits and fifty repeated lifetimes. A diagnostic INT21
observer returns a fixed DOS2C time while preserving other calls; real BIOS ticks
still force timeout. Separate controlled tick fixtures exercise midnight wrap and
invalid samples. The original INT21 vector is restored. The window-only suite
also passes all 771 checks on the updated generation-aware owner.

The real UART diagnostic passes sixteen COM1/COM2 cases crossed with NONE,
software, hardware and both flow policies and native completion/injected service
error. Each case passes 538 assertions (8,608 total), observes all 508 independent
peer bytes queued during the popup, then reads those exact bytes, exchanges
`READY!` afterward and restores the selected UART IRQ/vector/PIC/registers plus
screen/cursor. The payload contains all byte values except software-flow11h/13h,
repeated twice; those controls are separate explicit stimuli in S/B cases. The
exact guest wire is RPF for N/H and XON,RPF,XOFF for S/B. The first UART attempt
rejected the latter due to an incomplete oracle; that failed cohort is preserved,
and the accepted audit requires those lifecycle controls exactly, without stripping
arbitrary bytes. DOSBox nullmodem holds CTS ready and does not enforce RTS; this
is not physical flow timing or a Telnet/BBS interaction test.

A fresh tree with 62 declared sources reproduces all 33 products, including the
window, notice and UART diagnostic executables. Normal window/notice owners also
compile without diagnostic hooks. The UART variant gives the notice's recovered
clock a distinct symbol so it cannot silently replace the backend's deliberately
unreachable legacy clock fail-stop. Original and generated executable artifacts
are absent from the fresh tree's inputs.

```sh
./tools/build test-notice
./tools/build test-notice-uart
./tools/build test-notice-source
```

Actual PROGRAM/shared-parent view and input leases, arbitrary external nonlocal
fault recovery, native sound/macro policy, code-bank placement, other geometries,
BBS workflows and physical hardware remain required before normal publication.
The normal interpreter still rejects DOS/RUN/SHELL; no full F01-F16 gate closes.

## Bank-local notice recovery

The notice runtime now uses a [source-owned 8086 recovery frame](../src/ui/notice_checkpoint.asm)
instead of small-model CRT `setjmp`/`longjmp`. The latter uses near return
addresses without restoring CS; it cannot be wrapped in a returned C frame to implement recovery
in a separate notice bank. The new assembly entry owns the native call's live
stack frame in its own CS, rejects nested entry, and restores SP, BP/BX/SI/DI,
DS/ES and IF/DF after a synchronous notice abort. An abort without a live frame
or on a foreign SS terminates with DOS status127 rather than returning success.
Callbacks in another segment must return through a far bridge before aborting.

The [independent receipt](validation/notice-checkpoint.json) accepts 2,048 actual
8086 DOS calls across normal, abort, nested and deep-stack cases crossed with
IF0/1 and DF0/1. The map independently confirms that the probe and checkpoint
share a CS distinct from the far adapter/near callback's CS. The harness disables
code packing explicitly; separate segment names alone did not establish that
condition. Inactive abort is a separate DOS invocation requiring exit127. Four
declared sources reproduce this diagnostic byte-for-byte in a fresh tree.

The updated composed notice retains all583 DOS assertions and69 matched
allocations/frees; all16 COM1/2 N/S/H/B cases retain508 peer bytes and pass8,608
assertions. Sixty-three source files reproduce the33 window/notice/UART products;
neither notice executable links CRT jump helpers. Run the focused ABI test with:

```
./tools/build test-notice-checkpoint
```

This resolved the recovery-frame prerequisite for bank placement. The following
checkpoint supplies complete notice/window placement, CRT/platform/callback far
adapters and native helper isolation. PROGRAM error paths and outer
nonlocal-fault cleanup remain required. The frame is foreground-only and does
not catch arbitrary interrupts or faults. Normal application binaries and the
105-slot interpreter remain unchanged; full F01-F16 and physical gates stay open.

## Complete notice code bank

The notice runtime, guarded window owner, timed controller and native drawing,
text, clock and recovery helpers now link into NOTICECODE. The C entry points
use an explicit far ABI under `NOTICE_BANKED`; their data and stack arguments
remain near pointers within shared DGROUP and require DS=SS. Private native/C
callbacks stay near within the bank. The [CRT/platform bridges](../src/ui/notice_bank.c)
stay in the near CRT's `_TEXT` segment and return far. Service/sound callbacks
retain their original near pointer types and execute through these bridges in
`_TEXT`; supplying a near callback from a different CS is outside this ABI.

Reused display/string/clock symbols receive a consistent `notice_` prefix in
both their definitions and references, allowing the original application helpers
to coexist. The native algorithm sources and flat byte proofs are unchanged.
The builder emits separate production binding/owner objects without clock
fixtures, diagnostic key bridges or allocation-failure hooks. Default diagnostic
bank placement explicitly disables code packing, so the bank and near adapter
really execute with different CS values.

The [independent receipt](validation/notice-bank.json) accepts all583 DOS
notice assertions,69 matched allocations/frees and sixteen actual COM1/2
N/S/H/B normal/error cases with8,608 UART assertions. Each popup retains508 peer
bytes until close and then exchanges READY!, restoring screen/cursor and the
selected UART IRQ/PIC/registers. Decoded owner/runtime objects have no near call
escaping their code bank; every external far call names an explicit platform
adapter or bank API. Sixty-four declared sources reproduce all33 window/banked
notice/UART component products in a fresh tree without originals or prior objects.

The separate `build/aspect-notice-parent/ASPECT.EXE` also links the production
bank and passes all13 attached PROGRAM workflows, including the real DOS source
compiler and nested child execution. The parent has176 bytes left in near CODE;
NOTICECODE occupies5,237 bytes and may share a packed CS with PROGRAMCODE, while
remaining separate from the near CRT. These tests establish coexistence, not an
executed PROGRAM error popup. The standard105-slot interpreter is unchanged.

The near diagnostic builds were also rebuilt: an added header changed private
data ordering, so their actual new binaries were retested rather than assumed
identical. They retain583 DOS and8,608 UART assertions, and63 declared sources
reproduce33 products. The standalone window suite retains771 assertions with114
matched allocations/frees; its source declaration now includes the shared header.

```
./tools/build test-notice-bank
./tools/build test-notice-bank-uart
./tools/dev --command python3 standalone/build_aspect_process.py --notice-bank
./tools/dev --command python3 standalone/test_aspect_parent_process_dos.py --notice-bank
```

The next integration must show notices after failed PROGRAM execution without
changing the child's raw status, service the live transport through a correct
near callback, and retire or quarantine window/input leases after outer nonlocal
faults. Native sound/macros, mouse/shared UI policy, broader views, BBS workflows
and physical Boca/SPA2102 validation remain open. No full F01-F16 gate closes.

## PROGRAM error notices and outer recovery

The separate experimental notice parent now calls the banked service after
failed PROGRAM execution. It restores the UART, screen and cursor first, then
uses the native `FFFF` result plus nonzero CRT errno to select a source-owned
message. The [presentation adapter](../src/process/program_notice.c) retains
the recovered2/7/8/12/other error branches; it never overwrites the child's raw
status. Successful execution does not trigger a stale error notice. The near
callback getter resides in `_TEXT`, as does the returned transport callback;
the bank calls it through the existing far service bridge. Polling preserves
queued input and continues software/hardware flow control. Notices remain quiet;
native sound policy is still a separate requirement.

PROGRAM tracks a pending notice until its window retires. A retained damaged
snapshot keeps the controller busy, and external teardown preserves its parent
lease and private streams. The private [outer recovery ABI](../src/ui/notice_unwind.h)
may only be called after the outer owner has discarded the stack containing the
notice and callback. It invalidates the old bank-local frame, clears the running
state and uses normal generation/identity-checked cleanup. Successful retirement
returns OK while retaining the original cause in the result. It is not a live
callback cancellation API or a general interrupt/allocator fault handler.

The [independent receipt](validation/program-notices.json) accepts14 actual8086
DOS socket-peer sessions. Eight normal sessions cover COM1/2 crossed with NONE,
SOFT,HARD,BOTH flow. Six fault sessions cover before/during/after notices,
foreign-DS DIV and native typed abort, including COM2/BOTH. Every session runs
the same missing-target command twice in the same process across two VM runs,
preserves rawFFFF for both, and retains508 exact peer bytes until afterward.
The second script consumes every byte and completes READY!/END exchanges. Actual
flow-control wires include startup/close bytes and two PROGRAM pause/resume pairs.

The focused banked probe checks the visible error text, restored video/cursor,
PSP,JFT,INT0/23/24 vectors, six stream owners and continued serial activity. A
fault during the notice leaves cause STATE while cleanup succeeds; the second
notice confirms that the abandoned recovery frame does not remain armed. The
general fault diagnostic initially exceeded near CODE by1,189 bytes, so this
focused probe lives in NOTICECODE with explicit far platform bridges. Existing
general fault diagnostics and their checks remain intact. This focused build
does not enable the general `ASPECT_EXTERNAL_DIAGNOSTIC` instrumentation.

All13 attached terminal/PROGRAM workflows pass on the new ordinary experimental
parent, including real DOS source compilation and nested children. They prove
normal return behavior; popup faults above are observed in the raw CLI, rather
than through the attached parent. A fresh tree with236 declared source files
reproduces35 products: both experimental ASPECT binaries plus33 notice/window
products. The updated near/banked notice suites retain583 checks each, and the
bank-local ABI probe retains2,048 calls. The near notice closure now declares64
files including the private recovery header. Parent near CODE has160 bytes free;
the focused diagnostic has48 bytes free.

```
./tools/build program-notices
./tools/build test-program-notices
./tools/build test-program-notices-source
```

Actual DOS fixtures for errno7/8/12 and generic failures remain to be accepted.
Attached-parent popup fault observations, damaged-window quarantine/retry tests,
original sound/macros/mouse/shared UI policy, other geometries, BBS workflows and
physical hardware remain open. The ordinary105-slot interpreter still rejects
DOS/RUN/SHELL. No full PROGRAM policy or F01-F16 application gate closes here.

## PROGRAM message branches and post-error EXEC

The [expanded independent receipt](validation/program-notice-errors.json) accepts
all five message-selection branches through actual DOS runs. Each fixture runs
on COM1/HARD and COM2/BOTH, with the following explicit mechanisms:

| CRT errno | Saved DOS error | Fixture and scope |
| --- | --- | --- |
| 2 | 2 | Missing target with a controlled empty PATH. |
| 7 | 10 | A short RUN command finds a BAT in a long PATH directory; the maintained composed-tail bound rejects it before EXEC. |
| 8 | 11 | The diagnostic explicitly requests unsupported DOS EXEC mode4 on a valid child. This verifies the real DOS error-to-CRT/popup route, not malformed-MZ rejection. |
| 12 | 8 | The diagnostic consumes the actual remaining DOS paragraph block after snapshot/heap preparation. A witnessed real EXEC fails; the block is released before drawing the popup. |
| 13 | 5 | A real empty executable is rejected by the built-in DOS loader and selects the generic message. |

The long-tail fixture keeps the complete RUN text below82 characters to respect
the recovered frontend's fixed buffer. It reaches the longer composed BAT name
through PATH rather than overflowing that buffer with a long literal. Clearing
PATH in each script also makes EXEC attempt counts independent of inherited
search directories. No batch execution marker may appear.

Every session then starts a second VM invocation, shows the missing-target
notice, and runs [SUCCESS.COM](../standalone/notice_success_child.asm). The real
child creates SUCCESS.OK containing OK and exits0. The final comparison word is0,
both saved CRT/DOS errors are0, and the notice count remains2. This checks that
the previous failure does not become a stale popup after successful execution.
All508 peer bytes are retained until the script consumes them afterward. Exact
software-flow wires include the three PROGRAM pause/resume pairs, then the
READY!/END exchange; screen/cursor, PSP/JFT/IVT and stream-owner checks also pass.

The focused diagnostic has a FLAGS-preserving counter immediately before the
actual INT21/4B instruction. A test-only mode byte requests AL4 solely for the
explicit errno8 fixture. Test-only far memory hooks bracket process execution;
they do not activate the existing allocator-failure switches. The memory runs
record30,228 DOS paragraphs held, successful release and one failed EXEC before
the later missing/successful calls. The guarded long-tail path records no initial
EXEC attempt, as required. The flat recovered EXEC product retains its exact
bytes; the ordinary experimental parent also remains byte-identical.

The format distinction matters: the [upstream DOSBox-X loader](https://raw.githubusercontent.com/joncampbell123/dosbox-x/master/src/dos/dos_execute.cpp)
treats short nonempty files as COM programs and uses invalid-format status for
unsupported EXEC modes. The explicit mode fixture establishes the mapping and
presentation route. Acceptance of naturally malformed executables on a real DOS
kernel remains required; this fixture does not close that requirement.

All10 expanded sessions and all14 original popup/fault regressions pass on the
new diagnostic. A fresh236-source tree reproduces35 products; the child is also
independently assembled and hash-checked. Since the ordinary parent is unchanged,
the previous sealed13 attached-parent workflows remain applicable without being
rerun. The auditor verifies their complete stored custody and exact image identity.
Near CODE remains160 bytes spare in the ordinary parent and32 in the diagnostic.

```
./tools/build test-program-notice-errors
./tools/build test-program-notices
./tools/build test-program-notices-source
```

Natural malformed-executable handling on real DOS, attached-parent popup/fault
observations, damaged/foreign-window quarantine and retry, original sound/macros/
mouse/shared UI policies, other geometries, BBS regression and physical modem
acceptance remain open. Full PROGRAM policy and all F01-F16 gates remain open.

## PROGRAM window quarantine and stopped-owner retry

The PROGRAM integration now treats either its own active notice or a still-open
window as an outstanding owner. Previously, a service callback could close the
notice and open a replacement window: notice cleanup correctly left that foreign
window alone, but PROGRAM checked only `notice_active()` and could release its
parent lease anyway. The [banked PROGRAM owner](../src/process/program_notice.c)
now retains its pending state until both owners retire. Its unwind does not erase
the previous cause when a foreign window remains after the original notice closes.

VM shutdown also previously continued closing streams after external cleanup
had deliberately retained the handle mask. The invocation-file close now defers
while private handles remain masked, and final VM teardown defers while PROGRAM
is busy. The six script streams, invocation file and their saved positions remain
owned, rather than being closed through masked DOS handles.

The private `program_notice_retry()` far entry accepts only a stopped invocation
with a retained external scope. A live callback receives STATE without changing
ownership. Retry uses the existing process/window/handle/stream teardown; a
failure keeps the scope and owners held. After an invocation has already returned
and restored its caller's divide vector, successful retry retires the foreground
scope without trying to reacquire that dead invocation's ISR scope. Normal active
scope exit retains its original vector checks. Final VM cleanup runs only after
the external leases have retired. This is an owner API, not an end-user repair UI.

The [independent receipt](validation/program-notice-quarantine.json) accepts12
actual8086 DOS sessions: guard damage or a foreign replacement window crossed
with DIV, foreign-DS DIV and typed abort, on COM1/HARD and COM2/BOTH. The probe:

- Raises the real fault with508 peer bytes queued during the popup.
- Confirms PROGRAM, the window, six script streams and the invocation file remain
  held; a masked JFT matches its original baseline while the saved owners stay live.
- Rejects live-callback retry and a new VM invocation.
- Retries before repair and confirms the exact displayed window/cursor remain intact.
- Repairs the guard or closes the replacement through its own window owner.
- Retires all leases, preserves cause STATE and restores the original screen/cursor,
  PSP/JFT/IVT state and balanced far allocations/frees.
- Runs another popup and successful DOS child, consumes all508 exact peer bytes,
  and completes the READY!/END exchange with the expected flow-control wire.

The focused diagnostic enables the window owner's guard/count hooks; the ordinary
parent retains the production owner without those hooks. A replacement is never
closed by the abandoned notice's cleanup. Guard cases release two allocations
across the session; replacement cases release three, including the foreign owner.
The initial failed cleanup and subsequent failed/successful retries remain
distinct, with three recorded recovery attempts and the original CPU/typed result.

The parent build now reuses PROGRAM's existing far `int86` and `memset` bridges
for the notice bank. The checked OMF transformation changes only EXTDEF names,
preserving every other record, type index, code/data byte and fixup. Duplicate
notice wrappers are omitted in the parent-specific platform object; standalone
notice builds retain their own platform. The auditor independently reconstructs
both owner/runtime import transformations and checks the linked bridge locations.
Near CODE has144 bytes spare in the ordinary parent and16 in the focused diagnostic.

All24 previous popup/error sessions and13 attached normal PROGRAM workflows pass
on the changed images.237 declared sources reproduce35 products in a fresh tree.
The standalone notice/UART executables are byte-identical to the prior accepted
component products. The historical general fault and error receipts retain their
original scopes and custody.

```
./tools/build test-program-notice-quarantine
./tools/build test-program-notices
./tools/build test-program-notice-errors
./tools/build test-program-notices-source
```

Those quarantine receipts cover the raw CLI. Attached-parent popup/fault and
selected quarantine cases are covered separately below. Natural malformed-
executable behavior on a real DOS kernel, complete original mouse/macros/sound/
shared UI policies, other geometries, BBS regressions and physical modem validation
remain open. Full PROGRAM policy and all F01-F16 application gates remain open.

## Attached terminal popup and recovery observation

The [attached checker](../standalone/test_program_notices_parent_dos.py) runs the
focused notice diagnostic as the real terminal's foreground ASPECT child, with
an independent passive DOS EXEC observer. Its `PCPNOTICE` request ends in `P`
after an explicit window selector (`N`, `G` or `W`). This diagnostic mode captures
the real pre-popup screen/cursor after the login banner; it never resets the
parent's video mode, paints a synthetic baseline, or asserts UART DTR.

The [receipt](validation/program-notices-parent.json) covers11 actual8086 DOS
sessions: DIV before/during/after the popup, plus typed abort and foreign-DS DIV
during the popup, on COM1/HARD; three guard-damage cases on COM1/HARD; and three
foreign-window cases on COM2/HARD. It checks:

- The first typed/CPU error reaches the outer DOS caller unchanged.
- Screen/cursor restoration, PSP/JFT/vectors and all six stream owners around
  the first fault or repaired stopped-owner retry.
- Rejected live retry, rejected new VM entry, and an unchanged retained window
  after failed cleanup; repair retires the selected owner and preserves cause.
- An exact508-byte printable response displays through the real attached ANSI
  renderer during the next script, followed by another error popup and a real
  source-built DOS child that writes `SUCCESS.OK`.
- The passive observer's parent file owners, JFT and saved resource bytes match
  before/after; all observed PROGRAM lease begins/ends balance and the terminal
  continues transmitting after ASPECT returns.

The queued response is printable terminal data. An initial arbitrary binary
fixture reached the terminal's normal between-script display path and correctly
hit unsupported control handling. Normal successful script completion can drain
input with display disabled, so this checker specifically exercises fault/retry
paths. Exact raw binary input preservation is established by the separate14-case
CLI regression, not by this attached renderer test. The before-popup fault does
not claim that its response was already queued at the fault instant; the other
attached fault phases observe508 queued bytes.

The ordinary experimental ASPECT executable remains byte-identical to the
previous accepted build. Only the focused diagnostic changes;237 declared sources
still reproduce35 products without an original executable, install or REA database.
This closes the selected attached popup/fault observation gap, while full shared
UI policy, other flow-control combinations in this attached test, live BBSes and
physical modem acceptance remain open.

```sh
./tools/build test-program-notices-parent
```

## Natural malformed MZ rejection on FreeDOS

The [kernel checker](../standalone/test_program_notices_kernel_dos.py) boots the
pinned FreeDOS1.4 floppy distribution, using its actual kernel rather than
DOSBox's internal DOS. An independent COM witness records reported and true DOS
version7.10 and OEM FD before ASPECT starts. The diagnostic runs ordinary EXEC
mode0: the request contains no unsupported-mode selector, memory-pressure fixture
or fault injection.

A38-byte MZ declares one relocation at file offset1000h, beyond EOF. The loader
returns DOS13, which the exact native error map converts to CRT22. PROGRAM shows
its generic execution-error notice, preserves rawFFFF and restores the screen,
cursor, PSP, JFT and vectors. A second invocation runs the missing-file popup,
consumes508 exact queued binary bytes, retains all six stream positions/output,
and executes the source-built success child with final CRT/DOS errors0. Both
window allocations are freed. The command processor then executes the identical
MZ with only its relocation count cleared; its body exits99 and the batch file
checks that exact result. This positive control distinguishes rejection of the
missing relocation from a nonworking EXE environment.

The [receipt](validation/program-notices-kernel.json) records the pinned archive,
boot template, tested executable, source and capture hashes. The current upstream
[FreeDOS loader](https://github.com/FDOS/kernel/blob/master/kernel/task.c) also
contains an invalid-data return when relocation reading fails; the booted
pinned distribution and observed result establish this test's behavior separately.

An initial empty-file attempt returned raw0 on this pinned kernel and is retained
as a failed local experiment, not accepted format-error evidence. This test proves
one natural malformed-MZ rejection as DOS13/CRT22. It does not establish natural
DOS11/CRT8 behavior, other DOS kernels or malformed headers, attached-parent
behavior on FreeDOS, or physical modem compatibility. The earlier explicit
EXEC-mode4 fixture remains the evidence for the specific format-error popup.

```sh
# Uses the same pinned archive cache as test_kernel_critical_dos.py:
# build/freedos-kernel-lab/FD14-FloppyEdition.zip
./tools/build test-program-notices-kernel
```
