# Existing shorter keyboard files

The maintained keyboard editor now accepts1 through33 complete948-byte
profiles. This closes a mismatch with the parent: a valid seven-profile ANSI
file could load in the terminal but was refused by the full33-profile editor.
The selected profile must exist. Saving preserves the exact original length,
other bindings and opaque slot suffixes; it never appends defaults.

This is a maintained compatibility extension. The recovered original editor
evidence and its full-size workflow receipts remain separate. The old strict
`kbd_editor_file_load/save` API still requires31284 bytes. New prefix APIs stage
and validate the whole existing file, check EOF and close before publishing,
and compare exact length/content before both staging and replacement. A failed
load publishes nothing. Unused RAM is zeroed without writing padding to disk.
Open adjusts navigation to the accepted file's profile count; an absent current
profile selects profile0 only after a successful Open. A failed Open retains the
previous saved file and profile count.

[The validation receipt](validation/keymap-prefix.json) binds the new helper
`618443f4…` and unchanged parent `44891156…` to:

- 955454 DOS8086 storage checks across all33 lengths,57 save-fault cases and
  six concurrent length-change refusals;219188 strict legacy storage checks.
- 14 full-file and19 shorter-file GUI sessions, with exact file preservation
  and restored screen/cursor/shape, including missing/malformed files and
  absent-profile refusal.
- 33 actual parent sessions:11 each for VT220/profile4 in a five-profile file,
  ANSI/profile6 in seven profiles and ANSI/profile6 in33 profiles. Tests cover
  save/RIS, cancellation, Open, another profile, missing helper, malformed
  return, recovery exit14, ordinary child-error reload, reference and browser.
- Actual stock Enigma and Synchronet edit/save/return sessions with6636-byte
  seven-profile files, exact frame/cursor/input checks and subsequent BBS input.
  Synchronet's independent audit also verifies the RTS pause without delivery.
- An isolated18-input public-source export reproducing the exact helper.

The helper's linker memory is69920 bytes,336 more than the previous helper;
the4096-byte stack and peak full-capacity image allocation strategy are retained.
A fresh composed parent build produces the same executable and companion bytes.

The current private KBD has not been inspected. These BBS checks use virtual
serial connections and SynthModem's Telnet bridge. Physical Boca/SPA2102 audio,
carrier/flow control and DOS disk-close behavior still require hardware tests.
The installed package and selected deployment remain unchanged. The
[reviewed contract2 package](KEYMAP_PACKAGE.md) now also passes packaged START
editing at seven and33 profiles and exact clean-source archive reproduction.
