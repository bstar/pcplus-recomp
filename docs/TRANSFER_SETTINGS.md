# Saved automatic-download settings

PRMEDIT now exposes Auto Download and Download directory on its TERMINAL page,
bringing the mapped editor to 48 fields. This checkpoint implements editing and a
checked decoder. The terminal does not yet adopt these fields or automatically
start reception. The native locations and original consumer evidence are in
[ZMODEM_AUTOSTART_NATIVE.md](ZMODEM_AUTOSTART_NATIVE.md).

| Setting | PRM location | Maintained representation |
| --- | --- | --- |
| Auto Download |042c, little-endian word|Editor preserves 0..65535; decoder maps zero to disabled, every nonzero value to enabled.|
| Download directory |031c,64-byte region|Terminated path of at most63 bytes; empty decodes to `.`.|

The lossless Python codec can inspect/edit the proved raw word and string bytes.
It preserves bytes after a newly written terminator and all unrelated bytes;
application validation is separate. Merely viewing a malformed image never
repairs it. PRMEDIT accepts explicit repairs and restores baseline tail bytes
when reverting an edit. Its existing checked replacement owner still handles
staging, backup, baseline conflicts and cleanup failures.

## Checked transfer decoder

`transfer_import_decode` is independent of the existing 44-byte serial-settings
ABI. Its 66-byte result contains the normalized flag and bounded directory. The
pure near-cdecl API rejects null, overlapping and wrapping arguments before
mutation, preserves the source and commits the result only on success. DS=SS
is required. It performs no DOS, UART or filesystem operations.

The maintained syntax accepts DOS8.3 directory components, roots, drive-relative
paths, either separator and one optional trailing separator. Empty and explicit
current-directory forms are accepted. Devices (including extensions), UNC,
parent traversal, wildcards, spaces, overlong components and unterminated fields
are rejected. This bounded ASCII syntax is maintained policy, not a recovered
complete original path grammar. A raw malformed path remains representable in
the lossless codec and repairable in the editor.

Spelling, case and slash direction remain unchanged for nonempty decoded paths.
Current-directory resolution is deferred until transfer start. A syntactically
valid directory does not prove drive availability, directory existence, free
space or sufficient room for each incoming filename. The actual checked batch
file owner must enforce those conditions. Drive-relative current-directory
forms such as `C:`/`C:.` also need explicit reconciliation with that owner's
normalizer before terminal integration; accepting them here does not prove
end-to-end transfer support.

The new 63-byte field scrolls horizontally while editing, so its final characters
remain visible within the existing 53-column field area. Older field indexes and
page order remain stable; the two new fields follow Clipboard separator.

## Validation and limits

`./tools/build test-setup test-config` runs the editor model, existing DOS owner/UI
workflows, new transfer-setting workflows and lossless Python codec tests.

- The source-built 8086 model passes 450 inputs across 12 groups, including 48-field
  byte-identical round trips, raw nonzero enable words, empty/roots/drive-relative
  and 63-byte paths, opaque-tail restoration, invalid-path repair, output atomicity
  and near-pointer guards. Its independent CPU replay forbids BIOS/DOS/UART I/O;
  a separate actual DOS run verifies the C runtime and unchanged input file.
- All 12 existing actual DOS editor/owner workflows pass, including cancellation,
  production save, replacement-failure ownership and screen restoration.
- Seven additional actual DOS BIOS-key UI workflows save enable/nonzero/path/both,
  cancel staged changes, refuse a device name and save a 63-byte directory. They
  compare the complete 1264-byte image and check restored video/cursor state.
- Seven production terminal/PRMEDIT/clipboard workflows pass with the new editor,
  preserving saved/session separator behavior and post-child serial interaction.
- All 15 lossless configuration unit tests pass. A fresh original-free source
  snapshot reproduces all 64 existing application/diagnostic outputs, including
  the changed editor. The terminal remains byte-identical at `d791eb10`.

The first long-path UI attempt used an unsupported ADDKEY token and timed out
before receiving save/exit keys. That fixture failure is retained separately;
the corrected recipe uses a literal slash, following the upstream
[DOSBox-X command parser](https://github.com/joncampbell123/dosbox-x/blob/master/src/shell/shell_cmds.cpp).
It did not require a product change. Exact hashes and scoped reports are in
[validation/transfer-settings.json](validation/transfer-settings.json).

Startup/live adoption, recognizer ownership/deadline integration, automatic
receiver entry, destination-owner reconciliation, actual DOS/BBS automatic
downloads and physical modem validation remain unfinished. No F01–F16
whole-application gate closes at this checkpoint.
