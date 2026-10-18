# Native capture, snapshot and printer inventory

This F10 ledger describes original PCPlus2.01 behavior established from retained
REA assembly and SHA-verified original bytes. It records native behavior rather
than the current maintained implementation; see [LIVE_CAPTURE.md](LIVE_CAPTURE.md)
and [LIVE_SNAPSHOT.md](LIVE_SNAPSHOT.md) for implemented live owners. No new REA session, original application execution,
BBS session, captured private text or customized configuration was used.

Follow-up recovery is recorded in [PRINTER_NATIVE.md](PRINTER_NATIVE.md) and
[RAW_MONITOR_NATIVE.md](RAW_MONITOR_NATIVE.md). The latter proves a separate
Ctrl-\\ monitor and optional binary `PCPLUS.DMP` writer; it is not the screen
snapshot path. Those follow-up ledgers supersede the unresolved route questions
below within their stated search boundaries.

Baseline EXE:214016 bytes, SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Resident CS offset `x` maps to EXE file offset `1200h+x`. The initialized DS
image begins at file offset `25950h` (153936), length60080; selected constant
strings and the actual keyboard pointer table were read there after digest
validation. Overlay routes use the existing `analysis/pcplus-overlays/manifest.json`.
Saved native exports are ignored local artifacts, not build inputs. Evidence
IDs below are their retained REA **assembly** observations; analysis overlay
images are synthetic carriers and were never executed.

The advertised surfaces are catalogued in [FEATURES.md](FEATURES.md), F10:
EXE strings at file26081h..260c7h identify log toggle/pause, screen snapshot and
printer toggle, while the help/status entry is only an advertised description.
The executable call paths below establish considerably more than those labels.

## Commands: verify the actual key route

`reconstruction/keyboard_mapping/dispatch_table.asm` reauthors original DS44e0
as relocated pointers. Raw BIOS scan numbers here are **hexadecimal**; scan68h
is Alt-F1, not ordinary F10 (scan44h).

| Command | BIOS scan / resident entry | Observed destination |
| --- | --- | --- |
| Log toggle | Alt-F1,68h ->bb23 | Overlay16:e5a4 |
| Log pause/resume | Alt-F2,69h ->bb17 | Overlay16:e57a |
| Screen snapshot | Alt-G,22h ->1310 | Calls3496(1), with0dae service before/after |
| Printer copy toggle | Alt-L,26h ->1a76 | Open/close PRN, state3988/handle8ff0 |

Two tempting but incorrect command associations must be avoided: Alt-F3/6ah
points to332e, which toggles CR-adds-LF word1d24. Alt-F4/6bh points toba3f,
overlay3:dc34, which resolves COMSPEC and invokes the external-program path.
They are not the screen-snapshot or printer-toggle commands.

The maintained raw classifier identifies unreconstructed local commands with
an explicit local-action result. Classifying a key does not implement these
native UI/file services. Ordinary F1..F10 remain configurable mapping slots.

## Capture state, owner and normal append policy

| Original DS field | Source-proved meaning |
| --- | --- |
|398a| Capture file enabled/open flag |
|398c| Capture held/paused flag; only meaningful while398a is enabled |
|d114| Near CRT FILE pointer for capture, not a DOS handle number |
|1d24| CR-adds-LF terminal option, also changes capture/printer newline output |
|3988| Printer-copy enabled flag, separate from capture |
|8ff0| Printer FILE pointer, also used by native screen-print helpers |

Overlay16:e5a4 first brackets its work with6b5a/6b42. When capture is active,
it clears398a, calls `fclose(D114)` at8318 and returns. It does not prompt for
another file and does not check close/flush success. It does not clear398c on
this branch, although status treats an inactive capture as closed regardless.

When inactive it saves a UI rectangle, prompts into a40-byte local buffer
using7880 with limit22h, then restores the saved rectangle. Input resultffffh
(Escape) leaves capture inactive. Result0 (empty Enter) substitutes the literal
`PCPLUS.LOG` from DS1e1e. A supplied nonempty name is used as entered by the
input service; there is no observed path normalization or overwrite dialog in
this function.

It calls resident48a1 on the selected name, then `fopen(name,"at")` at841a.
The mode bytes at DS7761 are **append text**, not write/truncate or binary.
Successful open stores D114, clears398c and sets398a=1. Failed open leaves
capture inactive and displays the message pointed to by25aa (initial text is
an unable-to-create-file error) through427f. Capture therefore resumes by
reopening in append mode, not overwriting earlier session text.

The pre-open helper48a1 is concrete but must not disappear from an exact
recovery: it opens the same path with mode `r+t` (DS4782), calls853a with
file-offset0 and whence2 (seek end), then closes. Return values are not checked
by that helper or the capture owner. There is no observed overwrite operation
there. Exact consequences of missing files, a trailing DOS text EOF marker,
sharing restrictions and failed seeks still need focused CRT/runtime tests;
mode strings alone do not settle those edge cases.

Overlay16:e57a toggles398c only if398a is nonzero. Inactive pause requests have
no effect. It does not close/reopen the file, write a pause marker or add a
timestamp. Status refresh2fb8 selects the literal `OPEN`, `ON HOLD` or `CLOSED`
from DS432e/4336/433e using both flags. This proves a three-state UI distinction
rather than two unrelated flags.

## Actual logged bytes: terminal text, not raw serial capture

The already recovered resident09b6..0a39 (`terminal_log_character`) is132 exact
bytes. Continuous input0610 calls it after the ordinary printable renderer;
CR1002 and LF0f3e call it explicitly. Escape/control processing follows other
paths. Thus this is a processed terminal-character sink, not a byte-for-byte
recording of the UART, ANSI command stream, file-transfer payload or Hayes
traffic. Other modes/echo routes must be tested separately before claiming a
complete transcript policy.

Its capture branch is precise:

- Values00ffh and007fh are discarded before either sink.
- If398a=0 or398c!=0, the capture FILE receives nothing.
- For CR000dh with1d24=0, it writes nothing to capture. With1d24!=0, it writes
  LF000ah instead and returns immediately.
- Other delivered characters are passed to8436(character,D114). LF is passed
  normally when the LF input handler invokes the sink.

8436 is the original CRT single-character putc fast path: decrement FILE
remaining count at+2, append at its pointer at+0, or call91a6 on exhaustion.
Its word resultffffh indicates error. Because capture opens in text mode, the
recovered lower write routinea368 inserts CR before LF. That lower-layer policy
is already independently documented/tested in [TRANSFER_FILES.md](TRANSFER_FILES.md).
The CR/LF behavior above must be tested together with this text translation;
it is not correct to copy the09b6 character values into a binary file and call
that the original log format.

No timestamp or capture annotation is emitted by09b6 or the ordinary open,
close and pause functions examined here. This is a bounded statement about
those paths, not proof that no application subsystem ever writes annotations.

On an ordinary non-CR putc error,09b6 loads BX from418a, calls427f, callsbb23
and refreshes2fb8. 427f is a BX-message UI thunk into429a, not a disk-error
return-code function. Since capture was active, bb23 reaches e5a4's close
branch and disables it. However the special CR->LF branch returns without
checking putc's result. Native fclose errors are also ignored. A maintained
owner needs truthful failed-write/close state rather than copying those gaps.

## Printer copy and screen printing

3988's branch in09b6 calls36fc(character). For CR it additionally emits LF when
1d24 is enabled. This printer sink retains CR even when capture drops it.
Resident36fc calls8436(character,8ff0) and then8c54(8ff0), flushing after every
character. It does not check the putc result before flushing. No retry,
unavailable-printer or printer-status recovery is established by this wrapper.

Resident1a76 toggles3988. Disabling clears the flag and closes8ff0. Enabling
sets3988 **before** opening the literal `PRN` (DS1d50) with binary mode `wb`
(DS4688), stores the returned FILE pointer, and refreshes the status. It does
not check for a null open result before leaving3988 enabled. This distinction
matters: a true flag alone does not prove a usable printer handle.

Overlay12:e2f8 prints screen rows to PRN, independently of the stream-copy
wrapper. Mode1 chooses rows0 through334c-1; mode2 chooses ce0e throughce3a
inclusive; mode3 chooses the current cursor row. For each row it positions the
cursor, reads each cell through6fa0 using video page3344, emits columns0..3258
inclusive, writes CR/LF and flushes. It then closes PRN, restores cursor
row/column and refreshes status. This path emits character bytes, not video
attributes. It performs no checked open/write/flush/close handling in the
examined function. e3ca selects mode1/2 from3982 and optionally sends a final
form-feed0ch via36fc when3980 is enabled.

These print helpers reuse8ff0. Their interactions with an already-open printer
copy stream, printer device failure and form-feed after close remain unresolved
integration cases. Opening an independent maintained printer handle cannot be
claimed to reproduce that original ownership automatically.

## Screen snapshot format

Resident3496 is a separate screen-file writer, reached by Alt-G's3496(1) call.
It opens literal `PCPLUS.SCR` (DS1e5f) with **append binary** mode `ab` (DS4716).
This appends snapshots to the existing file; no overwrite-choice branch occurs
in the examined function. Script overlay18:e8ef calls3496(0), suppressing the
interactive status/key-wait portion, while reusing the same writer.

For rows0 through runtime word7a74-1, it calls3446 to obtain character data
from either the far shadow screen (cdfa!=0) or the selected video-memory/page
path.3446 delegates to64b8, which strips attributes, converts NUL cells to
spaces, computes a length excluding trailing spaces, and leaves DF clear.
3496 appends literal CRLF at that returned length and writes the C string with
8e88. Leading/interior spaces remain; each output row ends CRLF. This is text
screen content, not a packed character/attribute RAM-window snapshot.

There is an original special case on row334c: a1Ah byte three positions before
the string end is replaced with a space. Its precise UI rationale is not
proven. The writer ignores row-write and fclose results. Open failure displays
a message via427f; the interactive mode also displays status and waits for a
key after successful writing. No `.DMP` format or consumer was proved here;
its advertised filename remains a separate F10/F11 recovery question.

## Script integration and remaining gates

Overlay18:e7ea parses an operation through4cb4:0 closes D114 and clears both
flags;1 obtains an explicit/default filename and opens `at` only if not already
active;2 clears pause;3 sets pause. Successful open clears D124 to report
script success; initial success/failure setup is visible in that branch. Full
ASPECT token grammar, parameter errors and script lifecycle are not inferred
from this isolated function.

Overlay18:e8be derives the requested printer state through4cb4 and tail-calls
1a76's toggle. The surrounding grammar/preconditions must be preserved; its
state assignment immediately before a toggle is not a generic boolean setter
API. Script snapshot e8ef is another separate entry. These observations keep
capture work connected to F12 rather than reducing F10 to one new terminal
hotkey.

Next source units worth recovering are16:e5a4 (185 bytes),16:e57a (42 bytes),
resident36fc (27 bytes),8436 (36 bytes), and1a76..1aa9 (52 bytes), reusing the
existing native CRT write/flush/close work. The prompt/window dependencies and
48a1/file-open machinery require their actual contracts. Snapshot3496 (167
bytes) needs3446/64b8, video/shadow ownership and checked output policy.

Required focused tests remain: escape/default filename; repeated append;
pause/resume and active-close; ANSI/plain input and exact CR/LF/FF/DEL bytes;
text-EOF existing log; partial/disk-full writes and close failure; truthful
status on failed printer open; snapshot row trimming, repeat append, video
versus shadow; lost carrier and cleanup; script and ongoing transfer coexistence.
This initial native inventory does not itself establish those runtime results.
The linked live-owner ledgers above now supply capture and screen-file evidence;
printer-device and full raw-monitor integration remain separate open work.

## Evidence register

| Retained original function | REA assembly Evidence ID |
| --- | --- |
|09b6 logger| `ev_59d3555c1eff09c949a0ed62a576c1f7a6107831cb7b3ba2e3c669917aec0157` |
|36fc printer byte| `ev_77f724fb00c1f481d308bbf610897fcc3ba64a77116a9d47f527765f1082a447` |
|8436 putc| `ev_9f27b2e0c4579953671867596b65615e5a6ceb853e73e9cb62527bedcb9239cd` |
|427f message thunk| `ev_ef44a4efdb769174514a8710a15e8e0fcf0dbb50e054e73d39acbbfdcd1bc457` |
|bb23 overlay stub| `ev_6cb21b5770b35c4bb0ac8484b1402683925641684956af9e2cca9d5be8cfc62f` |
|16:e5a4 capture toggle| `ev_c898e314fc45ab827c0ff83879f9defa5fcccff06616e52c9ccf8e8c8f123b7b` |
|16:e57a pause| `ev_c723041d5c69ef07a6b1db40918938ead7b33631ed149d5b4063a2516b508d07` |
|48a1 pre-open seek| `ev_fc279527a339fca93af06340199cc73d7a48533cfd56107c6e0fd826de82d9ce` |
|2fb8 status| `ev_37f3de96121de4b87b610528664677582883ea518eaecb770ba29ed10ada9cbe` |
|3496 snapshot| `ev_68337647c17ff53945a61bc81e6e08247d7b411b28e586de927f3c7e7d559fa1` |
|3446 screen row| `ev_3e80115b63239dd2e9e663e183f115b211778ed0e7eec02a76c7b9c1ec6c7a9b` |
|64b8 trim/copy| `ev_073a04b35f90a84a7ea7dfa10db55bca00d442e74f9adfe4deee25ece4413bab` |
|12:e2f8 screen print| `ev_e93d8b17d34c8a6d6de8681c47ca87d75edf0feb2859696d55402e512a275e0b` |
|12:e3ca print mode| `ev_be9ebd36f995696b314f779b0ee5314a5e078a2aae90bc1b6a63b8c9536ee2ce` |
|18:e7ea script log| `ev_577ce1fd18db1a1910c425200533e32f93bceae6cdfe1349ad7c4053af2d068e` |
|18:e8be script printer| `ev_b70b83b1a51994f5131254c85c1e2bfac98f96809f03415b86ac27c953aa45cc` |

Selected original-byte anchors, end exclusive:

| Span | EXE offset / bytes | SHA256 |
| --- | --- | --- |
|09b6..0a3a|7094 /132| `19053388706c76e4aca61da2157a8581655d4f6b4b5567d21b28b2b3ee2da6fd` |
|36fc..3717|18684 /27| `3fcb2ef101b1f1285af7967279c3007e2e4657d50345843940ca05844362401a` |
|8436..845a|38454 /36| `e3da11f827461f16ac372f756ede18ded9801ee95de1a0b90bc7355ac537de60` |
|1a76..1aaa|11382 /52| `f2d448629c2552b3871dea92dc1a4aa6c466f034587daf8bcb0ee6e1408fb223` |
|3496..353d|18070 /167| `25a650bd17aba7d58bf3e1571fe910b57fee2a6a64edd88df15f4bdca8cceb57` |
