# Composed PROGRAM controller

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
wait has no foreground UART service. Next compose the native window save/restore
and real keyboard/scheduler ownership, then bind error notices into PROGRAM's
normal and unwind paths. These requirements and the other macro/mouse/UI/geometry
requirements still precede normal external-command publication; all full F01-F16
gates and physical modem acceptance remain open.
