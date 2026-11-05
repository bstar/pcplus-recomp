# Original path editor follow-up

The path-control follow-up corrects the dialog geometry and restores original
editing and error acknowledgement behavior. It also fixes the first paint
after selecting Alt-F7 from a menu and reduces ordinary editing to field-only
video updates. The source-built parent remains a separate development
candidate; the selected physical release is unchanged.

## Evidence correction

The earlier original-program observer stored a two-byte scheduling word
between its six-byte header and its video frames. Its decoder started frames
at offset 6 instead of offset 8. That shifted the reported cells one column to
the right. The raw observations are preserved. Correct decoding of the old
capture matches a new unmodified-original capture byte-for-byte.

Correct zero-based geometry is rows 5–9, columns 1–76. The header marker is at
row 5/column 3, its path starts at column 18, and the prompt starts at row 7/column 3.
The 62 magenta input cells occupy row 7/columns 13–74. The earlier path-control
receipt's checks used the erroneous coordinates and are superseded for this
UI contract. Its independent lifecycle/resource/storage evidence is unaffected.

Ten new unmodified-original DOS workflows and 13 receipt checks establish the
corrected geometry, menu removal, representative editing transitions and error
acknowledgement. REA anchors the generic editor, cursor helper and Enter
callback. Static analysis uses the previously anchored overlay image; that
analysis image is never executed. Exact IDs and capture hashes are recorded in
[the follow-up receipt](validation/path-editor-parity.json).

## Restored interaction

The original editor uses a fixed 62-cell space-padded buffer and starts in
overwrite mode. Right can move through blank padding. Enter trims trailing
spaces while preserving leading and internal spaces. Insert shifts the fixed
field and drops the last cell. Reaching its last cell sets a full latch;
Home/End/Left/Backspace/Delete/Ctrl-End clear it, while Right and Insert do not.
End on a full field permits one replacement at the last cell.

The Insert cursor starts at `floor(saved_end_scanline/2)+1`, retaining the saved
end scanline. Overwrite and exit restore the saved shape. The original fixture
has saved shape 0607; the current application fixture has 060F. The compatibility
test independently observes the pre-popup BIOS shape and applies the recovered
formula when comparing cursor states. VGA character/attribute comparisons use
only explicit C-to-D startup-header normalization.

Invalid paths remain in the field behind the original-shaped Path not found
modal. Acknowledgement creates a blank overwrite editor, with its cursor back
at the field start. The modal remains serviced, as does the underlying terminal.
Its visibly observed shadow retints the underlying path border without changing
characters. The full shadow footprint on arbitrary colored BBS backgrounds
remains inferred and needs broader coverage.

The first menu-to-popup paint now removes the full-screen menu before drawing
over the live terminal. Ordinary editing copies only the input field to video;
menu transitions, error acknowledgement and incoming traffic still compose over
the appropriate live background. This matters functionally: the same unpaced
62-character replay overflowed the BIOS input queue with whole-screen repainting,
but passes with field-only painting. The test does not add key delays.

The navigation replay also exposed a compiler-specific Backspace error: the
generated code reused the old cursor value when shifting the field after a
decrement. Keeping the decremented index local avoids that transformation.
Actual linked instructions now pass 1,134 edit cases across all field positions
and reachable full-latch states, with six additional cursor-shape cases. These
checks include far-call return/stack and callee-preserved-register invariants;
they supplement the original-program VGA/cursor comparisons.

## Application failure boundaries

A test-only INT21 shim injects one-shot DOS failures after an actual directory
change, during rollback and during final restoration. It never changes product
memory or executable bytes. The four application workflows verify successful
rollback/retry, fatal failed rollback followed by successful shutdown restore,
failed native shutdown restore, and failed shutdown verification.

A paired PROGRAM witness proves ordinary program execution remains possible
after verified rollback and is not executed by a queued key after fatal
rollback. Final exit codes, current directory, modem cleanup, hardware snapshots
and restoration of the test interrupt vector are checked separately.
These are emulated failure injections, not claims that physical DOS failures
have been reproduced.

## Candidate identity

The parent is `build/path-ui-editor-final-20261104/TERMINAL.EXE`, SHA256
`4ed1a0036de7684334ab8a01def0ac50ebb1e3cf14d55e1329a6088d5b0ef434`.
Its FILE_CODE bank is 4,012 bytes, including the unchanged 220 persistent state
bytes outside DGROUP. Near data/stack remains 65,488 bytes (48 spare) and resident
code 65,332 bytes (204 spare). The disabled control still exactly matches d8e8b72
and its declared source hashes match the current tree.

The exact candidate passes ten original-key replays matching 42 captured edit
states and window cells, eleven dialog workflows with 274 checks, and four
application-fault workflows with 108 checks. Three resource-identity workflows
pass 90 checks and production PRMEDIT open/cancel passes 31. Fresh stock Enigma and
Synchronet editor audits each match 1,920 logical cells and the checked cursor.
An empty Git-free tree reproduces the executable from 583 declared public inputs;
the original UI captures are compatibility-test inputs, not build inputs.

Physical Microsoft DOS 6.22, slow filesystem/UART combinations, other fonts and
file-owner combinations remain acceptance gates. The full-field refusal beep
and exhaustive special-key behavior also remain UI parity work. Gateway,
File Directory, View a File, editor integration, directory/key tools, Chat and
the broader ASPECT/emulation/protocol/Host inventory remain in the active goal.
