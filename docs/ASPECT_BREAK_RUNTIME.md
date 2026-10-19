# BREAK in the DOS interpreter

The source-built interpreter now runs native BREAK0D, SET BREAK09 and FETCH37.
BREAK uses the maintained owned UART transport; the selected SET/FETCH command
bodies and generic FETCH dispatcher remain recovered instructions. The runtime
supports71 opcode slots, twelve SET setters and the same twelve FETCH getters.
The host compiler's setting-query grammar is separately checked against the
original compiler. Other opcodes/settings, recorder and complete application
behavior remain open.

## Duration and lifetime

A parent/child ASIOv4 capability3 handshake inherits the parent's current raw
BREAK word exactly once per interpreter invocation. It does not convert, clamp
or persist the value. Parent import still reads the raw PRM01A4 word. Source
SET BREAK accepts signed0..32767 through native DD9C; FETCH returns all16 bits,
including imported values32768..65535 as negative integers. Reassigning such a
negative result through normal SET is an original range error. A standalone
child without the rendering capability starts with the original350-unit
initializer. CALLs share the script word. CHAIN remains unimplemented.

The policy request carries no child data pointer: parent request4 delivers its
word using checked child callback6. That callback is admitted only during the
synchronous request and only once. Missing/duplicate/unsolicited responses and
closed UART leases fail explicitly. Fresh interpreter initialization resets the
policy latch. Capability1/2 pairs reject before UART admission; distribute the
new parent and child together.

SET changes the child session word. Its normal status tail draws the current
parent row; drawing does not save settings or change the parent's configured
BREAK duration. FETCH uses the real typed destination writer and has no status
refresh. The shared FETCH table reaches the twelve recovered getter paths;
unimplemented selectors stop through explicit stubs. Checked FILE reads stop
truncated selectors/destinations before the native unchecked table access.

## Notice and cleanup

Capability3 request5 brackets the parent's native31BB notice and actual798E/6E78
cursor services. The maintained parent admits a single bracket, with phase0
begin and idempotent phase1 end. It uses a relocated `*** BREAK ***` resource;
the original's pointer0000h is a valid DS:0000 string, not a missing resource.
Native suppression/attribute words retain their actual roles. Unsupported
geometry rejects before drawing. The maintained bracket retains the native15-cell underlay so it can remove the
notice even after abrupt child exit, without reading UART status. The parent
retires a remaining bracket before
revoking the renderer, without calling a retired child callback.

The child restores the cursor before native E67B's normal status refresh. On a
transport/cancel error it explicitly restores the bracket and status before the
nonlocal interpreter abort skips that normal tail. The UART service releases
its own BREAK before either close path drains/restores hardware. Foreign
BREAK/DLAB is rejected. See [transport ownership](ASPECT_BREAK_OWNER.md),
[native recovery](ASPECT_BREAK_NATIVE.md) and [calibration](ASPECT_TXPACE.md).
The parent's Alt-B action retains its separately documented BIOS-tick policy;
its raw configured word is inherited without adopting that different timer.

## Verification

The DOS execution suite passes1147 cases/26330 checks, including SET bounds,
FETCH storage, all twelve source-compiled getter defaults,244 unsupported FETCH selectors,
truncated reads and readiness/error cleanup. A failed initial RXDATA-default
expectation was corrected by tracing the native CF main prologue: its gate is0
inside the frame. The diagnostic BREAK path models readiness only; it is not an
electrical pulse simulator.

Five actual DOSBox-X parent/child cases separately check configured350 and1000,
raw65535 followed by a script override, zero duration and Escape cancellation
during a30000-unit pulse. The passive INT1C observer reads LCR and VRAM, and
qualifies child words by PSP/DS/SS. It observes the native notice, clearing after
assertion, the effective child duration, the unchanged parent word and a closed
notice bracket before the next PAUSE. It also retains the independent query,
keyboard/history, file-handle and hardware/IRQ restoration checks. The first
observer stopped at child exit and missed post-cancel clearing; the corrected
observer continues across return. That failed observation remains under
`build/aspect-break-dos/break-live01`, followed by the passing `break-live02`.

Independent CPU proofs cover all LCR bytes/IF states, native units through65535,
TEMT draining, stopped clocks, midnight, cancellation, overflow, typed policy
lifetime and exact notice/cursor behavior. The separate native FETCH/cursor
proof covers107 bytes/all45 instructions in2399 cases. Parent/child callbacks
also pass the actual DOS lifecycle fixture. A fresh original-free checkout
reproduces138 outputs byte for byte. [Bound validation](validation/aspect-break-runtime.json)
records the final binary identities, source hashes, reports and BBS scope.

These are virtual UART observations, not physical pulse timing or Wi-Fi modem
validation. Existing whole-application gates and the ENiGMA immediate-forwarding
interaction issue remain open. The recorded buffered ENiGMA workflow is a scoped
regression, not a replacement for that issue.

```sh
./tools/build test-aspect-break-native test-aspect-fetch-native
./tools/build test-aspect-break-policy test-aspect-break-ui
./tools/build test-aspect-break-owner test-aspect-break-linked
./tools/build test-aspect-break-dos
```
