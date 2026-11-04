# Large-screen translation editor and reload return

The existing translation editor and explicit reload compose with the full-height
PROGRAM owner at25/28/43/50 physical rows. The original-reference build launches
the editor with Alt-W; Alt-F8 belongs to key mapping. An older maintained-keys test
used Alt-F8 and was not evidence for this original-reference candidate.

No ordinary product-code change was required. Its executable remains byte-identical
to the preceding PROGRAM/profile checkpoints:
`e05186fee47c9ae0273dbe692d337d9cf7500202694709209a577e69d9faf59b`.
The new `--xlt-display-probe` is a startup diagnostic requiring the PROGRAM owner.
It is mutually exclusive with the profile diagnostic and cannot be packaged as
an application. Nothing here selects or deploys a new physical-machine build.

## Checked behavior

The [receipt](validation/large-xlt-return.json) binds exact images/manifests,
raw results, checkers and source-only rebuilds.

-96 linked CPU inputs run real Alt-W/Alt-F9 scheduling, PROGRAM ownership,
 direct editor argument construction, file reading, confirmation, table commit
 and restored receive/TX processing. They cover four heights, visible/hidden
 status, editor/reload, default/fallback/explicit selected tables and accept/
 decline.20 further cases cover EXEC failure and short/failed-close reads at
 each height. Actual product instructions execute; DOS, child, BIOS and UART
 boundaries are modeled. The full physical frame/cursor, canonical/RIS state,
 keymap, history and metadata are preserved. A mapped L is rendered as X after
 acceptance, and keyboard L still transmits raw L. Declines/failures retain L.
-16 actual DOSBox-X8086 observations run the source-built XLTEDIT child via real
 EXEC, save its selected table and confirm in the parent. At each of the four
 heights the editor changes byte0 to88 and then back to0, in each of the normal
 and exclusive-output workflows. BIOS-enqueued editing/F1/Escape/Y keys drive
 these cases. Independent before/after frame and256-byte table captures verify
 full parent restoration, accepted table, physical/canonical dimensions, released
 leases and child exit0. Final synthetic disk table is identity, the PRM is
 unchanged, no replacement remnants remain, the virtual serial peer receives no
 bytes and the42-byte UART/PIC/vector snapshot restores. This startup diagnostic
 invokes the actual editor owner through an adapter, not normal Alt-W dispatch
 or the main receive loop; those dispatch/receive paths are checked separately
 in the CPU tests.
-Ordinary/diagnostic terminal rebuilds from569/571 declared public source files
 reproduce exactly, as does XLTEDIT from12 files. Fresh source trees exclude
 original binaries, private configuration and ancestor Git; builds use pinned Nix.

The editor intentionally saves a25-row UI prefix. The parent PROGRAM lease
preserves all accepted rows and restores the height after the parent temporarily
uses mode3 for a readable confirmation prompt. Comparing video memory beyond the
physical frame would incorrectly require preservation of off-screen unused rows;
checks compare exactly the accepted physical frame.

## Reproduce

Build the terminal with the receipt's exact flags through `./tools/dev --command
python standalone/build_terminal.py ... --output-dir build/NEW`. Add
`--xlt-display-probe` only for the diagnostic. The ordinary image stays unchanged.

Build the editor with `./tools/dev --command python standalone/build_xlt_editor.py
--output-dir build/NEWEDITOR`; the optional isolated output avoids overwriting
an accepted editor. Default build output behavior is retained.

Within the same pinned environment run `standalone/check_large_xlt_live.py
--terminal ORDINARY --output build/NEW` and
`standalone/test_display_rows_terminal_dos.py --terminal DIAGNOSTIC --xlt-editor
XLTEDIT --output build/NEW`. The latter places the terminal and editor together
in an isolated application directory so the real DOS3 environment trailer and
sibling-executable lookup are exercised. It keeps the selected table on the
separate synthetic data drive. All output directories must be new.

## Remaining work

ASPECT renderer admission currently explicitly limits BIOS/canonical rows to25
(`src/aspect/renderer_policy.c`). It must be composed with the larger-row owner,
including SAVE/NOCLEAR nested PROGRAM, script windows and live input, before
normal Ctrl-- and startup preferences can be enabled. Other fixed-height modal
owners, broader profiles/emulations and complete original parity remain open.

This checkpoint does not establish live Enigma/Synchronet, SIP/analog, arbitrary
VGA fonts or physical input acceptance. No installed bridge, physical card,
private settings/call history or deployed application changed.
