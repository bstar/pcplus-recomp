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

`KEYBOARD_BIOS_ONLY` links the existing normalizers and native7836/7842 BIOS
read/peek routines without their private queue or debugging callback.
The peek uses BIOS ZF: an occupied rawAX0 becomes0100, while an empty queue
returns0 even if BIOS leaves a nonzero AX. Reads use the original normalizer.
Near adapters expose these routines to Watcom C with DS=SS. The complete keyboard build and all four
flat regions retain their original231 bytes and baseline hashes. The ASPECT
product manifest now records each object actually linked, allowing the DOS
keyboard harness to reuse exactly those objects while replacing the CLI entry.

Run through the pinned Nix toolchain:

```sh
./tools/build test-aspect-keyboard
./tools/build test-aspect-keyboard-policy
```

The checker executes every possible16-bit BIOS result through the actual
production ASPECT.EXE reader and peek in CPU replay, in both standard and
enhanced modes with a declared INT16 BIOS model. It checks the returned key,
peek/read consumption, stack cleanup and BP/SI/DI preservation. It separately
executes all65,536 words in each mode in8086 DOS with the exact
production objects and a temporary owned INT16 vector, restoring that vector
before exit. The DOS harness also checks native WHEN last/pending-key state,
disabled input, deferred ordinary keys and Escape cancellation. Its655,494
checks pass;19,011 words differ from the previous lossy reader. Exhaustive
word coverage includes values a particular physical BIOS might never produce.

The child selects AUTO at invocation startup through the recovered7916 BDA
detector. CPU replay checks every possible BDA0496 byte without mutating it.
With an admitted parent, renderer capability5 inherits the parent's effective
mode0/10h once before script execution. Thus explicit `/B:STANDARD` and
`/B:ENHANCED` survive the child boundary, independently of AUTO. EXECUTE retains
that selection; a new invocation resets inheritance. ASIO's descriptor remains
version4/48 bytes; its guarded renderer capability is now5. Capabilities1–4
are rejected before UART access. Missing, duplicate, unsolicited, invalid or
closed-lease policy callbacks fail explicitly.

Four actual parent/child DOS cases pass for both explicit modes, directly and
after EXECUTE. A passive timer observes the real child's BIOS mode while PAUSE
runs, with the existing status, renderer/query, owner/IRQ/handle restoration
and parent-keyboard-return assertions retained. The mode-policy CPU checker
separately covers10 successful/rejected lifecycle cases.

The initial expanded DOS harness forgot to reset its16-bit BIOS-read counter
between mode sweeps, producing one checker failure; the product key results
were correct. The first parent probe correctly observed all four modes but
expected a status row that its own incoming clear-screen banner had erased in
the direct cases. It now explicitly repaints that row through SET WHENCASE,
as the reused status fixture requires. Both failed attempts remain private
under `build/aspect-keyboard/history/bios-counter-01` and
`build/aspect-keyboard-mode-dos/bios-policy-01`; the passing parent run is
`bios-policy-02` with the same product binaries.

This fixes acquisition only. Ordinary script-time keys still reach the explicit
unsupported dispatcher; native abort confirmation, full profile/macro/hotkey/UI
dispatch and physical BIOS validation remain unfinished.
The parent terminal keyboard path is unchanged. Full keyboard integration must
preserve native mapping precedence and UART/renderer ownership across the child
lease; substituting ASCII output alone would not complete that requirement.

The [validation record](validation/aspect-keyboard.json) binds the product,
objects, generated harness, source-only rebuild and regression results. Older
checkpoint ledgers retain the binaries they originally tested.
