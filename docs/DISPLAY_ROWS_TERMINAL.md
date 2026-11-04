# BIOS row service inside the terminal

`--display-row-owner` links the [verified BIOS row service](DISPLAY_ROWS_DOS.md)
into the current status-owner terminal as an independent DISPLAY_CODE bank.
Its recovered code/data symbols use the private drows_native_ namespace. The
public far-cdecl API uses caller-owned near result storage with DS=SS.

The linker and memory inspector verify that the bank has its own executable CS,
fits that segment, does not overlap other retained code/data/screen storage and
survives PROGRAM retention. The group starts at a nonzero six-byte offset;
admission checks its complete offset-plus-size extent, not an assumed zero base.
All native dependencies and flat-byte digests are explicit build inputs.

| Image | Identity prefix | Resident CS extent / spare | DGROUP |
| --- | --- | --- | --- |
| Existing status component, row bank disabled |3756c6d7 |65386 /150 |65024 |
| Internal component, row bank linked |a1c86342 |65386 /150 |65072 |
| Startup row diagnostic |f302f571 |65396 /140 |65072 |

The1113-byte bank consumes no additional resident code bytes in the ordinary
internal component. Its46-byte private state adds48 aligned DGROUP bytes.
CONFIG_CODE remains58522 bytes in the ordinary component. The build option
does not add a key/menu binding or change canonical terminal geometry; it is
not a replacement package or a completed Toggle Lines command.

## Linked DOS evidence

`--display-row-probe` creates a separate diagnostic image. After normal startup
capture, but before uart_enable or connection_start, it calls the actual banked
far API for probe,25,28,43,50,25 rows. Each of six binary records includes the
returned geometry plus independent BIOS mode/page and BDA row observations.
Canonical CSI rows/bottom/status suppression remain24/23/0 throughout. No
foreground receive/parser service runs while BIOS and canonical geometry differ.
The diagnostic restores BIOS25 before writing its report and ordinary shutdown.

The actual8086 DOSBox-X parent passes both workflows on COM3/3E8/IRQ5:

- Normal run: all six geometries, real cross-bank calls and expected BIOS/BDA
  results match; return0.
- Existing DROWS.BIN: the same BIOS sequence ends with exclusive-create refusal,
  preserves the sentinel file exactly and returns23.

Both workflows preserve the synthetic PRM and executable, produce zero bytes
on the connected virtual serial peer, and restore all42 sampled bytes covering
IRQ0–7 vectors, INT1C, UART configuration/divisor and PIC mask. This proves
ownership restoration, not active UART receive or modem connection handling.
Packaging rejects the diagnostic manifest before creating output storage.

The ordinary linked image also passes the76 status transaction inputs and250
captured-reset-row inputs, including late-renderer rollback and queued UART
continuation in the linked CPU harness. These remain distinct from the startup
DOS row probe. The five-profile standalone426-check BIOS matrix repeats with
the same d226171b diagnostic identity after the bank-only assembly conditional.

All three terminal images reproduce exactly from declared public sources in
fresh trees with ancestor Git unavailable and no original artifacts. The new
ordinary and diagnostic images declare561/563 sources. The disabled image stays
byte-identical3756c6d7. See [bound evidence](validation/display-rows-terminal.json).

```sh
# Add to the existing status-owner build flags:
--display-row-owner
# Separate startup diagnostic; never install/package this as the application:
--display-row-owner --display-row-probe

./tools/dev --command python standalone/test_display_rows_terminal_dos.py \
  --terminal build/DIAGNOSTIC/TERMINAL.EXE --output build/NEW-row-parent
```

## Remaining integration

No normal command invokes the raw BIOS service. A future foreground owner must
preflight frame/history/shadow capacities, retire notices, coordinate all live
and reset geometry, and commit or restore both BIOS and canonical state. Larger
screen loans, configured selector import/cycling, guarded UI, online size/refusal/
disconnect coordination, BBS/package regressions and physical card/modem
acceptance remain open. In particular the current offline status owner still
admits only BIOS80x25; linking a bank does not expand that contract.

No active deployment pointer, ready package, installed configuration, bridge or
live BBS is changed. All13 unavailable reference commands and full application
parity remain open.
