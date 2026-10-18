# Terminal support services

Four recovered routines provide 273 original bytes, independently assembled in
flat mode and linked into the combined source-only CSI diagnostic:

| Entry | Export | ABI and behavior |
| --- | --- | --- |
| 0b4e | `terminal_keyboard_mode` | One caller-cleanup word: prefix byte. With DEC keys enabled, rewrite matching three-byte arrow bindings ending A/B/C/D, switching the second byte between `[` and `O`. |
| 246c | `csi_clear_tabs` | One caller-cleanup word: zero removes the current-column stop, one initializes eight-column stops, other nonzero values clear all stops. |
| 24e2 | `terminal_clear_home` | No arguments. Clear the full configured screen using the normal attribute, reset current attributes and position at origin row, column zero. |
| 250a | `csi_reset_scroll_region` | No arguments. Set scroll top to zero and bottom to the configured last row. |

DS must equal SS and the direction flag must be clear. Names are analyst
annotations. Flat mode preserves exact original instructions; OMF uses linker
symbols, including immediate pointers, key-table end comparisons and tab-table
indexing. `provenance.json` records each original range and digest.

## Key mapping and interaction

The original routine searches 79 twelve-byte binding slots, not just four
fixed arrow slots. It rewrites only exact three-byte arrow strings. Custom
bindings and longer strings remain unchanged. This is a live key-table rewrite;
it does not load a KBD file, establish factory bindings or transmit keys itself.
The diagnostic supplies synthetic bindings. A terminal application still needs
the key dispatch/transmit path and configuration loader.

`terminal_keymap_end` and `terminal_mode_372c` share the original DS372c boundary
immediately after the 948-byte table. The mode word's full meaning remains
unresolved; do not infer capture or insert semantics merely from its address.
The table at DSce10 has thirty byte entries and FE terminators. The ce11 operand
is an alias at base+1, not separately allocated state.

Tab initialization assumes a valid screen width; tests cover 0, 1, 8, 80 and
132 columns. Original initialization has no bounds guard for corrupt widths
requiring more than thirty stops. Tab deletion assumes a properly terminated
table. These invariants are not validated by the original helper itself.

## Verification

```
./tools/build test-terminal-services
./tools/build test-csi
```

The support test assembles every flat unit and checks its recorded size/digest,
then executes the linked instructions. It checks all four arrow suffixes,
first/last slots, custom and longer bindings, disabled DEC rewriting, tab reset
and actual CSI g/0g/3g deletion, CSI scroll-region resets, and real clear/home
instructions through the BIOS video model. Unrelated video cells and table
boundaries are checked. The combined DOS executable also verifies a real arrow
rewrite, tab reset and clear/home in DOSBox-X, using actual BIOS screen services.

Retained REA/Ghidra assembly IDs are in
`evidence/terminal-services/rea-index.json`. Keyboard-mode evidence is
`ev_e45c15025904c0fc2bf6ac5c76a3773b1782478a3ac891c01ac8550449616d78`;
tab handling is
`ev_85224615a81654601a90f59cac12f56cd330ed19a3f01e8c27730e232a4cff4f`.
The two short reset helpers were decoded directly from verified original byte
ranges with NDISASM; no individual retained REA function record is claimed.
The explicit `recover.py` analyst step requires the local original. Normal
builds and tests do not read original artifacts.

No physical modem or public BBS interaction was tested by these fixtures.
