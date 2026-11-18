# ASPECT local screen commands

The opt-in capability27 profile compiles and executes BOX, CLEAR, HOME, LOCATE,
SCROLL, GETVATTR and PUTVATTR through the source-built interpreter and the
admitted parent display owner. The normal application build remains source
only. Original binaries and retained REA analysis are optional comparison
inputs, never application inputs.

The current full products are `build/screen-parent-v6-20261119`,
`build/screen-child-overlay-v4-20261119` and
`build/screen-compiler-v2-20261118`. This is an integration checkpoint; complete
connection-package qualification and physical acceptance are separate gates.
The installed DOS selector and private configuration remain unchanged.

| Command | Native operation |
| --- | --- |
| `box row1 col1 row2 col2 attr` | BIOS rectangle clear, then the recovered native frame kernel |
| `clear [attr]` | Clear the canonical rectangle, reset current attribute and home to the configured origin |
| `home` | Set row/column zero, with the native conditional attribute-boundary branch |
| `locate row col` | Native cursor/cache update, including canonical wide-screen panning |
| `scroll count row1 col1 row2 col2 attr` | Native BIOS rectangle scroll; count zero clears |
| `getvattr row col destination` | Read a physical video attribute into a writable integer destination |
| `putvattr row col attr` | Write a physical video attribute, preserving its character |

Screen operands use the recovered atomic integer grammar. They are not arbitrary
arithmetic expressions. The compiler also recovers the general writable N0–N9
bank, including assignment, expressions and procedure parameters; N01, N001 and
N10 retain ordinary-name behavior. The EMULATE selector is separate from N0.

Physical video operations include the status row. Their address is the native
low WORD of `row * physical_stride + 2 * column + 1`, independent of the logical
cursor and horizontal pane. LOCATE alone accepts columns through131 when the
canonical132-column profile is active. Other coordinate readers retain physical
bounds. CLEAR with an attribute changes configured normal and current values;
without an attribute it retains normal and still resets current.

The initialized native frame is the double border
`C9 CD BB BA BC CD C8 BA`. Runtime frame-style/PRM selection is not recovered.
BOX does not gain a new ordering or nondegeneracy guard: zero and reversed
rectangles retain native wrapped loop counts. The instruction model covers the
complete64KiB ES offset space, but writes outside the visible VGA aperture are
not physical-hardware qualification.

## Native provenance and ownership

[The provenance ledger](../reconstruction/aspect_screen_commands/provenance.json)
binds ten newly recovered instruction units,220 bytes, to original addresses,
digests and retained REA Evidence IDs. HOME reuses resident1F56. The native
checker also executes630 bytes of reused helper dependencies. The source-only
and optional-original runs each pass133442 CPU cases. BIOS, DOS and device
behavior in component checks remains explicitly modeled.

The seven resident interpreter entries enter the screen overlay. Four operand
readers and the abort/wire/admission bridges stay resident. The scalar client,
C adapter and exact native handlers share overlay section5; linker-resolved
internal calls avoid reentering the overlay loader. Errors transfer to resident
CS before the ordinary typed-abort chain.

The parent uses authenticated operations32–36: metadata, primitive begin,
sequential WORD arguments, commit and cancel. It validates current owners and
geometry and retires staged operations before calling native helpers. This
local scope temporarily activates the parser policy and restores it afterward;
screen primitives do not feed receive/parser history. Unrelated authenticated
operations, END, prepare, revoke and typed abort retire staged state. The outer
PROGRAM/compiler-loan refusal can retain staging until a later cancel/end/revoke;
component checks preserve that distinction.

The screen overlay is1016 bytes. Near code is65508 bytes, leaving28; DGROUP is
40640 and the stack remains8192. Exact minimum DOS allocation including PSP is
126640 bytes; conservative page accounting is126848. These are separate
measures. Current successful full8086 cases grow the near heap to41906 without
reducing buffers, stacks or environment size.

## Execution evidence

The original compiler observations freeze1394 distinct fixtures:1173 screen
cases and221 numeric-register cases. Both maintained compilers match557 accepted
outputs and837 refusals. The ordinary4670-case compiler regression and existing
Host/compiler checks remain separate from this opt-in application profile.

`build/screen-full-reused-v1-20261119/result.json` passes five actual emulated
DOS8086 cases and254 checks: ordinary execution, source startup, source EXECUTE,
bad physical row and bad attribute. Every success executes all seven commands,
checks native BOX/SCROLL pixel snapshots, status-row31→46→31 attributes,
LOCATE/HOME, optional/default CLEAR, N0–N9 and EMULATE separation, owned FILEs
and the full inherited GET assertions. Source EXECUTE repeats the family in its
replacement script. The two operand failures preserve the destination/video
byte and exit through resident code with native error1/runtime error7.

The passive observer reuses otherwise idle admission-snapshot storage. A
separate executable CPU check proves that original failure capture replaces all
3538 snapshot bytes and256 BDA bytes, and that added writers cannot overwrite
that failure evidence. It removes resident observer allocation without changing
application memory or waiving the original checks. Earlier larger-observer
failures remain retained negative receipts.

`build/screen-base-source-lease-v3-20261119/checks.json` separately passes both
baseline source workflows with the existing clock, terminal, HITKEY and state
probes. `build/screen-when-v3-20261119/checks.json` passes the plain/framed WHEN
regression, two cases and82 checks. These do not imply script execution within
a live modal GET field.

The client aggregate `build/screen-client-capacity-20261119/result.json` binds
six passing DOS client suites, default-profile byte identity for the admission
refactor, and measured placement. The parent platform and RPC checks separately
cover native helper ABI, authenticated ownership, geometry, metadata, staging
and retirement. The default renderer policy remains byte-identical; the opt-in
policy adds coherent physical status-row cursor handling while preserving the
logical scroll rectangle and4096-cell plane limit.

## Remaining boundaries

The canonical132-column run at
`build/screen-wide-dos-v6-compact-20261119/result.json` passes58 checks over seven
passive milestones. Peer CSI?3h/3l activates and retires the wide profile through
the real parser; LOCATE pans52 columns, raw physical attributes remain independent
of the pane, HOME repans left, and owned FILE/GET/UART checks remain active. Its
separate observer-priority replay passes two cases/six checks.

Nested Help, held FILEs, frame restoration and handles also pass63 checks with
the existing386/upper-memory observer recipe, at
`build/notice-help/screen-help-v3-20261119/result.json`. A richer conventional
8086 Help observer timed out before child entry and remains a negative diagnostic;
this is not a successful8086 nested-Help claim.

The parent-refusal/nonlocal-unwind path followed by overlay reuse, complete
source-export replay and the final connection package are tracked as additional
integration gates. Component checks alone do not close them.

The maintained profile initializes `screen_attribute_checks` to zero and reset
clears it. Native HOME's checked branch is component-tested, but its real profile
producer is not linked. Retained original overlay13:F59E enables it and F5C2
disables it; ECD2's token26 arm calls F59E. Evidence IDs are
`ev_f6cd43c0efbc9a215618d5f2d2bb4df8e3675c3b99564b21b5592cf25297b202`,
`ev_3595d0cbb43110faa9e6224d35037ca51cea98ffffee1977a658b42df5ada861`
and `ev_4bca6fda2fa059463560f718d111c872c2dbb78451d82642cec963a85c74465f`.
Outer emulation/profile routing and associated marker-plane initialization need
recovery; setting the flag from a test observer does not establish that path.

Physical VGA/CGA behavior, all supported geometries and configurable frame
styles, full ASPECT, remaining emulations/protocols and [F01–F16](FEATURES.md)
remain open. Host remains last. The broader sequence continues in
[ASPECT_RECOVERY_NEXT.md](ASPECT_RECOVERY_NEXT.md).
