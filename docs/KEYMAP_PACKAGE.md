# Matched keyboard-helper package

The current recipe uses [contract4's actual Key Mapping Help](KEYMAP_HELP.md),
helper `c94d43ba…` and archive
`9ecf9c5bce2f87e71f609e729fe6bfdeebd3903d5090ecff1c533763075784ed`.
[The current receipt](validation/keymap-help-package.json) records35 admission
cases, including diagnostic-helper and missing-Help-resource refusal.
Packaged DOS8086 COM3/IRQ5 START edits a33-profile file, opens actual context17
Help before saving a seven-profile file, and opens Help before explicitly
creating a new file while preserving the frozen selected/private files.
All16 products and the ZIP reproduce from2690 public inputs at tooling
commitedb21fb, with application base59bc746. Only mapper/README/VERSION differ
from contract3; parent, standalone PCHELP, authored HLP and other modules retain
their bytes. The feature-disabled archive remains exactly installed `6f9e1f6f…`.
No selected deployment or physical installation changes.

The preceding recipe uses [contract3's explicit-save new-file workflow](KEYMAP_NEWFILE.md),
helper `5a917b93…` and archive
`f0f1b132e9ed8dbc9423ca5082e89ab1f08870469eb26ba131959f1f1ea32ab6`.
[The preceding receipt](validation/keymap-newfile-package.json) records29 admission
cases, packaged DOS8086 COM3/IRQ5 existing-file edits at seven and33 profiles,
and a separate new-file creation preserving the frozen selected file and all
private sentinel fixtures. All16 files and the ZIP reproduce from2684 public
inputs at tooling commit270e1e5, with application source base38a37d6. Relative
to contract2, only PCKEYMAP, README and VERSION payload bytes change. The
feature-disabled archive remains exactly the installed `6f9e1f6f…` archive.
No selected deployment or physical installation changes.

The following describes preceding checkpoints. Contract2 uses the
[prefix-file extension](KEYMAP_PREFIX.md),
helper `618443f4…` and archive `9365ebff…`. It accepts1..33 complete profiles
and preserves their exact file length. The
[preceding package receipt](validation/keymap-prefix-package.json) records26
admission checks, packaged DOS8086 COM3/IRQ5 START edits for both seven-profile
and33-profile files, and an exact16-file/ZIP rebuild from2680 public source
files at tooling commit4fe5bee. Source base fe43c2b identifies the application
checkpoint. The feature-disabled archive remains exactly `6f9e1f6f…`.
Seven read-only inspector cases cover full/short/VT220/absent/malformed/empty/
oversized files, with bytes unchanged and no binding values displayed.
The old receipts below remain bound to their original bytes.

The preceding keyboard-mapper candidate contains16 public files, including
the exact tested PCKEYMAP helper beside its parent. The tracked
[recipe](../standalone/keymap_connection_candidate_recipe.json) builds every
application from source, checks all payload hashes and produces deterministic
archive SHA256 `690eabd49b028388cdade5aa5c53437b568cbeda3c8208965c3017e6cf9a71cc`.
It does not select or deploy this package.

Package admission requires an explicit helper whenever the parent exposes
Alt-F8, and rejects a helper with a disabled parent. The reviewed helper contract
pins its binary hash, source-only build proof, argument interface and recovery
exit. Source paths/hashes are checked before staging. Archive admission rejects
missing, corrupt, undeclared or falsely rehashed companions and mismatched
contracts. Eighteen admission cases pass.

The actual packaged START launcher passes a DOS8086/COM3/IRQ5 edit/save/return
test. It saves exactly the intended ANSI F1 slot in a separate full-size SYN.KBD;
the private-fixture PRM/DIR/KEY/KBD/XLT/FON, including the existing seven-profile
PCPLUS.KBD, remain unchanged. Application files and hardware state also match.
This is a dummy-port launcher test, separate from connected BBS tests.

An isolated export from the committed tooling rebuilds all16 files and the ZIP
exactly from2674 public source files, without original programs, prior objects,
private settings or ancestor Git. The recipe's source-base commit identifies
the preceding application checkpoint; the reproduction receipt separately
records the actual tooling/source-export commit. The feature-disabled composed
build reproduces the installed15-file archive byte for byte.

[The receipt](validation/keymap-package.json) binds these checks and the new
paired Synchronet flow experiment. Both flow runs use identical application,
helper, generated programs, framing and single-byte pacing. Ignoring RTS exits6
after a correct save/frame restoration; respecting RTS pauses delivery for8.895
seconds with DTR asserted, then passes continued editing, draft abort, exact
screen/cursor and zero DOS exit. This closes the earlier pacing confound within
the model. It does not establish physical CTS/DCD, modem latency or FIFO behavior.

```sh
./tools/dev --command python standalone/build_connection_candidate.py \
  --recipe standalone/keymap_connection_candidate_recipe.json \
  --output-dir build/my-keymap-candidate
./tools/dev --command python standalone/prove_connection_candidate.py \
  --recipe standalone/keymap_connection_candidate_recipe.json \
  --build build/my-keymap-candidate --output build/my-keymap-source-proof
```

RA608E10 and the selected connection-test payload remain unchanged. Before a
deployment, validate the selected private KBD: the helper currently requires
all33 profiles/31284 bytes and safely refuses shorter files. Expanding or
replacing private bindings is not part of packaging.
[Current-candidate connection regressions](KEYMAP_CONNECTION_REGRESSIONS.md)
now cover BBS transfers, cancel/retry, actual Enigma loss/redial and reported-close
quarantine. Private KBD validation, broader foreground-refusal DOS transitions
and physical Boca/SPA2102 acceptance remain open. Broader native helper/UI/defaults,
ASPECT, protocol/emulation and Host parity remain open.
