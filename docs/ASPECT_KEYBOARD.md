# ASPECT keyboard acquisition

The maintained ASPECT reader now uses the same recovered BIOS normalizer as
the terminal. The previous reader cleared AH whenever AL was nonzero, losing
Backspace, keypad and enhanced E0 identities before native WHEN stored the key.
For example, BIOS0E08 now remains0E08,48E0 remains48E0 andE02F remainsE02F;
ordinary1E61 becomes0061 and3920 becomes0020. The original signed372A threshold
also remains intact, including words with bit15 set.

REA inspection of the verified PCPlus2.01 image confirms native64FE calls7836,
which applies77D2. The latest normalizer dossier is
`ev_cb670ed8c108fd2f8a4d03d1d83765074271c3cae5e31f2e0ac94f3c59873699`;
the read-path dossier is
`ev_8e40cf9d5f190f977da1b135d35970d1fcab5cac3261658c9dabbd80eb7dfbd6`.
The original identity and earlier acquisition evidence remain in
`reconstruction/keyboard/provenance.json`. These are static observations,
not evidence of physical keyboard or modem operation.

`KEYBOARD_NORMALIZERS_ONLY` links the two existing native normalizers without
their private BIOS queue or debugging callback. Caller-cleanup wrappers expose
their RET2 ABI to Watcom C with DS=SS. The complete keyboard build and all four
flat regions retain their original231 bytes and baseline hashes. The ASPECT
product manifest now records each object actually linked, allowing the DOS
keyboard harness to reuse exactly those objects while replacing the CLI entry.

Run through the pinned Nix toolchain:

```sh
./tools/build test-aspect-keyboard
```

The checker executes every possible16-bit BIOS result through the actual
production ASPECT.EXE reader in CPU replay, with a declared INT16 BIOS model.
It checks the returned key, single BIOS read, stack cleanup and BP/SI/DI
preservation. It separately executes all65,536 words in8086 DOS with the exact
production objects and a temporary owned INT16 vector, restoring that vector
before exit. The DOS harness also checks native WHEN last/pending-key state,
disabled input, deferred ordinary keys and Escape cancellation. Its131,132
checks pass;19,011 words differ from the previous lossy reader. Exhaustive
word coverage includes values a particular physical BIOS might never produce.

This fixes acquisition only. Ordinary script-time keys still reach the explicit
unsupported dispatcher; native abort confirmation, full profile/macro/hotkey/UI
dispatch, BIOS mode inheritance and physical BIOS validation remain unfinished.
The parent terminal keyboard path is unchanged. Full keyboard integration must
preserve native mapping precedence and UART/renderer ownership across the child
lease; substituting ASCII output alone would not complete that requirement.

The [validation record](validation/aspect-keyboard.json) binds the product,
objects, generated harness, source-only rebuild and regression results. Older
checkpoint ledgers retain the binaries they originally tested.
