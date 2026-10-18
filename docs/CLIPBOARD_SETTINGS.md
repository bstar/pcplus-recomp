# Saved clipboard separator

The terminal imports the recovered separator word at PRM offset04EA and checks
that it is0..255 before applying any configuration. Without a PRM selector the
maintained default stays13 (CR). The source-owned PRMEDIT Terminal page adds
**Clipboard separator** after Input translation. It accepts decimal0..255;
32 selects a space and0 selects a literal NUL. Single paste still uses only CR;
the setting affects all/tagged output.

A saved edit changes only the mapped two-byte field and uses PRMEDIT's existing
whole-file validation, baseline comparison and staged replacement. Unknown
bytes remain opaque. Invalid loaded values can be explicitly repaired in the
editor; a terminal startup with256 or any larger word is rejected before UART
ownership with a specific configuration diagnostic. This is a maintained range
constraint; it does not establish the original PCSETUP control's exact UI.

## Startup, session and live setup

Startup applies the validated field for serial-only, explicit dialing and
selected-directory paths. The clipboard list retains its entries across DOS
children and adopts the current separator when reopened.

Clipboard R changes the session value. Alt-F10 records that effective value in
the active candidate. Its owner separately remembers the last accepted saved
value: a canceled editor, unchanged file, or save of another setting preserves
R. An actual change to the saved separator applies with the independent settings
without a UART/profile question. Only a successful foreground application
acknowledges that saved baseline, so reverting a previously accepted saved value
is recognized correctly. Failed reads/validation/command preparation leave the
active separator and acknowledged baseline intact.

Typing an identical saved value is indistinguishable from a no-op child return
and preserves R. Use R to restore that value for the current session, or change
the saved field deliberately. No shared-memory PCSETUP parent protocol is claimed.

## Explicit ABI update

`terminal_import_settings` grows from42 to44 bytes, appending the separator at
byte42. Existing serial/translation offsets stay intact. The pure candidate
grows from626 to628 bytes: modem starts at44, directory at412 and change mask at
626. Clipboard changes use bit4096. All assembly copies/storage, pure validators,
callback fixtures and independent byte oracles now use these layouts. Public
function word-argument counts and the85 code bridge pairs stay unchanged.
PRMEDIT grows from45 to46 mapped fields; separator is index45. The on-disk image
remains exactly1264 bytes.

## Evidence

`./tools/build test-clipboard-settings` runs805 linked production inputs and
seven actual DOS workflows. The linked cases cover all256 import/editor/candidate
values, invalid word rejection, exact field-only mutation, active validation,
CLI precedence, saved baseline acknowledgement/revert, session preservation,
live parent application and reopening a populated clipboard with changed bytes.

The DOS tests use the production terminal and PRMEDIT, a synthetic modem peer,
and an independent INT1C screen observer. Separators0/32/255 reach the wire
unchanged; a live separator save matches the complete expected PRM; canceled
unsaved edits and an unrelated color save preserve R; invalid256 exits before
modem commands. All cases check sampled UART/PIC/vectors and ordinary keyboard
return. Fourteen Python codec tests separately preserve unknown neighbors,
including raw malformed words for inspection.

The current77-command application regression and64-output fresh-source rebuild
bind this feature to the executable in
[the validation record](validation/clipboard-settings.json). Source-only building
and DOS emulation do not prove physical UART/modem behavior. Original menu parity,
clipboard transfer-prompt workflows, other geometries and the full application
remain open.
