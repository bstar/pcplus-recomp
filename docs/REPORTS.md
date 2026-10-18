# Recovered terminal reports

`reconstruction/reports/core.asm` contains the actual PCPlus 2.01 primary
attributes and device-status routines. Flat builds reproduce CS:dd58..dd73 and
CS:de04..de97 exactly: **176 bytes** total. `provenance.json` retains original
image identity, file offsets, region hashes and REA assembly Evidence IDs.
Normal source-only builds read no original image or analysis database.

OMF mode uses explicit linker symbols. `src/reports/decimal.asm` supplies a
maintained signed 16-bit decimal conversion implementation, and
`src/reports/data.asm` supplies the public protocol strings and profile table.
These sources replace dependencies; they are not claimed as recovered original
runtime source or original data layout. Their report output was compared with
the actual original instructions and UART writes.

## Integration ABI

Assemble the core with `-DREPORTS_OMF` and the shared UART include directory.
Link `src/reports/decimal.asm` and `src/reports/data.asm`.

- `csi_device_status()` and `csi_primary_attributes()` are near no-argument
  entries. Their original instructions may clobber AX/BX/CX/DX/flags.
- `csi_transmit_byte(word)` sends the low byte; `csi_transmit_string(near_pointer)`
  sends a NUL-terminated DS string. Both are **callee cleanup, RET 2**. Supply
  actual output services in the application; the dedicated test host captures
  bytes in memory instead.
- `csi_report_decimal(value, near_buffer, base)` has caller cleanup of six bytes
  and returns the near buffer pointer in AX. Maintained implementation supports
  base 10, signed 16-bit values including -32768, requires seven buffer bytes,
  and preserves BP/SI/DI. A non-10 base produces an empty string. Only base 10 is
  called by the recovered reporting code. DS must equal SS.

The host owns `ansi_parameters`, `ansi_private`, `screen_cursor_row`,
`screen_cursor_column`, `csi_origin_row`, `csi_terminal_id`,
`csi_report_private_prefix` and `csi_printer_ready`, all words.
The data unit owns `csi_report_buffer`, `csi_attributes_table` and the protocol
string symbols declared by the recovered core. It does not redefine host state.

## Observed replies

| Request/state | Output |
| --- | --- |
| Parameter 5 | ESC `[0n` |
| Parameter 6 | ESC `[` row `;` column `R` |
| Parameter 6 with both original DS:904c and private flag nonzero | ESC `[0;` row `;` column `R` |
| Parameter 15, original DS:3984 nonzero | ESC `[?10n` |
| Parameter 15, original DS:3984 zero | ESC `[?13n` |
| Other parameters | No output |

Row is signed 16-bit `(screen_cursor_row - csi_origin_row + 1)` and column is
signed 16-bit `(screen_cursor_column + 1)`, including original wrap behavior.
The `csi_printer_ready` and `csi_report_private_prefix` names annotate these
observed branches; peripheral detection and mode selection are outside this
unit. No `attributes_monochrome` reference exists in these two original routines.

Primary attributes output is ESC `[?` plus the selected table string plus `c`:

| Original terminal ID | Payload |
| --- | --- |
| 2, 6, 7, 10 | `1;2` |
| 3 | `6` |
| 4, 11 | `62;2` |
| 5 | `63;2` |
| 8 | `1;0` |
| 9 | `7;5;1` |

Only IDs 2..11 are supported by the reconstructed table. Original IDs 0/1 have
null pointers into unrelated DS:0 content; the maintained data unit substitutes
empty placeholders for those two unsupported entries. Values above 11 are
outside the table. The application must validate/configure its terminal ID;
no new bounds guard is silently inserted into the exact recovered routine.

## Verification and limits

```sh
./tools/dev --command python3 standalone/build_reports.py
./tools/dev --command python3 standalone/check_reports.py
./tools/dev --command python3 standalone/test_reports_dos.py
```

The build checks both baseline hashes, then links a DOS MZ with actual report
instructions and maintained formatter. Four CPU regression groups check ordinary
status/cursor/printer reports, private/origin behavior, signed decimal and wrap
bounds, and every supported device-attribute profile. The decimal test includes
512 deterministic random values plus signed and decimal boundaries. DOSBox-X
runs a status-report self-check and verifies DOS exit status. These use captured
output, not a physical UART or live BBS.

Optional local-original comparison:

```sh
./tools/dev --command python3 standalone/check_reports_original.py \
  --original /path/to/PCPLUS-main-2.01.EXE
```

This verifies original image identity, reuses the ignored local overlay manifest,
loads real original instructions into the CPU emulator, records original UART
writes, and compares them with source-built report output. **182 comparisons
passed**, covering requests 0..16, private/printer flag variants, all ten supported
DA profiles, coordinate boundaries and 64 deterministic random coordinate triples
in both private-prefix modes. It requires original/overlay artifacts locally;
normal builds and source-only tests do not. Results, including executable hashes,
are in `build/reports/` and `build/reports-dos/`.

The real reporting functions are also linked into the combined CSI diagnostic;
parser-driven status, cursor and primary-attribute queries pass with captured
output. Connecting output services to the rebuilt UART remains work in progress.
Public BBS and physical modem validation
remain separate requirements.
