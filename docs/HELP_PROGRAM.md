# Source-built PCHELP interface

`src/help/program.c` now builds a standalone source-owned `PCHELP.RTE` which
accepts the original `PCHELP <decimal DS:offset>` process arguments. The
recovered132-byte parent producer launches it successfully under actual DOS.
It admits the descriptor through the
[parent PSP/MCB service](HELP_PARENT_ADMISSION.md), reads an HLP resource through
the existing bounded streamed reader, and displays an original-derived Help UI.
The opt-in [global Help profile](GLOBAL_HELP.md) now wires reference context41
through the terminal's PROGRAM owner. It is not selected for the physical
machine.

The matched interface has a full-width topic/title header, right scrollbar,
bottom key reference, scrollable text, `T` topic selector, `S` search dialog,
and `C` continued search. Topic selection remembers its last selected row.
Search highlights matching text and asks once before continuing into other
topics. Escape restores the calling screen and cursor. The caller supplies
the title, normal/bold/reverse attributes, context and raw UI words through the
legacy descriptor. The source helper uses no vendor executable or help text
as a build input.

## Runtime comparison with the original

[The receipt](validation/help-program.json) binds source/product identities,
the independent original/source comparison, public golden hashes and the cold
rebuild. The current helper SHA256 is
`f163169fd4c4bf2d47a3a78879b8cb3cc4d9d255aa467e892bbca5e6db5dc57b`.
The MZ minimum DOS block is30384 bytes including PSP; the display snapshot
adds4000 or8000 bytes plus file/runtime allocations. DGROUP is9824 bytes with
the retained8192-byte stack. These are build measurements, not proof that the
helper fits alongside the full terminal and every active resource owner.

18 original/source pairs run actual DOS8086 at25 and50 rows. Each uses the
same source-built native descriptor producer, authored47-topic/1880-line HLP
and diagnostic BIOS keyboard observer. The resource is78869 bytes; selecting
and searching topic46 exercises file positions beyond64KiB. The workflows are:

- Topic-selector cancel, selection, Home/End, paging and remembered row.
- Main Up/Down/PageUp/PageDown/Home/End navigation, including short pages.
- Search text entry, Backspace/cancel, highlighting, continue/decline,
  continue/accept, a later-topic match and a complete no-match search.
- A negative signed context selecting topic zero.

At every scripted BIOS keyboard read, the observer copies the actual VGA text
plane and BDA cursor position/shape. All144 corresponding snapshots match in
every visible byte, including attributes, and all cursor states match. Both
programs restore the exact patterned background and original cursor after
Escape. No helper instruction, state word, display function or key handler is
patched. The observer temporarily owns INT16 and supplies declared key reads;
this is not physical keyboard or mouse acceptance.

The original helper's normal Escape returns raw process exit byte35, which is
recorded separately from launch/capture success. The source helper returns0 on
success and typed nonzero startup/runtime failures. The capture harness does
not silently equate the original's nonzero exit byte with DOS launch failure.
The terminal's future launch policy must account for that distinction.

The source-only regression uses public original-derived frame hashes and
cursor states; it does not load an original executable or HLP. A fresh24-file
source tree reproduces the helper byte for byte and repeats all18 sessions.
It contains no configurations, prior objects, original programs or analysis
artifacts. These tests validate selected helper behavior rather than a full
terminal/modem/PROGRAM ownership composition.

## Corrections established by evidence

The first actual original capture showed the full-screen interface and the
nonzero normal exit byte. An initial authored CRLF fixture also exposed the
native reader's visible CR byte; the comparison fixture now uses authored LF,
matching the historical resource convention. The maintained streamed reader
continues to accept and strip CRLF as well.

Initial source comparisons exposed a one-cell topic-label offset and search
prompt centering difference. Subsequent navigation checks showed that native
PageDown permits a short last page instead of always clamping its top to the
last full page. Boundary keys explicitly move the scrollbar thumb even when
the text cannot move. Short-topic searches also place the thumb at the bottom
when their top offset is nonzero. These behaviors are now preserved.

Cursor checks found differences invisible in a text-plane capture: hiding must
preserve the existing cursor shape bits, topic selection uses the original
off-screen cursor position, and the search confirmation must expose its input
cursor. All are included in the accepted comparison. The broader search case
also verifies that accepting the other-topics prompt authorizes the remaining
scan, without asking again at every topic.

Static REA checks corroborate rendering/navigation rules:

| Original helper procedure | Evidence |
| --- | --- |
| 0D9D scrollbar position | `ev_462c9820877e6dfa4f40fa7f2fc1ab2294521e36369a6bbc3e08d19f882e625a` |
| 0C40 streamed body display | `ev_e1e1077db8eae549d6195f25cf7278519b6bb077cf495fce49fdff1e5f251d55` |
| 0A11 Down boundary | `ev_13cc3106bc98434ec5efcab1e5bb771d562656b5b073019919a3938d00e857a1` |
| 0B27 PageUp | `ev_76846e4cd6225628eccaa4ac337f52437f525a0e189e07a05174f730446c8a9d` |
| 0978 End | `ev_743199c67802387d85f1144c68d7c416375ddc3499f9993f0b50048bef5bbd4b` |

The original helper identity remains
`5d135afc5808ddec923ec027f385490c7ecd4fa5004d11cefe6ff4a3c468d0aa`.
Selected static records are retained in ignored
`analysis/help-program-layout-20261106.rea.json`; REA is closed. The original
helper itself was executed only in the explicit DOS reference comparisons,
not in source-only builds/tests. No synthetic analysis image was executed.

## Build and remaining integration

```sh
./tools/build help-program
./tools/build test-help-program
./tools/build test-help-program-source
```

Each Make invocation creates a fresh timestamped output. For a chosen location:

```sh
./tools/dev --command python standalone/build_help_program.py --output build/help-program-new
./tools/dev --command python standalone/test_help_program_source.py --build build/help-program-new --output build/help-program-new-tests
```

This is a maintained C implementation derived from native evidence and checked
behavior, not an assertion of byte-identical recovery of the original helper.
The accepted display is color mode3/page0,80 columns at25 or50 rows. The source
admits other heights25..50, but those have not passed this runtime matrix.
Monochrome/wide layouts, all input-editor keys/mouse actions, audio, allocation
and file faults during interaction, asynchronous geometry changes, long search
cycles, maximum line/count boundaries and arbitrary HLPs remain unaccepted.
Body painting currently clips to77 columns to protect the scrollbar; complete
native behavior for longer lines remains open. Unsupported display admission
fails before painting, and changed geometry is not restored with a stale copy.

The next application work is bounded resolver admission for the native producer,
global context/Alt-Z mapping, launch through the terminal PROGRAM owner, helper
memory budget under the full parent, serial flow/carrier continuity and failure
return. Real authored context content and packaging also remain. The HLP in
these tests is deliberately an authored fixture, not the final user help file.
The source helper adds no new serial/SIP/Telnet handling.

No terminal package, selected deployment, physical files or private configuration
were changed. Boca/SPA2102/SynthModem acceptance and the full-parity inventory
remain in the active objective.
