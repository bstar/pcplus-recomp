# Large-screen SETUP/profile return

Confirmed SETUP changes between supported terminal profiles4 and6 retain the
accepted25/28/43/50-row text height after a source-built PRMEDIT child returns.
The existing profile transaction stages keyboard input before committing, then
refreshes RIS defaults, palette, keyboard and content. No ordinary product-code
change was needed: the new evidence exercises its composition with the full-height
PROGRAM owner rather than assuming independent component checks establish it.

The ordinary image remains SHA256
`e05186fee47c9ae0273dbe692d337d9cf7500202694709209a577e69d9faf59b`.
This is an internal component candidate, not a deployment selection. The separate
`--profile-display-probe` requires `--program-display-owner`, implies the startup
display diagnostic and is rejected by application packaging. It executes the real
SETUP/PROGRAM/EXEC/confirmation routines through a diagnostic adapter; the normal
main loop and ordinary line-switch command are outside this DOS test.

## Evidence

The machine-readable [receipt](validation/large-profile-return.json) binds exact
images, manifests, checkers, raw results and source-only rebuilds.

-60 linked CPU inputs execute the actual parent instructions with declared BIOS,
 DOS file/kernel and UART boundaries.48 cases repeatedly adopt6→4→6 at all four
 physical heights, both status states and default/explicit keyboard policies.
 They verify coherent canonical/RIS dimensions, home cursor, cleared content,
 retained status and history, keyboard staging, subsequent RIS/DA and released
 leases.12 N/Esc/Enter declines retain the entire parent frame and profile.
-16 DOS observations run the actual source-built PRMEDIT via real EXEC in
 DOSBox-X8086 mode:6→4→6 at four heights in each of the normal and exclusive-output
 workflows. BIOS-enqueued PgDown/Home/Delete/profile/F10/Escape keys edit and
 save the child, then Y confirms adoption in the parent. Independent captures
 check child exit0, profile identity, physical/canonical height, blank logical
 content, retained physical status row, selected948-byte keyboard and released
 leases. Status is visible in these DOS cases. Final synthetic PRM bytes are
 unchanged after the round trips;42-byte UART/PIC/vector snapshots restore,
 the virtual peer receives no serial output and diagnostic packaging refuses.
-The extracted shared PROGRAM boundary model retains all57 previous return and
 fault checks. These include pending UART data and tracked-online model cases;
 they do not imply live peer traffic during the actual DOS profile diagnostic.
-The ordinary and diagnostic terminal reproduce byte-identically from569/571
 declared public sources; PRMEDIT reproduces from30. Fresh trees contain no
 original binaries/settings and cannot access ancestor Git. All builds use
 the pinned Nix toolchain.

The synthetic PRM fixture explicitly supplies valid mouse scales. An initial
fixture with zero scales was correctly rejected before profile adoption; it was
corrected instead of weakening validation. The editor uses the custom IRQ variant
to preserve the synthetic COM3/IRQ5 selection while saving unrelated fields.
`build_setup.py --output-dir` permits an isolated editor build without replacing
an existing accepted artifact; default output locations retain their behavior.

## Reproduce

Use the receipt's exact terminal flags with `./tools/dev --command python
standalone/build_terminal.py ... --output-dir build/NEW`. Build the editor with
`./tools/dev --command python standalone/build_setup.py --mouse --notice-sound
--custom-irq --output-dir build/NEWEDITOR`. Output directories must be new.

Run `standalone/check_large_profile_live.py --terminal PATH --output build/NEW`
and `standalone/check_program_display_live.py --terminal PATH --output build/NEW`
inside the pinned environment against the ordinary image. Run
`standalone/test_display_rows_terminal_dos.py --terminal DIAGNOSTIC --editor
PRMEDIT --output build/NEW` for the separate actual DOS acceptance. The terminal
source-rebuild helper is `standalone/prove_terminal_variant.py`; its exact flags
and result hashes are in the receipt.

## Remaining acceptance

XLT, ASPECT adoption, other fixed-height modal owners and broader emulation/profile
coverage remain open before enabling normal Ctrl-- and startup display preferences.
These tests are not Enigma/Synchronet session, analog/SIP, arbitrary VGA font,
physical keyboard or hardware acceptance. Source-code availability and scoped
passing tests do not establish complete original PCPlus parity. No physical
machine/card, private settings/call history, selected package, installed bridge
service or deployed application changed.
