# Redisplay export and filename clipboard recovery

This ledger records static original-product observations for remaining F11 work.
[Serviced export](HISTORY_EXPORT.md) now implements the maintained file path;
[the maintained filename clipboard](FILENAME_CLIPBOARD.md) now supplies the core/UI/output path. This ledger records the original
static observations separately from those maintained behaviors.
Original main executable SHA-256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Resident exports live in ignored `analysis/pcplus-main/functions`; overlay exports
in ignored `analysis/pcplus-overlay-anchored-15/functions`. Synthetic overlay
analysis executables are static contexts only and are never executed.

## History file output

Overlay15 entry D8BDh (`ev_1fbfae25e909f4dce2aacc7720d25245a1b18830da899e1d95923cfa1828e74e`)
opens the caller pathname with the string at DS:7724h, traverses recorded bytes
in circular order and expands CR through the string at DS:7727h. The genuine
original data bytes at file2D074h are `61 62 00 0D 0A 00`: mode `ab`, then CRLF.
Thus history output appends binary text; it does not replace an existing file.
The native ring traversal helpers E708h/E7EEh skip the oldest CR when a wrapped
ring begins on that marker and stop at the recorded endpoint. Other bytes pass
through unchanged. These observations need controlled original comparison before
claiming complete empty/wrapped boundary fidelity.

The maintained export now uses the frozen chronological snapshot, services
serial input between bounded writes and uses the checked DOS file ownership
policy; see [the implementation and validation](HISTORY_EXPORT.md). CRLF expansion can make a full63,000-byte snapshot
larger than64KiB, so output totals must be32-bit and staging must be bounded.
Existing-file append, missing-file exclusive create, denied/colliding paths,
short writes, disk full, close ambiguity, cancellation and incoming data require
independent coverage. The maintained validation supplies that coverage; it does
not establish recovery of the complete original UI.

## Clipboard observations

| Entry | Observed behavior | Assembly Evidence ID |
| --- | --- | --- |
| D0D0h | C cut, E edit, P paste all, S single, T tagged; Escape returns | `ev_ead52f25f79395b992a038ceda4cc115a4eb090f037604308a9dd143452994c4` |
| D136h | Select detected screen filename; Enter copies, uppercases and rejects duplicate names | `ev_7e8f5f1564c9539da38c52b705a22fff1c79c5c455d136fa760453ce58f5ae72` |
| D34Eh | All/tagged traverses allocated count, including edited empty names; separator after each selected entry, final CR if any selected; list retained | `ev_5daa740e3d4267513723a0bab04c0fa9d7ab4d603fdc0b4b158524b071feaac4` |
| D3D4h | Single sends first name and CR, removes it and compacts names/tags | `ev_c6db04f178b383933e36bc105b421b4bc9e2461bcf54c0bbf6ab8b1d6b03ba93` |
| D411h | Uppercase candidate; compare all15 slots for duplicates | `ev_6deab914b444d1352825defffc1bd13bea01621b40032206ed2c5f74916878b2` |
| D455h | Add/edit/delete/purge/tag, cursor movement and first-letter navigation;12-character field | `ev_cbd205914b5b142964d5d7e6c01cd6dbe2e2cf1ae42693e918817613e0d2570f` |
| D81Ah | Maximum15 entries,13 bytes per NUL-terminated slot | `ev_dc0c5ad2f97e78ca3d87d8db3e83021cac6e679609023f235a8d70149133f1b2` |

Names begin at DS:E798h, tags at DS:E85Ch and count at DS:7580h.
The separator at DS:206Eh is initialized to CR (original file279BEh).
The dispatch loops below allocated count, not all15 slots. Edited empty entries
also emit separators; tagged skips only zero tags. All/tagged emits a separator
after the final selected name as well as the final CR; an empty tag selection sends nothing. Help's wording about separators is
less precise than this assembly. Single paste does not use that separator loop.

Resident3859h scans screen rows for dots, up to132 columns
(`ev_2c871145a445d28211fc2575f69b02a80c5eedb9dd7e13ed80393a5a7848daae`).
397Bh requires1..8 preceding allowed basename bytes and at least one following
extension byte, copying at most3 extension bytes
(`ev_ba4f8f4a51e4398882a6528e4ec064b31dfa02d98bfabe63e3329efd055e3e46`).
Extensionless names are missed and long extensions truncate. The allowed-byte
predicate at resident39FCh permits
ASCII21h..7Eh excluding `."/\[]:|<>+=;,`
(`ev_221f2f5a82e5affce2f511fae391f5837819c9216def179b1aaadec09bfe72ab`).
The blacklist bytes are at original file29FECh. Neither extraction nor paste
checks whether the named file exists on the local filesystem; BBS names can
refer to remote files. Uppercasing is ASCII only (resident9128h,
`ev_af474791eca9acf2db71969ff3c292523e8ed769a7f02f274f430beb977ddc2c`).

The original help clipboard topic at file0973h corroborates single removal,
tagged retention, configurable separator and single-file/batch usage. Redisplay
help at3E1Fh advertises C opening the clipboard. Baseline terminal hotkey is
Alt-=; a separate historical `clipkey.dtp` patch changes it to Alt--.

## Remaining evidence and implementation

The saved separator word is PRM offset04EAh: DS:206Eh lies within the1264-byte
DS:1B84h..2073h payload read/written by overlay19 E8E4h through DDE3h/DE3Ah
(`ev_c365a56c6527a5303a8baa2df06bd32c5a8a1b950085051bf86358892d97e7ee`).
Its exact original Setup control remains unresolved; maintained import, editor
persistence and live adoption are implemented in [saved settings](CLIPBOARD_SETTINGS.md).

Original editing through resident79D4h/3F9Ch preserves case and accepts duplicate
or empty entries without changing allocated count; add remains uppercase and
checks all15 slots. The maintained bounded core preserves that distinction and
its packet quirks. The optional original replay now compares321 cases, including
48 dispatch/packet/Single-compaction cases with allocated holes.

The original screen scanner supports up to132 columns, but the precise refusal
threshold and video/UI behavior remain unrecovered;80x25 is a maintained gate.
Help describes pasting to remote prompts before single/batch protocols, rather
than injecting names into a local transfer dialog or active protocol stream.
Exercise those end-to-end workflows, complete original UI and
other geometries before closing F11; physical validation remains open.
