# Insert/delete lines and alternate-mode wait

`reconstruction/line_edit` recovers504 exact original bytes from overlay12:

| Original CS | Source | Export | Bytes |
|---|---|---|---:|
|d668..d73a|insert_line.asm|csi_insert_line|211|
|d73c..d842|delete_line.asm|csi_delete_line|263|
|daf2..db0f|wait_control_n.asm|csi_wait_control_n|30|

Flat assembly reproduces SHA-pinned original instructions. OMF requires
`-DLINE_EDIT_OMF`; addresses become named linker symbols. Provenance records
original2.01 SHA6401ccfd…7196904, file offsets and region digests, plus saved REA
evidence identifiers. The REA overlay analysis container has its own distinct
digest; it is a static analysis input, never executed. Original file bytes,
not the analysis container, establish the exact comparisons.

## Behavior and integration

The CSI dispatcher repeats `csi_insert_line` for CSI L and ordinarily repeats
`csi_delete_line` for CSI M. Each helper edits **one line** and accepts no count
argument. The count/default/repetition policy remains in the dispatcher.
Both helpers return immediately if DS3734 `screen_attribute_checks` is nonzero.
Otherwise they home the current column to zero and scroll/clear the rectangle
from the current row to DSce3a `screen_last_row`, using the existing recovered
`csi_service_2530`. Equality with DS334a `csi_last_row` chooses a zero-distance
clear. The routine uses current row through bottom; it does not independently
reject a row outside the configured scroll region.

CSI M with DS8ff6 nonzero takes a different branch: `csi_wait_control_n`.
**daf2 is not delete-line code.** It repeatedly calls actual `uart_receive_byte`
until AX000e, otherwise checks `keyboard_peek` and consumes `keyboard_read`.
Only local Escape exits. It has no timeout and discards other received bytes.
This legacy behavior is preserved exactly; a maintained foreground-service,
cancellation or timeout policy must be a separate deliberate implementation.

Line helpers preserve BP,SI,DI; AX,BX,CX,DX,ES and flags are volatile. Near calls,
DS=SS, DF clear. Wait preserves BP; other register effects are inherited from
its called UART/keyboard services. No production callback stubs are supplied.

Shared interfaces are `screen_set_cursor`, `csi_service_2530`,
`erase_previous_attribute`, `erase_scan_attributes`, `erase_move_bytes`, and
`erase_repair_attributes`. State aliases are canonical existing screen/erase/
scroll symbols; `provenance.json` maps every original DS address. The wait
routine only needs `uart_receive_byte`, `keyboard_peek`, `keyboard_read`.

The optional DS900c attribute-plane mode preserves original memory moves and
fills. It hardcodes23 rows when calculating plane-copy lengths, and the delete
routine fills at the configured `erase_cell_count` offset. These are legacy
operations, not newly generalized window bounds. The nontrivial delete repair
branch calls original2d98 `erase_repair_attributes`; that complex renderer
service remains explicitly unresolved in this standalone module. Protected
DS3734 returns, ordinary video operations and simple attribute-plane paths are
fully executable. Arbitrary corrupt pointers, invalid row geometry and unsafe
attribute counts are not validated by the exact recovered instructions.

## Verification

```
./tools/dev --command python3 standalone/build_line_edit.py
./tools/dev --command python3 standalone/check_line_edit.py
./tools/dev --command python3 standalone/check_line_edit.py --original
./tools/dev --command python3 standalone/test_line_edit_dos.py
```

The ordinary build reads source and recorded hashes only. It links real screen,
erase and scroll recovery. The diagnostic declares UART/keyboard value fixtures
for the wait routine; unresolved UI/complex repair services trap visibly.
CPU checks exercise both line directions, full and restricted margins, bottom
row, protected no-op, actual attribute planes, cursor changes and register ABI.
Twelve optional genuine-original comparisons verify video cells, BIOS calls,
cursor and simple plane bytes against the actual original instructions. Wait
checks prove control-N exit, local Escape, consumption of another key and
original indefinite waiting. A nontrivial repair test verifies the explicit
2d98 boundary. Actual DOSBox-X8086 verifies inserted/deleted rows, cleared last
row and unchanged outside rows, using actual emulated video; no physical UART,
real modem, BBS or protected-attribute repair is claimed by that diagnostic.
