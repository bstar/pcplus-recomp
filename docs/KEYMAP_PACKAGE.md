# Matched keyboard-helper package

The reviewed keyboard-mapper candidate now contains16 public files, including
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
replacing private bindings is not part of packaging. Targeted admission/close
faults, current-candidate transfer/reconnect/carrier regressions and physical
Boca/SPA2102 acceptance remain separate gates. Broader native helper/UI/defaults,
ASPECT, protocol/emulation and Host parity remain open.
