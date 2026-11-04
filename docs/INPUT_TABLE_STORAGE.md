# Input dispatch table storage

The carrier/C0 parent occupied 65,534 bytes of resident CS, leaving only two
bytes for further command recovery. The optional `--input-tables-data` build
moves the existing 30-entry low-control table and 24-entry C1 table to DGROUP.
Their near code pointers still target the same recovered handlers. Two indirect
jumps now use DS instead of a CS override; the existing DS=SS ABI is retained.

This is a maintained storage adaptation, not newly recovered original behavior.
The original flat 288-byte dispatch region remains exact. Default OMF builds
retain the CS tables; rebuilding the current parent's flags without the new
option reproduces its entire executable byte for byte.

| Layout | Resident CS | CS spare | Near data/stack | Near spare |
| --- | ---: | ---: | ---: | ---: |
| Existing carrier/C0 parent | 65,534 | 2 | 65,120 | 416 |
| Optional data tables | 65,424 | 112 | 65,232 | 304 |

The change moves 108 pointer bytes and removes two segment prefixes. Data
alignment accounts for the 112-byte near-group increase. This creates code
capacity; it does not establish lower total memory use or faster execution.
The additional capacity is still small, so larger commands need banked code.

The candidate is `build/input-tables-data-20261104/data/TERMINAL.EXE`, SHA256
`055f56e6412ca8de4446d7af2a37a36e798e23fddd062ac68fccca9c95454b6a`.
An empty, Git-free export of its 570 declared public inputs reproduces it
exactly, without original executables or generated analysis inputs.

The differential CPU replay compares all 256 stream bytes under eight
monochrome/C1/input-mode combinations at three independently padded code/data
placements: 6,144 paired streams. It checks the complete 4,000-byte video page,
history, selected parser/cursor/control state and explicit unsupported-service
results. Segment-size assertions reject an ignored storage option. The normal
diagnostic builder independently verifies the original flat region hashes.
The new application also passes 45 linked C0 cases, 58 carrier/flow cases and
28 transfer-loss cases, including the retained failing pre-drain image.

Fresh authenticated DOS 8086 editor sessions through the staged SynthModem
proxy pass on stock Enigma and Synchronet. Independent raw-wire/cell audits
match all1,920 logical cells and cursor coordinates on each, with NAWS80×24
at25 physical rows and the status bar visible. These checks include normal
exit and hardware restoration; other display layouts and transfer/reconnect
composition on this new image remain separate gates.

The receipt at [validation/input-table-storage.json](validation/input-table-storage.json)
binds these artifacts and the fresh BBS checks. CPU models and loopback DOS
sessions do not establish physical Boca/SPA2102 timing or broad feature parity.
The installed carrier/C0 package remains selected while the storage variant
awaits complete transfer/reconnect composition and package admission.

Reproduce in the pinned toolchain with fresh output paths:

```sh
./tools/dev --command python standalone/build_input_dispatch.py
./tools/dev --command python standalone/check_input_table_storage.py \
  --output build/NEW-input-storage
./tools/dev --command python standalone/prove_terminal_manifest.py \
  --terminal build/input-tables-data-20261104/data/TERMINAL.EXE \
  --output build/NEW-input-storage-source
```

To build the variant, replay the installed parent's manifest options through
`prove_phone_log_startup_terminal.flags()` and add `--input-tables-data` to
`standalone/build_terminal.py`. The manifest records the option and the common
flag converter carries it into source-only rebuilds and package reproduction.
