# Attribute repair

The resident2D98 field repair,2C3A byte repaint and2CF2 coordinate advance
are recovered as399 exact bytes. `./tools/build test-attribute-repair` builds
flat baselines and relocatable OMF objects from maintained source. Ordinary
builds read neither an original executable nor an analysis database. The
explicit analyst-only recovery script verifies the original SHA-256 separately.

REA Ghidra assembly evidence:

- Repair2D98: `ev_4ab18267a860061b33b0bdd2abff5eebfe38b8a8c31cac2c6c1126d9f006f8cf`.
- Write2C3A: `ev_d63e7b7d265d17bf760c635ad693f9e334d37416eba14e47425126b55ad1281d`.
- Advance2CF2: `ev_4f8f8f3ebcf4e0586108151870cc92586265a163247141a2592b4082c9629a1d`.

Repair returns immediately when cursor wrap is disabled. Mode0 scans the whole
plane and carries stored field attributes through marker boundaries. Mode1
starts at the cursor with the current attribute. Mode2 starts there with the
previous cell's stored attribute (or the native default at cell0). Mode3 keeps
that starting position and previous attribute but switches to mode0 scanning.
Other nonzero mode words follow the mode2 boundary policy.

For nonzero scan modes, starting on a marker repairs that field through its
next marker; starting inside a field stops after repainting the next marker.
Marker cells receive the configured normal/protected display attribute while
their stored value remains intact. Ordinary cells receive the carried attribute
in stored values. A protected cell with flag1 and without flag2 displays the
configured protected foreground combined with the carried upper five bits.
Characters and protection flags are preserved throughout. The cursor stays put.

Repaint uses the recovered6C84 byte writer for visible cells and writes directly
through the supplied far shadow pointer for hidden viewport cells. Native
coordinate descriptors use DS=SS and cache visibility/video offset. Advance
recalculates at the viewport left boundary, physical column count and logical
row rollover. It does not refresh at arbitrary viewport right+1; wide/nonstandard
right edges can retain stale visibility. The existing inactive-left0 unsigned
threshold quirk also remains in the exact native baseline. Both are explicitly
characterized, not silently corrected or claimed as working application modes.

The1928 CPU cases execute all seven real routines: repair, repaint, advance,
position conversion, default attribute, previous attribute and byte writer.
They cover all combinations of the relevant flag bits on two cells, all four
defined modes plus another nonzero mode, wrap enabled/disabled, cursor positions,
full planes up to132x25, cross-row fields, viewport/shadow transitions and CGA
polling. Expected metadata, value guards, video and shadow buffers are compared
in full; stack cleanup, BP/SI/DI preservation and DS=SS are checked. ES is scratch
in the native writer. Only the CGA status port is modeled; this is not physical
video or timing validation.

The application now binds2D98 through a resident RET2 bridge and checked far
entry in ASPECT_CODE, with near/far adapters to real resident default, previous
and byte-video services. Read-only admission requires fixed80-column geometry,
bounded logical height and real metadata/value backing. Modes using the cursor
also require consistent cursor/video/attribute offsets. Whole-plane mode0
deliberately ignores cursor offsets: native wrap changes the column before
scrolling and updates those offsets afterward. Wrap-disabled repair retains
the native no-op behavior even with otherwise unsupported geometry.

The925 linked cases compare metadata/value guards and video through the actual
application bridges, including39 scroll, wrapping and repeated parser/keyboard
delete consumers and12 key rejection cases before any wire/cursor/parser/plane
change. This removes the earlier blanket rejection of marker deletion
and reverse-Tab paths requiring scroll repair. Invalid backing and suppressed
wrapping remain explicit keyboard failures before output. The630 reverse-Tab,
55 native key-edit,837 scalar key and existing parser regressions remain
separate checks. Real DOS keyboard/BBS tests cover the integrated product;
the detailed protected-field comparisons are CPU replay with modeled hardware.

Native scroll metadata shifts the entire logical plane even when its BIOS
video rectangle uses smaller margins. That original behavior is characterized,
not presented as region-matched metadata semantics. The line-edit helpers have
additional fixed row constants and still retain their existing wrap-state
rejection pending separate evaluation. All whole-application gates, complete
viewport ownership and physical modem validation remain open. See the
[validation record](validation/attribute-repair.json).
