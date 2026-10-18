# Recovered save/restore cursor services

`reconstruction/cursor_state/core.asm` reconstructs the original PCPlus 2.01
services at CS:dd74 and ddbc. Its flat build reproduces **144 bytes** through
de03h, including two original alignment NOPs. The source-only OMF build links
these instructions with the actual recovered screen cursor services. It reads
no original executable, installation, or generated analysis database.

`provenance.json` records original image SHA-256, file offsets 92708 and 92780,
individual 72-byte region hashes, REA assembly Evidence IDs and all state aliases.
Names are analyst annotations, not recovered original symbols.

## Integration ABI

Assemble with `-DCURSOR_STATE_OMF` and the shared UART include directory. Exports:

- `csi_save_cursor(word mode)` saves current row and column. With mode zero it
  also saves eight terminal-state words. Any nonzero mode saves position only.
- `csi_restore_cursor(word mode)` restores position by calling the existing
  `screen_set_cursor` with AX=row and DX=column. With mode zero it then restores
  those same eight terminal-state words; nonzero mode restores position only.

Both entries are near, **caller cleanup** of the one argument word. BP is
preserved. The linked screen path preserves SI/DI; AX/BX/CX/DX/ES and flags may
be clobbered. Use the shared small-model DS=SS invariant. No new rendering,
attribute recalculation, or charset callbacks are invented.

Supply the ordinary recovered screen services and the word state below:

| Live original DS | Live alias | Saved original DS | Saved alias |
| --- | --- | --- | --- |
| 399c | `screen_cursor_row` | 334e | `csi_saved_row` |
| 399e | `screen_cursor_column` | 3350 | `csi_saved_column` |
| cdf0 | `ansi_charset_g1_flag_graphics` | cc96 | `cursor_state_saved_cdf0` |
| cdec | `ansi_charset_g0_flag_graphics` | cc48 | `cursor_state_saved_cdec` |
| cdfc | `cursor_state_value_cdfc` | cbb0 | `cursor_state_saved_cdfc` |
| ce04 | `cursor_state_value_ce04` | cbb4 | `cursor_state_saved_ce04` |
| 1f70 | `attributes_current` | cdd4 | `cursor_state_saved_1f70` |
| 1d20 | `cursor_state_value_1d20` | cd24 | `cursor_state_saved_1d20` |
| cdd2 | `csi_origin_mode` | cd2c | `cursor_state_saved_cdd2` |
| 3342 | `csi_wrap_pending` | d110 | `cursor_state_saved_3342` |

The three address-named live values have unresolved broader semantics. They
remain real saved/restored words, rather than guessed callback implementations.
This routine does not save every charset or attribute-related flag: for example,
G0/G1 `flag_a` and the separately maintained bold/blink/reverse flags are not
copied by these original instructions. Broader terminal-state consistency must
be understood from their producers and the original renderer before changing
that behavior.

The original ESC entry calls these with mode zero for ESC `7`/`8`. Integrating
CSI `s`/`u` must retain the argument values selected by the recovered dispatcher.

## Verification

```sh
./tools/dev --command python3 standalone/build_cursor_state.py
./tools/dev --command python3 standalone/check_cursor_state.py
./tools/dev --command python3 standalone/test_cursor_state_dos.py
```

The build checks both original-region hashes and links `CSTATE.EXE`. Three CPU
regression groups execute actual linked save/restore and screen instructions:
full/position-only modes including ffffh, caller cleanup and register preservation,
all eight saved words, actual buffer-offset updates, BIOS cursor calls, and
repeated edge/middle-position round trips. The host deliberately traps unresolved
optional viewport/attribute-boundary/wrap services; ordinary tested geometry
uses the actual BIOS cursor path without invoking those boundaries.

The DOS self-check moves the actual emulated cursor, saves/restores position and
an attribute word, and reads the restored BIOS cursor position using INT 10h
AH=03h. It verifies row 10/column 20 before returning a successful DOS errorlevel.
This establishes DOSBox-X execution, not physical adapter or DOS machine testing.

Optional local original comparison:

```sh
./tools/dev --command python3 standalone/check_cursor_state_original.py \
  --original /path/to/PCPLUS-main-2.01.EXE
```

**48 comparisons passed**, covering both entrypoints, modes zero/one/ffffh and
eight deterministic randomized state sets per combination. It compares all
relevant state words and BIOS cursor calls while running the actual original
resident/overlay instructions against the linked source instructions. This
optional test requires ignored original/overlay analysis artifacts; normal
builds and source-only tests do not. Results with exact executable identities
are under `build/cursor-state/` and `build/cursor-state-dos/`.

The combined CSI diagnostic now links these real exports. Its ESC `7`/`8`
aliases tail-jump into the recovered routines without disturbing the caller's
mode argument, and the actual dispatcher selects mode one for CSI `s`/`u`.
Persistent combined-parser tests verify all eight state words restore for ESC
`7`/`8`, remain unchanged for CSI `s`/`u`, and both paths restore cursor position,
BIOS coordinates and video/attribute offsets. The combined DOS self-check also
runs both actual parser paths and reads back the restored BIOS cursor position.
Attribute rendering, charset producers, optional screen dependencies and physical
hardware validation remain separate work.
