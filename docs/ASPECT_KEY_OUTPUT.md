# Shared keyboard output during ASPECT

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

Earlier failed fixtures are retained privately. `shared-keys-02` omitted the
three displayed END characters from its cursor predictions. `shared-keys-04`
asked enhanced Home for legacy Home echo; explicit STANDARD BIOS selection now
tests the legacy identity. The product binaries were unchanged for those
fixture corrections. Neither failure is hidden by changing a product assertion
or treating output after script return as script output.

## Remaining application work

Local menus, transfers, macros/HOOK/PROGRAM dispatch, native abort confirmation
and original status/selection post-actions are unfinished during scripts.
Half-duplex reverse-Tab and Insert/Delete echo services are not linked and
return unsupported before any wire or echo output; full-duplex bindings work.
Original blocking per-binding pacing remains outside the maintained queue
policy, as it was before this integration. A raw script without an admitted
parent still has no keyboard-profile/UI owner and reports unsupported for
ordinary keys. Physical BIOS/UART/Wi-Fi modem behavior remains unverified.
No F01–F16 whole-application gate closes at this checkpoint.
