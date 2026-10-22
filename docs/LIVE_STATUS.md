# Live parent status service

Current parent4dae4ddb adds ordinary main-loop carrier refresh to the native
status renderer. [Independent validation](validation/parent-carrier-status.json)
binds64 keyboard/mouse linked groups, the earlier parent's actual DOS failure
and corrected passive captures. Initial-high DCD is sampled before automatic
script scheduling, so loss inside the child is recognized on return. An inactive
parent uses the normal help label without requiring a script basename. Explicit
STATUS invalidates cached visibility, including low/high-script/low transitions.

The ordinary poll samples at most once per BIOS tick and defers program, parser,
ANSI wait, monitor, snapshot, printer, transfer, redisplay, menu and hidden or
unsupported layout owners. A stack-only15-cell notice copy preserves live text
and updates the saved underlay. Supported ordinary geometry is80 columns with
the native bottom status row. DS=SS data spare is112/64 bytes and resident-code
spare244/94 for normal/mouse variants. DCD initially low with a complete later
rise/fall inside a child, other geometries and physical hardware remain open.
The following measurements describe the earlier frozen status checkpoint.

SET WHENCASE now refreshes the connected terminal's status row through an
admitted ASPECT child. The parent stages its actual line format, rate, profile,
duplex, script basename and hidden state, then executes the recovered status
body through the existing far formatter and resident text services. Drawing
does not commit session settings. The STATUS operation carries only a scalar
duplex projection: FFFF selects parent state; byte values select a temporary
projection. Child pointers and FILE objects never enter this operation.

The 48-byte ASIOv4 descriptor is unchanged in size. Its renderer capability is
now version2; version1 is rejected rather than silently accepting an operation
it cannot provide. Raw v1/v2/v3 handoffs retain their existing behavior. The
maintained raw-only and diagnostic WHENCASE paths retain their prior policy;
they have no resident status consumer.

STATUS uses the existing checked parent stack and client/PSP/DS admission. It
requires the live UART phase on both sides. Post-close diagnostic EMIT retains
its separate lifetime. Before drawing or reading MSR, state staging checks the
80-column row geometry, profile table bound, normal layout, exact supported
baud, parity/data/stop fields and a bounded script basename. Rejection is typed.
The carrier service executes the actual native UART MSR read, including its
delta-bit clearing behavior; physical DCD has not been validated here.

The shared owned resources are in `src/status/status_state.inc`; the live
stager is `src/terminal/status_live.asm`. Fixed resources and dynamic snapshots
use64704 bytes of the DS=SS group, leaving832 bytes. Resident code uses65128
bytes, leaving408; most status code lives in CONFIG_CODE. ASPECT_CODE now has
explicit paragraph alignment, removing its earlier accidental dependence on
the preceding segment's size. Five status near/far bridge pairs, relocations,
argument cleanup and label extent are checked in the linked product.

Validation for the frozen products is recorded in
[validation/live-status.json](validation/live-status.json):

- 85 linked staging/drawing cases cover two profiles, nine rates, all supported
  line formats, duplex projections, hidden state and invalid-input rejection.
  Only UART input is modeled; DOS/BIOS interrupts are forbidden in this proof.
- [Four actual DOS scenarios](ASPECT_STATUS_DOS.md) pass152 checks, including
  all81 native row cells, attributes, actual child PAUSE sampling and unchanged
  parent owners. Emulated carrier labels are declared before execution.
- Client checks cover47 inputs in16 groups, including closed-phase rejection;
  parent admission covers22 cases, and five actual DOS callback cases pass.
- Eight existing full-terminal WHEN cases pass315 checks. The diagnostic
  runtime passes825 DOS cases and18298 checks.
- Actual local Synchronet and ENiGMA login/editor regressions pass, with draft
  abort/no saved post. ENiGMA still requires explicit30ms modem buffering for
  this tested workflow; immediate-forwarding Home/Insert behavior is unresolved.
- A fresh public-source checkout reproduces112 outputs without originals,
  installed configurations, REA databases or previous build artifacts.

The earlier capability1 test fixtures and the incorrectly mixed VT220/ANSI
directory fixture remain in ignored attempt history. Their corrections did not
relax the product admission or rendered-row expectations.

The alternate key-label layout exists in the standalone component but lacks a
live key-label owner, so the application service rejects that layout. Live
renderer admission remains limited to its supported ANSI/VT220 owners. The
other ten compiler-emitted SET settings still need their native225-byte handler
integration, deliberate shared-state lifetimes and nonzero TXPACE service.
Complete UI, scripting/recorder, other profiles/protocols, Host and hardware
validation remain open. This checkpoint closes no whole-application gate.

Run the linked check after building the terminal:

```sh
./tools/build test-status-live
```

Actual DOS repeats need fresh labels and explicit product hashes; see
[ASPECT_STATUS_DOS.md](ASPECT_STATUS_DOS.md).
