# Internal live status-row transaction

`--status-owner` links the maintained far-cdecl `terminal_status_toggle()`
component. It performs a live24/25-row status transition with rollback, using
recovered scroll/cursor/status services and the staged captured-default helper.
It is not byte-identical recovery of native46BA and has no key/menu binding.

This first admission is **offline only**, BIOS80x25 mode2/3 page0, narrow ANSI/
VT220 with unprotected fixed planes. Connected requests return unsupported3
until the Linux bridge has a coherent size contract. Other modes and active
owners also refuse. These are unfinished integration gates, not reduced final
requirements or a claim that the original Status/Lines commands are complete.

## Ownership and commit

The component checks DS=SS, IF enabled/DF clear, reset readiness, parser/profile/
geometry/cache coherence, storage identity, supported status formatting and all
current foreground/frame owners. It refuses active/deferred notice leases; the
caller must retire a valid notice through its existing owner before acquiring
this transaction. It neither closes a viewer nor steals a pending modal action.

No scheduler, DOS, serial sender or parser runs during the transaction. UART
interrupts remain available, and queued input is retained for parsing afterward.
The existing EXEC/live/view frames are borrowed only after quiescent admission:

| Existing scratch frame | Transaction backup |
| --- | --- |
| program_screen | 4000 video bytes |
| redisplay_live | 4000 narrow shadow bytes |
| redisplay_view | 2000 attribute flags plus2000 previous-attribute bytes |

They are statically nonoverlapping frames checked by the normal linker/memory
inspection. Their inactive scratch contents are replaceable; this is not a
snapshot of every inactive UI workspace. Live scalar fields, line flags, BIOS
cursor and captured reset words are separately saved on the bounded stack.
No new far frame/heap allocation is added.

The captured reset defaults are updated only after their complete validation.
Hiding exposes row25, clears it with the original status attribute, initializes
its metadata and expands following bounds. Showing contracts the effective
extent; a cursor on row25 triggers the real scroll helper before the old complete
geometry is released. Custom margins survive if still representable; an
unrepresentable contraction refuses before commit. Saved row coordinates clamp
into the new extent. The real parent status service draws the restored status.

A status renderer failure restores live geometry, captured defaults, video,
shadow, both metadata planes, line flags and BIOS cursor before releasing the
owner. The normal status sampler may invalidate its cache and repaint later;
its cache is not a live geometry snapshot. This is foreground failure rollback,
not support for arbitrary concurrent programs or foreign interrupt-time drawing.

## Cursor and wrap invariants

The native fields named screen_previous_row/column are the cursor's offset
cache. They must agree with the current cursor at admission. On contraction,
the old cache is retained until native screen_set_cursor applies its signed
delta to video and attribute offsets. Clamping the cache first would leave
those offsets pointing at the old bottom row.

A pending deferred wrap survives hiding and a nonscrolling show. The real scroll
helper clears it when scrolling is required. Unconditionally clearing it would
make the next incoming character overwrite the last column instead of wrapping.
Captured-default resizing now also refuses incoherent old cursor caches.

## Evidence and limits

The [receipt](validation/status-transition-owner.json) binds76 linked transaction
inputs,250 captured-default inputs and enabled/disabled source reproductions.
Actual C/ASM code executes native scroll/cursor/status, parser/CPR/RIS, notice
admission, scalar/default/frame rollback and queued UART continuation. Tests
include32 owner refusals,32 geometry/profile/connected refusals, custom margins,
row25 cursor movement, pending wraps, stale cache rejection, notice ownership,
and failures both before rendering and after an actual draw/scroll. Fault tests
change an input/error field at the real renderer boundary; no product function,
instruction or return address is replaced.

Both builds reproduce exactly from declared sources in empty Git-free trees
without originals. The component has544 declared sources, resident code65386
bytes (150 spare), CONFIG_CODE58522 and one persistent owner WORD. DGROUP still
fits65024 bytes. Existing three frames are reused; stack guards remain checked.
With the option disabled the executable remains exactly7df99c1f, the existing
software-accepted package. The internal component is3756c6d7 and is not packaged,
installed or accepted for hardware tests.

The CPU checks alone establish no actual DOS/BBS/physical execution. A
subsequent [separate foreground diagnostic](STATUS_TRANSITION_DOS.md) now adds
actual DOS/virtual-UART evidence for six successful offline states, while the
ordinary component identity remains unchanged. It does not inherit the disabled
package's BBS/physical acceptance. Online bridge
size/NAWS policy, wider/larger modes, real foreground bindings, DOS/BBS tests and
physical modem acceptance remain open. The original39-command reference still
has13 unavailable entries.

```sh
./tools/dev --command python standalone/check_status_transition_live.py \
  --terminal build/COMPONENT/TERMINAL.EXE --output build/NEW-transition
./tools/dev --command python standalone/check_reset_rows_live.py \
  --terminal build/COMPONENT/TERMINAL.EXE --output build/NEW-defaults
./tools/dev --command python standalone/prove_terminal_manifest.py \
  --terminal build/COMPONENT/TERMINAL.EXE --output build/NEW-source-proof
```

The subsequent [staged Linux NAWS candidate](../lab/bbs/patches/synthmodem-window-size/README.md)
now has codec and owned Enigma size-update checks. It introduces no serial-side
control path and is not installed. It does not lift the connected-state refusal
or establish an atomic DOS/bridge geometry transaction or editor reflow.

The subsequent [actual ENiGMA editor comparison](TELNET_EDITOR_RESIZE.md) checks
an unsaved30-line draft across80x24→80x25→80x24 updates. Editing, paging and
discard retain the fixed24 behavior; the active art-backed editor emits no
resize redraw in the observation windows and still pages14 document lines.
This adds scoped remote-editor continuity evidence, not DOS/bridge integration
or dynamic layout acceptance. The connected-state refusal remains required.

The separately optional [BIOS row bank](DISPLAY_ROWS_TERMINAL.md) now executes
inside the DOS parent in a startup diagnostic. It is a low-level prerequisite,
not a wider geometry transaction: this owner still requires BIOS80x25 and all
existing quiescence/frame/online guards. No status/line key is enabled by linking
the new bank.
