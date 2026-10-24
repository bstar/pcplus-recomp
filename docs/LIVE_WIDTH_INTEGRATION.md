# Live width integration boundaries

The native reset diagnostic and the interactive terminal have different memory
owners. The diagnostic's whole-image snapshot is unsuitable for the live
application: restoring it would also restore a stale UART ring, parser/owner
state and stack. Width requests still stop explicitly in
`src/terminal/boundaries.asm`; no live 132-column support is claimed.

The [logical row-stride checkpoint](LINE_METADATA_STRIDE.md) removes fixed80
arithmetic from the live line-metadata owner and verifies its buffer operation
at132 columns. The wider admission and composition requirements below remain.
The [live viewport checkpoint](VIEWPORT_LIVE.md) now joins actual cursor/pane
copying, parser output and row erase over the static shadow, including a DOS8086
test-only wide-state fixture. Normal width requests remain disabled.
The [wide-field checkpoint](ATTRIBUTE_REPAIR_WIDE.md) extends shared admission
to native repair and boundary navigation, including a DOS region-repaint
consumer. Broader width/reset and UI/child workflows remain open.
The [private native reset context](NATIVE_RESET_CONTEXT.md) now proves actual
native soft reset can run on a separate DS=SS bank while the real UART ISR
updates root receive data. The [optional parent integration](NATIVE_RESET_PARENT.md)
namespaces that bank and borrows inactive redisplay storage with exclusive owner
admission. Retained-child allocation passes, and the
[compact interpreter](COMPACT_RUNTIME_FORMAT.md) now passes nested ASPECT source
compilation in four recorded DOS8086 workflows for the cold-only parent. The new
[explicit live transaction](LIVE_RESET_TRANSACTION.md) now supplies checked
projection/commit and display rollback for a plain24-row layout. Both modeled
fault/IRQ checks and actual DOS commits pass. The subsequent
[compiler heap fix](COMPILER_ARENA_ADMISSION.md) now passes nested compilation
beneath this larger variant in ordinary display geometry. General geometry/protected-field/UI composition and
normal peer width ownership remain required.

The current application already reserves two independent 4,096-byte near
attribute planes and an 8,192-byte far shadow in `src/terminal/state.asm`.
A 132-by-25 logical screen requires 3,300 bytes per attribute plane and 6,600
shadow bytes. The native diagnostic's 24-row screen requires 3,168 and 6,336
respectively. Capacity alone therefore does not require replacing the live
shadow allocation. Any live design must preserve its existing segment:offset
ownership, segment bounds and lifetime across DOS child execution. The diagnostic
DOS allocator remains evidence about native reset composition, not a reason to
free the application's static arena.

Physical video can remain 80 columns while recovered cursor and viewport code
select left or right panes of the logical 132-column screen. The maintained
viewport copy must retain the foreign-DS CGA correction. Physical BIOS geometry,
logical row stride, visible offset and active pane are distinct state.

Current source boundaries that must be resolved before admitting peer width
requests include:

| Owner | Current constraint | Required integration evidence |
| --- | --- | --- |
| Cursor and viewport | Owned pane hooks, separate capture refresh and static-shadow cursor/output/erase now pass; width requests still trap | Integrate normal width/reset ownership and broader scrolling/field operations with the checked pane state |
| Attribute navigation and repair | Ordinary80 checks and owned132 viewport admission now cover repair/navigation | Compose normal width/reset transitions and broader scrolling/editing/keyboard consumers with these verified planes |
| NETWORK line metadata | Logical row stride now drives the buffer kernel; live admission still requires 80 columns | Compose the verified132-byte buffer operation with native video, region bounds and field repair in both panes |
| Current-profile RIS | `terminal_reset.asm` restores captured startup geometry and clears static storage | Explicit semantics for width requests versus RIS, with no stale viewport pointers or configured defaults |
| Screen snapshot | `snapshot.asm` freezes exactly 25 rows of at most 80 characters | Logical-width export or an explicit visible-pane operation without truncating a claimed whole-screen export |
| Local redisplay/menu | `redisplay.asm` refuses an enabled viewport | Usable local actions and restoration of the live logical screen while receive processing continues |
| Script renderer | `src/aspect/renderer_policy.c` admits only 80-by-25 with viewport disabled | Parent/child renderer state, mode-list preflight and return ownership in both widths |
| Status row | Status rendering uses physical 80-column video and the last physical row | Logical row count/status visibility agreement; pane copying must preserve the status owner |

A live transaction must snapshot only the display state it owns, keep immutable
baseline/profile defaults separate, and leave UART, deferred serial input,
connection state, file handles and foreground owner state outside rollback.
The near group is already 64,080 bytes in the guarded custom-IRQ package; new
state must be budgeted against that measured layout rather than appended
unconditionally. A far snapshot requires its own non-overlapping declared owner.

Acceptance needs actual linked renderer tests for width entry/exit, output,
wrapping, scrolling, erase, attributes and overlapping pane regions; actual DOS
checks for reset and local/child workflows; and a BBS session that changes width
while incoming data continues. The allocation/reset diagnostic's passing cases
do not establish any of those live application outcomes.
