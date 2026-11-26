# ANSI-family terminal profiles and DEC Special Graphics (2026-11-25)

Two opt-in parent features move F04 (terminal emulations) toward PCPlus 2.01
parity for host software that expects a VT100-class terminal:

- `--ansi-profiles` (`TERMINAL_ANSI_PROFILES`) admits terminal ids 2 VT100,
  3 VT102, 5 VT320, 7 IBM PC, 8 WYSE 75, 9 ATT 605, 10 ATT 4410 and
  11 TVI 922 alongside the existing 4 VT220 and 6 ANSI.
- `--dec-graphics` (`TERMINAL_DEC_GRAPHICS`) renders `ESC(0`/`ESC)0` DEC
  Special Graphics with the recovered CP437 glyph map instead of identity.

Without either flag every object is unchanged. The qualified parent still
rebuilds as `7f5b3b03…` and the default minimal parent as `e25e0bd7…`.

## Why these ids are safe to admit

- **One parser.** The recovered dispatch table
  (`reconstruction/input_dispatch/tables.asm`) sends ids 2..11 to the same
  `ansi_escape_entry`. Ids 0, 1 and 12+ use separate native parsers, which are
  still `csi_unimplemented` stubs.
- **Same reset state.** The recovered reset
  (`reconstruction/terminal_reset/reset.asm` L_20c0..L_2284) sets every
  per-id flag identically for 2..11, with one exception:
  `attributes_monochrome` is set for 6..7.
  - 2, 3, 5 and 8..11 therefore equal VT220's state.
  - 7 equals ANSI's state.

  `src/terminal/configuration.asm` now sets monochrome for 6..7 under the flag.
- **Only replies and labels differ.**
  - Primary DA comes from the recovered table in `src/reports/data.asm`.
  - Secondary DA comes from the native L_e9ec branch: ids 4 and 11 give
    `1;10;0`, id 5 gives `24;10;0`, id 9 gives `4`, and every other id
    gives no parameters. The branch is recovered code, so no maintained
    table is involved.
  - The status label is already in `reset_data_299c`.
- **Same keyboard handling.** Keyboard files are read per id by
  `keymap_dos_read`. The built-in network keymap is id-independent.
- **Ids 8..11 audit.** Every read of `csi_terminal_id` (DS 1d18) in the
  original was checked. For 8..11 the only per-id behaviour is:
  - the primary DA (8 `1;0`, 9 `7;5;1`, 10 `1;2`, 11 `62;2`);
  - the secondary-DA branch above;
  - the reset flags (doublewidth and DEC keys, no monochrome);
  - the per-id keyboard-file record (`0x3b4 × id`);
  - the status label.

  There is no other parser, renderer or report difference, so 8..11 are
  admitted on the same footing as 2/3/5/7.

## Gates widened

All gates use `src/config/terminal_profile.h` (C) or
`src/terminal/terminal_profile.inc` (NASM). Without the flag, both expand to
the historical `!=4 && !=6` and `je/jne` sequences.

- **Startup and live configuration:** `terminal_import.c`, `live_configuration.c`, `hook_input.c`, `setup_model.c`.
- **Directory resources:** `directory_resources.c`, `directory_resource_cli.c`.
- **Reset and profile staging:** `terminal_reset.asm` capture, `setup_profile.asm` staging, `script_emulate.asm` (ASPECT EMULATE).
- **Display and status:** `window_size_report.asm`, `viewport_live.asm`, `reset_live.asm`, `status_transition.c`, `row_geometry.c`, `renderer_policy.c`.

Two of these sources are built outside the main object list, so the bank
builders also take the flag:

- `src/process/display_rows_link.py` compiles `row_geometry.c` for the display
  bank.
- `src/ui/native_reset_link.py` assembles `reset_live.asm` for the reset
  transaction bank.

Before this was fixed, the full parent's display-startup transaction still used
the narrow gate. Admitted ids 2/3/5/7 then stopped at startup with service
`2EAA`.

The startup refusal text keeps its 53-byte length because DGROUP is full at
65520 bytes in the full parent: "Terminal profile must be an ANSI-family id
(2 to 11)." Under the flag the setup editor's profile field accepts 2..11,
and its 41-byte hint reads "ANSI-family ID 2-11: 4 VT220, 6 ANSI, etc". The four C sources in the size profile had their reviewed source
hashes refreshed in `standalone/terminal_size_profile.json` and
`src/chat/echo_size.json`. Their code is unchanged without the flag.

## DEC Special Graphics

The renderer (`reconstruction/render/character.asm` L_07d3..L_07e9) reads
`render_graphics_map` only for characters 5Fh..7Eh, and only while the active
G0 or G1 set is graphics. The maintained table was identity, so BBS menus drawn
with `lqqk`/`x`/`mqqj` appeared as letters.

The 32 reachable bytes now match the original's DS:459b+5Fh table. That table
was verified inside the startup data block whose SHA-256 is
`41b5e49c3f2bc40b7007d311af4282d9724b4cf0b11a696ca2bd6062ef4132c7`, the same
block `reconstruction/input_dispatch/recover.py` checks. It maps:

- the corners, tees, cross and bars to CP437 single-line box drawing;
- 6F..73 (scan lines) to C4;
- the symbols degree, ±, ≤, ≥, π and £;
- `_` to blank and `~` to F9;
- b/c/d/e/h/i to the letters T/F/C/L/N/V, as the original does.

The table is written as source constants. The build reads no original input.

## Actual DOS evidence

The tests run `standalone/test_ansi_profiles_dos.py` in DOSBox-X with an 8086
CPU and no FPU. The setup is:

- actual COM1 UART with a synthetic modem peer and configured init/dial;
- after a typed byte, the peer sends a BBS-style screen: SGR, DEC line drawing,
  a scroll region, DECSC/DECRC, EL and CUP;
- then primary DA, secondary DA and CPR queries.

| Parent | Profiles online | Profiles refused (exit 7, message, no modem traffic) |
| --- | --- | --- |
| minimal, `--ansi-profiles --dec-graphics` `c162ea2d` | 2, 8, 9, 10, 11 | 0, 1, 12 |
| full qualified flag set + `--ansi-profiles --dec-graphics --vt52` `f82fcb05` | 2, 8, 9, 10, 11 | 0, 1, 12 |
| earlier 2..7 builds: minimal `bee295fe`, full `44665668` | 2, 3, 4, 5, 6, 7 | 0, 1, 8, 11 |
| minimal default `e25e0bd7` | 4, 6 (line drawing stays identity) | 2, 3, 5, 7 |
| qualified full parent `7f5b3b03` | 4, 6 (line drawing stays identity) | 2, 3, 5, 7 |

Each online case checks:

- the per-id primary DA, twice (banner and query) and no other DA;
- the per-id secondary DA, exactly once;
- CPR `10;36` after the menu prompt;
- the scroll-region result rows;
- the line-drawing rows;
- hardware restoration, configured init/dial/hangup and unchanged PRM/binary.

The 24 drawn rows hash identically in every online case of a build class:

- `5a54ecf9f041…` for every DEC-graphics case (both parents, all ids);
- `1e580dc3157e…` for the four identity-map cases.

Status rows show the recovered labels (`WYSE 75`, `ATT 605`, `ATT 4410`,
`TVI 922`). With `--vt52`, the full parent also passes the VT52 switch from
id 9 and the stay case from id 11.

Results are in `build/ansi-profiles-dos/`. The full flag-set build is DS/SS
65520.

The fixture sets the PRM display, mouse and sound words that the full parent
imports:

- display: `1c2/1c8/1ca/4ec` = 0, 2, 25, 0;
- mouse scales: `4e4/4e6` = 8, 4;
- sound: `1bc/1be/1e6` = 0.

Without them, the fixture's `A5A5` sentinel makes the qualified parent's display
startup stop with service `2EAA` ("Unsupported terminal function"). That is a
fixture requirement, not a parent defect. The minimal parent ignores these
words.

## Open

- VT52 (id 1) as a runtime sub-mode via DECANM `ESC[?2l` is restored by the
  opt-in `--vt52` flag; see `VT52.md`. TTY (id 0) still ignores ESC, as in
  the original.
- Native WYSE 75 / ATT / TVI keyboard layouts come only from a per-id
  keyboard file, as in the original. The built-in network keymap is the same
  for every id.
- The SCO/DECSCL `ESC[=…p`-style switch to id 2 is handled by the recovered
  parser. The maintained RIS snapshot restores the configured id, except with
  `--vt52`, whose profile-switch reset keeps id 2 (`VT52.md`).
- No physical terminal, modem or BBS deployment acceptance.
