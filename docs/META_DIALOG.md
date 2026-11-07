# Serviced Meta Keys dialog component

The new controller composes the recovered Meta Keys row rules and serviced text
field into a working DOS popup component. It has ten rows, kind/text revision,
wrapping navigation and clear behavior. Load/save are explicit deferred requests
to an external file owner; they do not yet perform checked KEY persistence.
The component is not linked into the interactive terminal or installed machine.

## Native behavior and test authority

The original dispatcher `df44`, row editor `e294`, shared editor `7880/79d4`,
callback `e261`, defaults `e24a` and original CRT helpers execute in a separate
analyst replay of executable SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The dispatcher is anchored by REA evidence
`ev_a1a870d1d2c2754325165f8155f2645805d413818b24f53fbf8bf375476f9bbf`.
Keyboard, window/render/cursor/bell and load/save effects are modeled over
synthetic definitions. No private KEY, original VGA pixels, real files, BIOS or
UART participate in this instruction replay. Its
[frozen corpus](../standalone/fixtures/meta_dialog_native.json) records 328 cases
and 3,341 pre-key states, including complete record tables, field bytes, selected
row/kind, cursor/shape, bell counts and load/save events.

All ten selected rows and four kinds are exercised through eight revision paths.
Further cases check wrapping in both directions, lowercase commands, unknown
commands, clear and load/save ordering. Overview Enter rings the modeled bell;
R begins revision. Other kind-selection keys cycle the staged kind, except
Enter/Tab, Escape and Shift-Tab. Accepted rows remain in memory when Escape
closes the dialog; closing is not a whole-file undo.

Shift-Tab in the text field accepts the text but returns to kind selection on
the **same row**, without yet accepting its staged kind. Escape then discards
that kind while retaining the accepted text. A second Shift-Tab commits the
kind and revises the previous row. Tab from text accepts kind/text and revises
the next row. These distinctions match the original composed instruction trace,
rather than being inferred from isolated field return codes.

## Component and memory contract

[meta_dialog.h](../src/key_mapping/meta_dialog.h) defines 684 bytes of explicit
caller-owned far state, including 540 raw KEY bytes, the 64-byte text state and
the displayed name. Open/load validate every kind and terminated record before
copying. The model preserves opaque definition tails. Clear changes only the
kind WORD and first text byte, as the original defaults do.

Load/save requests freeze keyboard edits until the external owner completes.
Failed loads leave definitions intact. A malformed successful-load response is
rejected while retaining the pending state, so its owner can finish recovery
before acknowledging failure. The eventual owner must supply checked IO,
canonical resource identity, close/recovery decisions and live table adoption;
the controller does not replace those responsibilities.

The controller performs no allocation, keyboard wait, BIOS call, DOS operation
or UART access. The view writes only rows 3..19/columns 7..76 of a supplied
80x25 frame. Its decoration is authored; row kind/text coordinates follow the
native control structure, but original window-pixel equivalence is still open.
All constant prose lives in its code bank, outside DGROUP. Code-bank GROUP frames
are explicit. A Watcom ternary conversion lost the based-code segment on kind
labels; separate assignments preserve CS-to-far conversion, and the actual
compiled view checks cover all four labels.

## Verification and prototype

```sh
./tools/dev --command python standalone/build_meta_dialog.py \
  --output build/NEW-meta-dialog
./tools/dev --command python standalone/test_meta_dialog_vga.py \
  --build build/NEW-meta-dialog --output build/NEW-meta-vga
```

The ordinary source-only diagnostic passes all 328/3,341 native trace comparisons
and checks the view at every pre-key state: kind/definition cells, selected-row
attributes and unchanged cells outside the window. Eight API/owner guards cover
bad definitions, aliasing, blocked pending input, malformed load results, failed
load preservation, save completion and invalid nested field state. The state is
in a genuinely separate segment outside DGROUP, and the caller/model use different
CS values with DS=SS. A diagnostic-only 64-KiB pad forces code separation; it is
not an application memory proposal.

The VGA test builds `METAPOP.EXE`, an owned probe using synthetic definitions.
An independent passive timer observer captures overview/kind/text states, typed
text and the dynamic Insert shape. The whole prior 4,000-byte screen, cursor and
shape are restored exactly; all 540 definition bytes, including opaque tails,
remain unchanged after cancellation. The test host writes
only its own `RESULT.BIN`. Its L/S requests deliberately report failure because
no persistence backend is linked. It is not a replacement PCPlus launcher.

Early VGA testing exposed a diagnostic linker-order error: BEGDATA's null guard
was placed after STACK. Both builders now put BEGDATA first within DGROUP and
assert `_NULL` starts at the group base. The corrected VGA test passes exact
restoration without a runtime null-assignment message. These failed intermediate
probes remain ignored artifacts and are not acceptance records.

An isolated twelve-file export reproduces both diagnostic/probe executables and
repeats controller and actual VGA checks without originals, private data, prior
objects or ancestor Git. The outer pinned Nix environment supplies tools. The
[receipt](validation/meta-dialog.json) binds source and product identities.
A [separate checked KEY backend](KEY_EDITOR_FILES.md) now passes its component
gates, but is not linked to this controller/probe. Filename selection, original
VGA comparison, live action
adoption, foreground/resource ownership and application capacity/BBS/physical
acceptance remain separate. No whole F02/F05/F06 gate is closed.
