# IRQ release and saved settings filenames

The directory-adoption candidate fixes an IRQ-only handoff on the same UART.
After restoring the old vector, it restores just the old IRQ's original PIC
mask bit. It retains the UART snapshot and DTR level, and leaves unrelated
interrupt masks untouched. Previously the old bit stayed masked until final
application exit. The fix is guarded by `DIRECTORY_RESOURCE_ADOPTION`; seven
earlier terminal control executables remain byte-identical.

Native testing exposed a second gap: the frozen settings launcher passes an
absolute saved PRM identity, while PRMEDIT's document owner accepts only leaf
filenames. The child exited with status 2 before editing. PRMEDIT now accepts
bounded drive-absolute ASCII 8.3 paths, enters that directory in the child, and
uses the existing leaf-only document/replacement owner there. Before returning,
it restores the target drive's previous directory and the original active
drive. A restoration failure returns an error. No parent-pointer protocol,
shell or PATH search is introduced. Existing leaf invocations remain supported.

Path components reject traversal, wildcards, drive-relative names, empty
components and long names. The document owner continues rejecting devices and
reserved recovery filenames. Recovery files stay beside the selected PRM;
an existing backup prevents replacement and remains intact. The existing
compare-before-save and recovery rules are not a writer lock or crash-atomic
FAT transaction.

Validation is recorded in
[the receipt](validation/irq-handoff-settings-path.json):

- 492 linked handoff cases cover all directed distinct combinations of four
  COM ports and IRQ3/4/5/7 under two initial PIC masks, plus late refusal cases.
  These execute real linked instructions against modeled hardware; they do
  not prove full C/UI selection or physical serial behavior.
- Actual DOS preview Apply moves from COM3/IRQ5 to COM1/IRQ4 and COM2/IRQ3,
  and refuses absent COM4 without publishing the proposed selection. Four
  native hardware snapshots and independent active-port samples are checked.
- Actual DOS PRMEDIT changes COM1 IRQ5 to IRQ7. A passive timer observes the
  old PIC bit released during new IRQ ownership, and a late loopback peer
  verifies DSR/DA/CPR, keyboard output and continued duplex input. This covers
  the shared assembly handoff through SETUP, not preview-A IRQ-only adoption.
- Fourteen native editor path tests exercise leaf/root/same-drive/cross-drive saves,
  invalid and missing paths, decoys, recovery conflicts, and drive/directory
  restoration. Twelve existing editor UI/document/recovery tests cover leaf behavior.
- Adoption guards and seven earlier executable controls remain accepted.
  A committed-source package rebuild must reproduce all ten package files.

The application binary is
`da09b00dde9ee9008295e53c96aaa8630b9a4e19f1a78dc683e89e4b3186f650`.
The revised PRMEDIT binary is
`9cc71319162e7e7ff1a242081c6f1b4af124e521a342e1c01e5409bdffd3f977`.
Prior full directory-adoption evidence applies to its recorded earlier binary;
this checkpoint does not relabel those runs as tests of the new binary.

Full application coverage, independent rendering acceptance, sustained data
during synchronous script checks, transfers and physical Boca/SPA2102/card
testing remain open. No removable card or live bridge/BBS was changed.
