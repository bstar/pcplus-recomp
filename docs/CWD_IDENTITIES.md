# Directory dialog contract and stable resource identities

The original Alt-F7 dialog is now identified in overlay 3 at DB99..DC33.
REA/Ghidra evidence
`ev_67c3a1cf531aa98f5c88d875c0474bd0356a2a2732f5fec5f84bf102e1b663ce`
shows a current-directory header, a field bound of 62, cancellation/empty return,
a call to the recovered path helper and an error/retry loop. The current-path
formatter at DF1A..DF42 has evidence
`ev_326ef11afa6cdec1d98678c818f258b71c8cb9194637c9cb381778b9a4cd9836`.
The private anchored image includes only the selected overlay chain plus
startup data; trampoline substitutions and decompiler types are not runtime
observations. No analysis executable is run.

Six separate executions of the unmodified original confirm the visible/runtime
contract under DOSBox-X built-in DOS/8086: an initially blank new-path field,
C/D directory changes shown when reopening the dialog, empty/escape behavior,
a missing-path error, and restoration of the initial directory on final exit.
A passive INT1C observer reads video only; it makes no DOS calls or key writes.
The unavailable-drive case is consistent with the low-level helper's retained
drive-only false success; it is not treated as proof of a new application bug.
Original files, copied private settings, complete screens and REA databases stay
outside Git. The receipt binds the local result summaries and original identity.

## Why identities must be fixed before Alt-F7

The selected development parent still used relative startup PRM/DIR selectors
and a relative PRMEDIT lookup. Its directory resource/retirement features were
not enabled. Changing DOS CWD could therefore refuse live settings or direct
directory accounting at another same-name book. Default XLT lookup was also
rebuilt from the new CWD during later settings entry. Existing absolute call-log,
capture and recording owners do not solve those separate identities.

The optional `--cwd-identities` build now:

- Canonicalizes all nonempty PRM/DIR/KEY/KBD/XLT selectors transactionally before
  startup import, and freezes any selectors resolved during keyboard loading.
- Resolves PRMEDIT beside the running terminal and passes the absolute startup
  PRM to both startup `/S` and live setup through the existing PROGRAM handoff.
- Freezes default current/PCPLUS XLT identities and their lookup errors once,
  including when `/X` selects a separate explicit active table. Later reloads
  retain their active identity without replacing the saved defaults.
- Preserves the existing directory-retirement scheduler when that feature is
  selected; the new legacy-settings branch does not replace its ownership gate.

This is a prerequisite flag, **not** an Alt-F7 implementation. The default flag
set remains byte-identical to parent 055f56e6. The enabled parent is
`build/cwd-identities-final-20261104/TERMINAL.EXE`, SHA256
`d8e8b72668ed00edaebfe22a2c5d445ded21880cf8a7145e90aa5ce92fc7d9c8`.
It reproduces exactly from 573 public inputs in an empty Git-free source tree.
Resident CS is 65,292 bytes; near data/stack is 65,488, leaving only 48 near bytes.
Further persistent dialog state needs an explicitly verified storage layout.

## Checked behavior

Seven linked cases exercise atomic five-selector publication, absolute sibling
setup preparation, busy/no-PRM refusal and canonicalization/length errors.
Five linked XLT cases cover default/fallback/explicit identities and retained
canonical errors after namespace/reload changes. Actual C/assembly executes;
those two suites model DOS calls.

Three DOS8086 workflows execute startup `/S`, live Alt-S after an owned PROGRAM
child changes directory, and directory-configured Alt-P after the same change.
The setup child receives `D:\TEST.PRM` from `C:\PRMEDIT.EXE`, reads the original
bytes, and leaves other-folder decoys untouched. Directory accounting updates
the original book. Keyboard/UART input and fresh ANSI replies work afterward;
hardware snapshots match exactly. These cases use a synthetic read-only setup
child and do not by themselves validate production editor saving.

A separate 31-check workflow uses the actual source-built PRMEDIT. After the
real directory change, a passive stable-VGA capture shows the startup PRM's
COM3 beside a COM2 decoy. Escape cancels, both files remain unchanged, the
editor restores the changed working directory, and keyboard/UART/query service
and hardware restoration pass. This covers production editor open/cancel and
does not claim save/adoption coverage.

The unchanged disabled parent fails the same real-CWD live-settings probe at
the four intended settings identity checks while retaining the real directory
change, serial return and hardware restoration. Only test preflight/case
selection is adapted; no application bytes or state are patched.

Fresh stock Enigma and Synchronet editor sessions on the enabled image each
match 1,920 logical cells and cursor coordinates, with NAWS 80x24. These are owned
loopback fixtures through the staged proxy, not SIP/DSP/Boca/SPA2102 acceptance.

See [validation/cwd-identities.json](validation/cwd-identities.json) for exact
products, source identities, native workflows, control and BBS audit bindings.
The installed release and deployment selector remain unchanged.

## Remaining integration

Alt-F7 still needs its serviced dialog, foreground/file-owner admission, retained
rollback quarantine, and original start-directory restoration on final exit.
The [guarded path component](FILE_PATH_OWNER.md) is not yet linked into that UI.
Production editor saves/reload, new-image transfer/reconnect composition,
wider namespace/profile/layout combinations,
Microsoft DOS 6.22 and physical modem acceptance remain separate gates. The
older current-folder wording in experimental settings help also needs updating
when the complete user-facing command is enabled. DOS Gateway remains required.
Future KEY/KBD editing/adoption must also retain the provenance of tables loaded
through implicit directory/default searches; canonical CLI selectors and active
in-memory tables alone do not implement those later tools.
