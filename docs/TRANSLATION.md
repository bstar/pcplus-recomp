# XLT translation recovery and checked DOS loader

The selected PCPlus 2.01 uses a headerless256-byte table. Entry `n` is the
replacement byte for input byte `n`; NUL, SUB, FF and repeated output values
are valid data. This checkpoint recovers file operations, identity reset and
one receive helper, and supplies a separate checked DOS loader. The interactive
terminal now supports explicit `/X:FILE.XLT`; see [live translation](LIVE_TRANSLATION.md).

## Recovered behavior

The original is SHA-256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Resident CS offsets below map to original file offset `0x1200 + CS offset`.
DS state names are analyst annotations.

| Original location | Observed behavior |
| --- | --- |
| DS324e | Near pointer to `PCPLUS.XLT`, initialized in startup-data overlay32. The filename begins at DS1b6f, original file offset274bfh. |
| DSd00a..d109 | One256-byte mapping table; distinct from renderer glyph/font tables. |
| 35a6..35d7 | Save: resolve name, fopen with DS4720 (`wb`), fwrite(table,1,256,file), fclose. |
| 35d7..3608 | Load: resolve name, fopen with DS4723 (`rb`), fread(table,1,256,file), fclose. |
| 3608..3616 | Fill all256 entries with their own byte indices. |
| 0566, specifically05a8..05b9 | Main receive loop reads aa65, indexes the table, zero-extends the mapped byte and calls terminal dispatch0610. |
| 4c74..4cb4 | Optional immediate aa65 or timed5ca0 read; negative return passes through without indexing. Nonnegative input maps before optional script logging and optional dispatch. Script callback is callee-clean; dispatcher is caller-clean. Helper returns mapped byte and RET4. |
| 5ca0..5cce | Timed parser continuation reads aa65 directly when ready. This routine contains no XLT lookup. |
| Overlay3, def8..df1a | Identity reset, receive mask8e22=ff; selection word1d64 equal1 loads XLT; equal2 selects receive mask7f instead. Remaining selection values retain identity/ff in this owner. |

The main loop and helper prove mappings can change terminal control bytes before
dispatch. They do not prove that every receive consumer translates. In particular,
adding translation to the parser continuation routine would change the observed
native boundary. Unread rewinds the raw RX ring; any maintained mapping must leave
that ring unchanged.

Both native file routines ignore fopen, transfer and close failures. The native
loader requests256 bytes without checking the file length: a short read leaves
the old table suffix, and trailing bytes remain unread. Controlled CRT-boundary
tests establish these call and mutation behaviors; they do not execute a genuine
CRT with a null FILE pointer or claim that such a call is safe.

## Maintained loader

`src/translation/xlt_dos.c` exposes `xlt_dos_read(path,destination,result)` using
DOS binary handle reads and small-model near cdecl. It accepts explicit paths
of1..63 bytes and exactly256 arbitrary table bytes. It handles fragmented reads,
checks EOF with a one-byte probe, closes once after successful open, and commits
the staged table only after successful close. On failure the destination stays
unchanged; primary read errors and secondary close errors are reported separately.
Invalid or overlapping/wrapping caller extents perform no I/O. The result pointer
is optional and remains untouched on argument rejection.

Rejecting short/trailing files and checking all errors are intentional maintained
differences. This loader does not search the environment, select a configuration
mode, write files, lock concurrent writers or alter the live UART/parser.

## Validation

Run through the pinned Nix environment:

```sh
./tools/build test-translation test-translation-dos
./tools/dev --command python3 standalone/check_translation.py --original
./tools/dev --command python3 standalone/prove_translation_source_build.py
```

The first command builds176 byte-exact recovered instructions as flat units and
relocatable OMF objects from source alone, then executes2,082 8086 CPU cases.
The optional second command verifies the original SHA and byte ranges and repeats
all2,082 cases using actual original instructions. It is not an application build
input. CPU tests cover all256 values, wait/script/dispatch combinations, negative
read results, table guards, identity reset, partial/trailing reads, unchecked open,
short-write and close-return behavior, register preservation and stack cleanup.
CRT, receive, script and dispatch are explicit controlled boundaries.

The checked loader separately passes nine actual DOS filesystem checks and22
declared DOS API fault/argument checks in DOSBox-X using an8086 CPU. Synthetic
fixtures include all256 byte values, an allzero nonbijective table, missing files,
five wrong lengths and48 successive rejected reads followed by a valid load.
The fault executable covers fragmented reads, handle0, read/probe/close errors,
error precedence, aliases, pointer wrap and optional result storage. Input files
remain byte-identical. See `validation/translation-native.json` and
`validation/translation-dos.json` for source and binary identities.

The isolated build copies only eleven declared source/provenance files into a
new temporary tree with no analysis directory or original artifacts. Its CPU
and DOS checks pass and six flat/OMF/DOS outputs reproduce byte-identically;
see `validation/translation-source-build.json`. Checkout-relative assembler
input names keep absolute paths out of OMF module headers. This proof covers
the XLT checkpoint only; it does not expand the earlier whole-terminal proof.

These standalone checks do not establish live terminal behavior; separate live
checks are documented in `LIVE_TRANSLATION.md`. Actual hardware, the full
translation editor, other emulations and complete reconstruction remain open.

## REA evidence and mapping limits

The original resident REA loader leaves these indirectly reached functions
undefined. Static synthetic overlay3 images add entry anchors to discover them;
they are never executed. The image used for the following assembly has SHA-256
`46c5a45c3a654b3059b73182332f698f9ab119314010c18edd9ca7fa181ce879`.
It copies verified resident bytes, active overlays1/3 and startup data32, replaces
overlay trampolines, and changes five synthetic far-call anchor targets. The
existing ignored `prepare_overlay_analysis.py` and saved entry manifest describe
these substitutions. Recovered flat bytes are separately compared against the
genuine original; synthetic call edges are not runtime or original callers.

| Observation | REA Evidence ID |
| --- | --- |
| Original resident source mappings | `ev_e64adede842cb5581a5caa88c7267b5fe09e200a2aa6cbcc31d7beee9f04e6ab` |
| Original resident pointer references324e | `ev_6aea9b5dfb1caa93b54c4ee9fe993b382e67b34d7434d85850d74ac218e54aa7` |
| Original native bytes at35a6 | `ev_ce6f69167a3b492ca5400544f1230fdfbb3b4e08ea631cf544c7bb747e60c364` |
| Save35a6, earlier synthetic image5b91b8cb | `ev_74527c74cce230ad18971a3796e87c3c6e4adb6c2e7567fdffe5adf188e192e3` |
| Load35d7 | `ev_bd83366d60f16eed685688c4a6ed37630b252e28a690394bd01085147b87d0f2` |
| Identity3608 | `ev_899d99d0ae59e35316637b9f7ee1c3ceb7623ba8830fdc96b3f5e4dab2ca4837` |
| Main receive0566 | `ev_5446486dc4042e1716d69d14f8715789b709588ed6f73c873b8fd63a8c4a936d` |
| Receive helper4c74 | `ev_7351891973c993c7668f722c09ba787f8e0c061d57192aec3f2945c44523d123` |
| Raw continuation5ca0 | `ev_861ae207bb7f834d6cd318ff78aa17b5c49445bf5dc70093e6448f73d28dbb2a` |
| Overlay3 selection ownerdef8 | `ev_b0a4d765907fddac1272d78c72eb1b69437991cd13a8e1bd5be06da3e5b9977f` |

## Original editor and save invocation

Additional REA inspection binds overlay31's static entry-anchor image to SHA-256
`221471c855310d6cc21eb48639606dfc3e7b51d5535069ff836c4c8b77203958`.
The code overlay itself is2,208 bytes at original file offset250a0h, loaded at
CSd0d0; its SHA is `9e8e24ae3968ea2810a68b0a6d530c7efaa81bfd7bcd4d290ec15979a189ecdc`.
These are static observations; neither synthetic image is executed.

- Editor entryd662..d93a retains a page base, dirty flag and saved screen.
  Digit input opens decimal source/replacement prompts. Source indices must lie
  within the current0..127 or128..255 page; replacement values are0..255.
  It writes a single byte at DSd00a+source and highlights nonidentity entries.
- F1 (3b00) calls the save ownerd94c. F2 (3c00) toggles page base0/128.
  F3 (3d00) optionally offers to save dirty changes, sets selection1d64=1,
  then reloads through35d7 and returns to the first page. F4 (3e00) sets
  selection0 and restores identity. Escape exits; selection0 restores identity
  again. A complete interactive cancel/dirty policy has not been reconstructed.
- Display helperd602..d662 renders128 source/replacement pairs as eight groups
  of16 rows. Save ownerd94c..d963 calls a status helperd93a and6bb6, then35a6,
  and clears the caller's dirty word without checking whether the write worked.
  A maintained editor must retain dirty state on failure.

Evidence IDs: editor `ev_3b67a42048b6055cdd22853e4e8248dd014b51b523d979381ce723313fadace7`,
save owner `ev_09cd68c427796534677c8a1cd6ce58fb828e30fcf0e1450fdff09ce59e3d9e26`,
display `ev_62d1b3b7cdb5cc4b6127b03239df29d1592f202bb1263e7691e6443911c96e05`.

## Remaining work

The maintained offline [XLTEDIT editor](XLT_EDITOR.md) now provides table editing,
checked persistence and explicit dirty state. It deliberately leaves parent PRM
mode changes separate. Saved selection1d64 now participates in validated startup and settings
transactions, including the7-bit alternative and explicit live deferral. Live
mode changes now use [confirmed staged adoption](LIVE_TRANSLATION_SETUP.md).
[Explicit same-table reload](TRANSLATION_RELOAD.md) is now available through
Alt-F9 or the menu. Dedicated live editor invocation remains open. Bounded default-table
[PCPLUS environment fallback](RESOURCE_LOOKUP.md) is now integrated; lookup
for the other resources remains open. Resolve remaining
emulation/script consumers. Explicit startup selection, normal mapping, raw
monitor/continuation and capture/RIS boundaries now have separate live tests;
full settings/UI and physical UART/modem testing remain open. Integration must
continue to respect the near-code/data segment budgets.
