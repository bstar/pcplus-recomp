# Shared keyboard output during ASPECT

The [current script-time window](ASPECT_LOCAL_UI.md) extends this earlier
key-output checkpoint: capability8 adds checked transport-only polling and the
native Alt-Z reference/help window; capability9 also admits external PROGRAM.
Ordinary bindings retain this shared output path. Other local actions remain
unfinished. Earlier capability6/7 evidence below retains its historical scope.

An admitted ASPECT child now forwards ordinary keys through the parent's
selected keyboard profile and continues its script. The native WHEN service
still acquires and records keys at its ordinary safe points. A capability6
request sends the complete16-bit normalized key; the parent uses the same
raw classifier and bounded output routine as the terminal's ordinary key path.
The child remains the only UART owner. Parent output calls back into that
owner instead of writing through the suspended parent's driver or leaving
bytes in its TX queue.

All79 KBD slots use the actual parent table, including enhanced/numeric keypad,
function/modifier banks and current DECCKM changes. Stored FF becomes wire NUL;
empty bindings remain empty. Both paths validate the full12-byte slot before
output. Ordinary queue output still reserves the complete binding's capacity
before appending anything. Existing low-E0 Enter/slash compatibility aliases
apply to script keys too. Unknown native no-op keys emit nothing. Recognized
local commands and hooks fail explicitly rather than transmitting scan bytes.

The request pulls one checked duplex snapshot: FFFF inherits the parent,
otherwise it uses the script's current SET DUPLEX byte. It never commits that
snapshot to parent preferences. Native-derived local echo now shares the actual
renderer: ordinary literals echo before transmission, mapped bindings echo
after transmission, Backspace uses control8, arrow banks invoke the recovered
cursor helpers, and legacy Home invokes the native(0,0) cursor call. Printable
keypad, Tab and Enter bindings echo their original stored bytes; FF remains FF
for local echo, unlike its wire encoding. Enhanced Home's native slot56 has
no local echo; legacy Home's slot76 moves the cursor.

Half-duplex Insert/Delete now call the actual recovered ICH/DCH helpers once.
Both standard and enhanced identities perform checked admission before any
binding reaches the wire. Unsupported geometry and metadata pointers return
unsupported without wire/video mutation. Marker deletion now calls the native
field repair through checked far bridges. Admission
restores the parser parameter count, and echo does not route through a CSI
repetition wrapper or change that count. Existing CSI error/no-op behavior is
preserved. These echo helpers implement the native cell edits, not a new local
insert-mode toggle.

Renderer capability6 retains capability5's BIOS inheritance. The ASIO
descriptor remains version4/48 bytes, with6 included in its guard. Older
capabilities1–5 are rejected before UART access. A key request must pull its
duplex policy exactly once; missing, duplicate, unsolicited or invalid-selector
callbacks fail. UART/cancellation errors and unsupported keys unwind through
the existing checked parent/child stacks. Raw parser continuations still bypass
translation and WHEN matching; file actions remain deferred on callback stacks.

The source is `src/terminal/key_dispatch.asm`, with small resident adapters and
the main routine in ASPECT_CODE. `terminal_enqueue_al` routes scoped output to
the child. `src/aspect/resident_render.c` owns the request and callback lifetime,
and `src/terminal/aspect_renderer.asm` validates the live lease, desktop and
policy before invoking the shared routine.

Reverse Tab now executes the recovered native routine with the selected tab
stops and protected-field metadata. Checked admission precedes all wire/echo
effects. Its real boundary/coordinate/division/protected-home services share
ASPECT_CODE and use explicit far bridges to resident cursor and notice code.
Malformed tables and nonprogressing native wrap are rejected before mutation.
Protected navigation bypasses unused tab-table validation. Protected scrolling
now uses actual native field repair with admitted backing. Unsupported geometry
and suppressed wrap remain pre-wire failures. See [reverse Tab](KEYBOARD_REVERSE_TAB.md)
and [attribute boundaries](ATTRIBUTE_BOUNDARY.md).

## Validation

The [checkpoint record](validation/aspect-key-output.json) binds the current
parent, child, compiler, checker hashes and the fresh source-only product proof.

The CPU key-output checker executes837 product cases over both profile tables,
all79 slots and full/half duplex, with declared echo/cursor recording endpoints.
It checks exact queued bytes, echo ordering, FF/NUL differences, aliases, no-op,
hook/local rejection, invalid bindings and atomic queue-capacity failure.
An independent316-case trace executes the exact recovered native dispatcher
to check echo-service choices; emitter/UI/status calls are recording boundaries,
and every omitted service remains listed. This does not claim full native UI
execution. The separate child checker covers14 scalar policy/lifecycle cases.

The DOS product test injects actual BIOS keys while the script waits for END.
Its owned peer withholds END until typed `done` reaches the wire. Only then
does the script send its continuation/password marker. This prevents keys
typed after script exit from masquerading as script-time support. Cases use
ANSI/VT220 profiles, binary custom KBD bindings, full/half duplex, native cursor
echo, and typed half-duplex editing failure before output. Existing parent
renderer/query, history, handles, sink-owner and post-return keyboard checks
remain active.

The current16 DOS cases include actual half-duplex Insert/Delete video edits,
default/custom reverse-Tab stops and continued script execution. An unsupported
local Alt-F9 key retains typed-error cleanup coverage. A separate55-case product replay exercises the real
video/native editing helpers in both profiles, standard/enhanced keys,
single/doublewidth cells, unchanged cursor/parser parameters and pre-wire
geometry/metadata rejection. The837-case scalar-boundary test separately
checks dispatch, bindings, wire encoding and ordering.

An additional630-case linked replay exercises actual reverse-Tab/native field
navigation and near/far bridges with hardware-only models. It includes
1..25-row planes, empty/malformed tables, circular fields, doublewidth rows,
pre-wire rejection and a bell BIOS that clobbers registers. The718-case
component test separately verifies exact boundary and viewport-coordinate
instructions with declared cursor/notice recording boundaries.

The925-case [live repair replay](ATTRIBUTE_REPAIR.md) executes the actual far
repair bridges and native repaint services, including39 scroll, wrapped
reverse-Tab and repeated parser/keyboard Delete consumers. It compares full
video and metadata/value planes. Native whole-plane metadata movement under
partial video margins is characterized explicitly.

Earlier failed fixtures are retained privately. `shared-keys-02` omitted the
three displayed END characters from its cursor predictions. `shared-keys-04`
asked enhanced Home for legacy Home echo; explicit STANDARD BIOS selection now
tests the legacy identity. The product binaries were unchanged for those
fixture corrections. Neither failure is hidden by changing a product assertion
or treating output after script return as script output.

## Remaining application work

Local menus, transfers, macros/HOOK/PROGRAM dispatch, native abort confirmation
and original status/selection post-actions are unfinished during scripts.
Reverse-Tab and Insert/Delete retain explicit preflight rejection for
unsupported geometry and suppressed wrap. Line-edit metadata ownership and
complete viewport/audio configuration remain unfinished; full-duplex bindings still transmit without
requiring a supported local-echo plane.
Original blocking per-binding pacing remains outside the maintained queue
policy, as it was before this integration. A raw script without an admitted
parent still has no keyboard-profile/UI owner and reports unsupported for
ordinary keys. Physical BIOS/UART/Wi-Fi modem behavior remains unverified.
No F01–F16 whole-application gate closes at this checkpoint.
