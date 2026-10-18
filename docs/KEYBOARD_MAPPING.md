# Terminal key mapping

The recovered original emitter, optional local echo wrapper, helper/dispatcher
body and calibrated delay total **1,869 exact bytes**. The separate DS44e0
indirect dispatch table has141 near pointers (282 bytes). `provenance.json`
pins every flat-region digest to the PCPlus2.01 original SHA6401ccfd…7196904.
`recover.py` is an explicit analyst operation requiring the ignored original;
ordinary builds consume only the assembly and recorded hashes.

REA exports establish the dispatcher/emitter/control flow. Ghidra left some
indirect helper instructions undefined; REA confirmed the original address to
file-offset mapping, and SHA-verified original bytes were independently decoded
with ndisasm. An undefined Listing entry is not evidence of absent code.

## Classifier ABIs

`classifier.asm` is maintained source derived from the proved original branches.
It exports `keyboard_classify`: AX is the **keyboard_read_extended normalized**
word. Returns AX0..78 for a binding slot,0100|byte for a literal, FFFE for a
known local/application service boundary, FFFF for unmapped input. BP,SI,DI,ES
are preserved; BX,CX,DX,flags are volatile. It makes no I/O or callbacks.

It owns zero-default word `keyboard_mapping_scrollback_mode` (originalDS1d74),
word `keyboard_mapping_hook_enabled` (DS1d6e) and byte
`keyboard_mapping_hook_character` (DS1d70). Enabled matching hotkeys take
precedence over ordinary nonzero-AL translation and return FFFE. The original
signed-byte comparison is retained. Raw queued AX8 is literal8; BIOS0e08 is
Backspace slot10. ASCII Escape is literal27. The existing normalized entry is
retained unchanged for compatibility, but the application can use the original
`keyboard_read` path with **`keyboard_classify_raw`** from
`raw_classifier.asm`. That entry has exactly the same result/register ABI and
reuses the normalized common scan/ASCII branches. It additionally needs the
canonical `terminal_keymap` symbol; it adds no state and makes no callbacks.
It covers every79slot including the raw enhanced and numeric keypad banks.
Aliases1ce0/35e0 are not recognized by the original dispatcher, so any support
for those words must be an explicitly maintained compatibility layer.

| Key | Slot |
|---|---:|
| Tab / ShiftTab |6 /7|
| Insert / Delete |8 /9|
| Backspace / CtrlBackspace |10 /15|
| CtrlHome / CtrlEnd |11 /12|
| PgUp / PgDn |13 /14|
| F1..F10 / F11..F12 |16..25 /26..27|
| ShiftF1..F10 / ShiftF11..F12 |38..47 /48..49|
| CtrlF1..F10 / CtrlF11..F12 |60..69 /70..71|
| Up / Down / Left / Right |72 /73 /74 /75|
| Home / End / Enter |76 /77 /78|

The raw additional banks are:

| Raw key words | Slots |
|---|---|
|372a multiply /4a2d subtract /4e2b add /532e decimal /e02f divide /e00d keypadEnter|0 /1 /2 /3 /4 /5|
|5230,4f31,5032,5133,4b34,4c35,4d36,4737,4838,4939 (numeric0..9)|28..37|
|48e0 Up /50e0 Down /4be0 Left /4de0 Right|50 /51 /52 /53|
|52e0 Insert /53e0 Delete /47e0 Home /4fe0 End|54 /55 /56 /57|
|49e0 PgUp /51e0 PgDn|58 /59, only if selected slot first byte is nonzero|

Empty raw enhanced PgUp/PgDn bindings return FFFE for the original local
scrollback fallback. These checks inspect the actual profile-selected table;
they do not use the scrollback preference flag. Raw73e0/74e0 are local actions.
Enhanced and legacy arrow banks need separate binding contents; DECCKM searches
all matching slot strings. No terminal profile flag gate appears in the raw
keypad branches themselves.

PgUp/PgDn emit slots only with DS1d74 zero; otherwise local scrollback.
CtrlPgUp/CtrlPgDn reverse that policy. Alt1..Alt0 dispatch KEY records0..9,
not the F-key slots. AltF1..F8 are local services; AltF9 is a no-op; AltF10
has a conditional local branch. AltF11/F12 are no-ops. CtrlInsert/Delete lie
beyond the original scan-table limit8c. Ctrl-\\, Ctrl-], Ctrl-_ are local UI.

## Binding data and unresolved application services

The KBD table is79 fixed12-byte slots at DS3378. The selected profile changes
the loaded block, not these slot indices. A slot ends at NUL; stored FF emits
wire00, with original DS1d68 pacing after each byte. The original emitter has
no slot-length bound; the live application must keep its separate bounded
queue sender. Exact original pacing remains blocking and unlinked from live
transport. Original helper/UI callbacks have explicit address-based interfaces;
the standalone diagnostic traps unresolved services. It is not a complete UI.

Historical per-profile4VT220/6ANSI defaults remain unproved without a pristine
companion KBD. Source-owned modern network defaults must be labeled maintained.
DECCKM rewrites every matching ESC[A..D string in all79 slots; the four arrow
slots alone do not define that search.

KEY macros use a separate mechanism: original47b6 dispatches kinds0ASPECT,
1PROGRAM,2HOOK,3TEXT; TEXT48cc calls caret parser4934, handles configured pause
DS1d66 with nine BIOS ticks, FF as NUL, optional local echo and pacing. This
macro engine is not implemented by the pure classifier. It is incorrect to
apply these macro transformations to KBD slot strings.

## Verification

```
./tools/dev --command python3 standalone/build_keyboard_mapping.py
./tools/dev --command python3 standalone/check_keyboard_mapping.py
./tools/dev --command python3 standalone/check_keyboard_mapping.py --original
./tools/dev --command python3 standalone/check_keyboard_mapping_raw.py --original
./tools/dev --command python3 standalone/test_keyboard_mapping_dos.py
```

The build checks1,869 recovered flat bytes and assembles relocatable OMF,
including all named unresolved interfaces. CPU tests exercise345 actual linked
classifier cases and the recovered FF-to-NUL emitter with an explicit recording
UART callee fixture. Optional614 three-way comparisons verify the pure result
against both the actual OMF dispatcher and genuine SHA-pinned original
instructions, under both scrollback policies. Only status-observer boundaries
are bypassed; local scrollback is observed at its service boundary. No original
synthetic analysis executable is launched. Raw tests independently compare632 combinations of all79keys, profiles4/6,
scrollback modes and enhanced-PgUp/PgDn binding availability against both the
recovered OMF dispatcher and genuine original instructions. DOS diagnostic
runs83 raw classifier vectors covering all79slots and the real emitter under an8086 DOSBox-X process, using the declared
recording UART fixture, not serial hardware or a BBS.
