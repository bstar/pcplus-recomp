# Original key-mapping helper caller

The original2.01 caller at CS:145A is now rebuilt as78 exact instruction bytes,
with a relocatable OMF form and a source-built DOS diagnostic. This is the
launcher component, not the PCKEYMAP editor or a new terminal command.
[The receipt](validation/keymap-launcher.json) records612 modeled CPU cases,
eight linked8086 DOS ABI cases and exact reproduction from five public source
files without originals or ancestor Git metadata.

REA Evidence `ev_bc822c737da0f500794a19a65784f194e4d51b6ff57576c3d0711fbc8baf6004`
contains the complete37-instruction body for source SHA256 `6401ccfd…`.
The original adjacent data literals are `%d %s` and `PCKEYMAP.EXE`. The caller
passes the current profile word and keyboard filename to the formatter, saves
the screen handle, resolves/invokes the helper, restores the screen and reloads
the keyboard table. Formatter, screen, lookup, PROGRAM and loader behavior are
external boundaries; the current tests explicitly model all six services.

The screen restore at CS:4870 ends in `RET 4`, corroborated by retained REA
Evidence `ev_96965061d48282dbba8fc0b1083bac343af45d1c86376b2955f2dcfc245bded3`.
It consumes the two-word handle arguments. Treating the decompiler's generic
C labels as the calling convention would leave the stack wrong. The linked
diagnostic checks BP/SI/SP, argument order, opaque/null screen handles, failed
lookup/modeled PROGRAM outcomes and the final reload result. Static linkage
also verifies six DGROUP data references, six near calls and all remaining
opcodes against the flat form. A128-byte pad makes the tested data-group offset
nonzero.

The CPU comparison uses33 profile IDs plusFFFF and synthetic filenames. Its
formatter is a declared model, not execution of the native CRT. Twenty bytes
below entry SP is the caller/model boundary depth, not a claim about the real
callees' stack or heap use. Original instructions and the rebuilt flat caller
produce the same boundary traces. Actual DOS executes only the source-built
diagnostic with authored service stubs; no original helper or synthetic
analysis executable is run.

The native caller reloads after all modeled helper results, including lookup
failure. Future maintained integration must use the existing strict loader and
preserve the live mapping after failed/invalid loads; this component does not
replace those safety checks. The original PCKEYMAP implementation, factory
defaults, full key editor UI and foreground admission/return remain open.
The installed connection-test build and physical machine are unchanged.

Source-only build and check:

```sh
./tools/dev --command python3 standalone/build_keymap_launch.py \
  --output build/keymap-caller
./tools/dev --command python3 standalone/test_keymap_launch.py \
  --build build/keymap-caller --output build/keymap-caller-proof
```

An explicit optional `--original` supplies a SHA-pinned2.01 image for paired
instruction comparison. It is never an application build input or public file.
