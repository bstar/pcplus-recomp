# Attribute-boundary navigation

The complete resident2ADC boundary scanner,2B86 position conversion,2BDE
offset conversion and830C signed division are recovered as316 exact bytes.
Their flat baselines and OMF objects build from maintained source through
`./tools/build test-attribute-boundary`, without an original or analysis database.
The analyst-only recovery command separately verifies the original's SHA-256.

The scanner accepts an attribute-plane offset and direction as two stack words
and returns with RET4. A cell without mask81 returns AX0 without moving. A
flagged cell searches backward for direction0 and forward otherwise, wrapping
within the configured cell count. Finding a different unflagged cell returns
AX1 and positions the cursor. An entirely flagged plane requests a notice,
homes the cursor and returns AX0. Coordinate conversion and signed division
execute as real recovered code; their temporary structures use DS=SS.

REA assembly evidence is retained in the provenance file:

- Boundary: `ev_d75dd65a13553e4742db7f30d1a50dfe3d14b2e666f686d77d058c9a76a83e4e`.
- Position: `ev_087aa230ed995ec3a6e3e060ea79a3e8edd7592fffb7562f95cebf07eb8eb152`.
- Offset: `ev_d4fdefeb3b5c08083bf2f27decd2646661bb907dce848db9102c617bd60a71f1`.
- Divide: `ev_b7e2aee6447f1486f524d08b70ed8284a1df9872fffb6b89775e635353848ae6`.

The718 component cases execute all four routines with recording cursor/notice
boundaries. They cover circular searches, mask combinations, all-flagged planes,
register/stack cleanup and viewport coordinate conversion. The original
inactive-viewport conversion with left0 wraps its comparison threshold toFFFF
and classifies every column as hidden; this behavior is characterized rather
than silently corrected in the recovered baseline. Application viewport
ownership remains unfinished.

The live application now binds the scanner through a resident near-call bridge
and checked far entry. Native keyboard and boundary code share ASPECT_CODE;
near proxies call the real resident cursor routines through far bridges. The
original scanner's RET4 and AX0/1 contract are preserved. Geometry admission
requires a consistent80-column,1..25-row B800 plane, valid metadata backing,
bounded offsets and supported margins. Unsupported calls retain the2ADC
application error. Keyboard admission occurs before wire/echo effects.

The no-writable-cell notice uses the existing maintained BIOS bell provider,
with general and segment registers preserved across firmware. This is an
explicit difference from original376D/774E PIT tone timing and configuration;
full original audio/settings behavior remains open.

The linked630-case keyboard replay executes the real scanner, coordinate,
division, protected-home and resident cursor helpers. Only BIOS/CRT hardware is
modeled, including notice firmware that clobbers registers. See
[reverse Tab](KEYBOARD_REVERSE_TAB.md) and the shared keyboard validation for
the DOS and modern-BBS checks. [Native attribute repair2D98](ATTRIBUTE_REPAIR.md)
now runs through checked application bridges. General viewport services,
line-edit metadata ownership, physical video/audio and all application gates
remain open.

The [validation record](validation/attribute-boundary.json) binds the component,
linked routines and segment sizes to the clean source-only product rebuild.
