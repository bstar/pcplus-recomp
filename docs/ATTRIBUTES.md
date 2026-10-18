# Recovered terminal attributes

The maintained source now contains the actual PCPlus 2.01 normal, bold,
underline, blink and reverse helpers. `reconstruction/attributes/core.asm`
recovers resident offsets `1c8c..1d87` (252 bytes); `reset.asm` recovers
`24da..24e0` (7 bytes). Flat assembly exactly matches the verified original
SHA-256 `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
These are resident module offsets; original file offsets add `1200` hex and
REA's resident linear addresses add `10000` hex. No original executable is
needed to build or test this module.

Run using the pinned Nix development environment:

```sh
./tools/dev --command python3 standalone/build_attributes.py
./tools/dev --command python3 standalone/check_attributes.py
./tools/dev --command python3 standalone/test_attributes_dos.py
```

The output `build/attributes/ATTRIB.EXE` is a source-only DOS self-test. It
asserts normal, bold, blink, reverse, repeated reverse and reset behavior in
DOSBox-X. Linked-instruction Unicorn tests additionally check all 256 byte
attribute reverse inputs, all 256 default nibble transform inputs, configured
preset/underline paths and monochrome/color-mode branches.

## Integration ABI

Build both recovered source files with `-DATTRIBUTES_OMF`, and provide the
following DS symbols. Each is a word except the reverse latch. Helpers take
no arguments, return near, and may clobber AX/BX/CX/DX and flags. Reverse
preserves BP and DI. The caller supplies a valid stack; DS=SS is compatible
with the project's common real-mode ABI.

| Original DS offset | OMF symbol | Meaning inferred from instructions |
| --- | --- | --- |
| `1d32` | `attributes_normal_value` | configured normal attribute |
| `1d34` | `attributes_bold_value` | configured bold preset |
| `1d36` | `attributes_preset_value` | additional preset |
| `1d38` | `attributes_reverse_value` | configured reverse preset |
| `1d3a` | `attributes_underline_value` | configured underline preset |
| `1f70` | `attributes_current` | current attribute word |
| `321c` | `attributes_reverse_active` | reverse latch, **byte** |
| `397c` | `attributes_bold_active` | bold latch |
| `397e` | `attributes_blink_active` | blink latch |
| `8ff6` | `attributes_monochrome` | selects hardcoded 07/01/70 overrides |
| `d122` | `attributes_color_mode` | selects nibble operations vs presets |

| Original CS offset | Export |
| --- | --- |
| `1c8c` | `attributes_normal` |
| `1caa` | `attributes_preset` |
| `1cb2` | `attributes_bold` |
| `1cce` | `attributes_underline` |
| `1ce4` | `attributes_blink` |
| `1cf0` | `attributes_reverse` |
| `1d6c` | `attributes_default_transform` |
| `24da` | `attributes_reset` |

Normal resets bold/blink/reverse latches and restores the configured value,
with a monochrome override. Reset alone restores the configured value and
leaves latches alone. In color mode bold and blink set bits 3 and 7.
Reverse swaps foreground/background color bits while preserving intensity and
blink; repeated calls are suppressed by its latch in color mode. In preset
mode reverse loads the configured reverse attribute and preserves intensity
and blink from the prior value. These are recovered behaviors, not newly
selected modern SGR semantics. No new SGR 22/24/25/27 behavior is implied.

## Evidence and limits

`provenance.json` records exact region hashes. The explicit analyst-only
`recover.py` verifies original identity, decodes every instruction, checks each
encoding and verifies the assembled complete regions. It must never become a
normal build dependency. `docs/evidence/attributes/rea-index.json` identifies
retained REA/Ghidra assembly evidence already present in the local analysis.
Small helpers omitted by that inventory were recovered directly from verified
original instruction ranges with NDISASM; the index explicitly distinguishes
those from REA-covered functions. No new REA session was needed or opened.
Names and mode interpretations are analyst annotations. The diagnostic supplies
representative configuration values, and does not reconstruct original startup
configuration or render a terminal screen. Full terminal integration remains
required.
