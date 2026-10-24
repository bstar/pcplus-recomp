# Protected erase and overlapping panes

The application restores the native protected erase helper reached through
resident trampoline `d05f`: overlay13, `f47c..f509`,142 bytes. Its flat source
assembles to `5806cb8aa0223436fde3ba46f966693d2f28602a286fc46d41825130fec6f2c0`. Ordinary builds check that identity without reading
an original executable. Explicit analyst recovery verifies original file offset
98604 against original SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.

REA dossier `ev_fdfc6216a1a29af2a940ed59bbce4f838dad18ef0f88f942ae636260f900fa79` identifies the helper and its four calls:
position conversion, character write, descriptor advance and mode3 attribute
repair. The dossier uses the static-only synthetic overlay13 image
`227a1b107f6981145550039916c0d264f50f8c46e432920b2df2216e1e15f85b`.
Original helper bytes are independently checked; the synthetic image is never
executed or deployed. Decompiler pseudocode is evidence rather than source.

The native line form stops at a metadata byte with bits81 set. The display form
skips those cells and continues through the remaining display. Erased cells
become spaces; the configured protection mode can mark them. Native mode3
repair recomputes subsequent field attributes. Marker bytes and protected
characters are not treated as an invented modern selective-erase protocol.

## Maintained integration

The original helper instructions remain unchanged. Checked caller-cleaned
adapters validate geometry, both metadata planes, DS=SS and execution flags.
The application projects EL2's temporary column home into its logical metadata
offset, then restores the cached offset when the native dispatcher restores the
actual column. This applies to color-field and monochrome erase paths.
A CS-owned projection flag permits bounded plane repair while the temporary
column is outside the current visible pane. The helper uses native descriptors
for hidden and visible output; it does not switch panes to draw.

The monochrome branch of the original display-after routine bypasses the marker
scan but later tests its uninitialized scan-result local. The application-only
build initializes that local to zero. This removes dependence on stale parent
or ASPECT stack contents. The standalone recovered flat routine is unchanged.

Wide count-zero rectangle clearing also needed a separate bounded owner.
The original rectangle assumes disjoint panes: a range ending in the overlapping
52..79 columns can underflow the hidden fill count. The application now fills
only the requested logical rectangle and its intersection with the selected
physical pane. It preserves cursor/pane caches, metadata and status rows, with
the native multi-row line-flag clearing policy. Counted scrolling retains its
existing owner. Narrow clears retain their native video implementation.

ASPECT command admission can now permit protected ED/EL. The existing guarded
resident bridge, serial owner, per-byte admission and parser budgets remain in
force. Font-provider configurations still reject separately.

## Validation

The [validation receipt](validation/protected-erase.json) binds the initially
build-free source reconstruction at `build/protected-erase-source-02`. Four
application products, both ASPECT runners, the compiler and CSI rebuild exactly
without original binaries or REA databases. The earlier attempt stopped at a
stale CSI source manifest, before rebuilding; it is not an accepted proof.

Each transaction parent passes288 direct cases and72 parser forms, covering
both widths/panes/profiles,1/5/24/25 rows, color-field and monochrome branches,
marking/stopping/skipping semantics, exact logical pixels/metadata and canaries.
Eight invalid states refuse before mutation. Four foreground UART-interrupt
cases additionally test pending serial input during native erase/projection.

The independent wide-clear model covers896 rectangles and five invalid boxes,
including overlap boundaries52/79/80, single and multiple rows, plain/wrapped
output, both profiles/panes, line flags and visible/hidden status.
All16 new DOS8086 erase workflows pass across color-field/monochrome modes,
visible/hidden status, open/closed script windows and source/precompiled scripts.
The eight precompiled cases compare complete logical screen and metadata
planes; the eight source cases require exact DOS-compiled ASX plus geometry,
replies, child return and keyboard resumption using the compact observer.
The existing eight ASPECT, eight field/local-view and five nested compiler
workflows also pass, together with the prior field/scroll/ownership regressions.

The erase sequence intentionally removes the startup banner. For these cases,
the shared harness's final-screen banner check is replaced by the initial
cursor-position reply arriving before SCRIPTREADY. Passive service-code capture
also requires zero unsupported-service faults. Earlier DOS pilots exposed a
whole-line terminal stop and the monochrome/control mismatch before the offset
and initialization fixes; only the completed clean-source runs are accepted.

Physical modem/BBS acceptance, peer-requested width, other unsupported field
modes and complete application parity remain open. No card deployment is implied.
