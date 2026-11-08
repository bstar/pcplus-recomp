# Current compiler-bridge reliability checks

The unchanged17-file compiler-bridge candidate now passes BUSY cleanup, three
ordinary calls in one DOS process, a five-minute paced receive test and four
stock-BBS editor snapshots. All four logical screens match an independent cell
reference exactly. The [validation record](validation/aspect-compiler-reliability.json)
binds these results to the exact [packaged candidate](ASPECT_COMPILER_PACKAGE.md).
These are software checks; the physical installation and selected package remain
unchanged. A [fifth editor snapshot](ASPECT_COMPILER_NAVIGATION.md) adds explicit
Backspace and up/down/right semantics with another exact1920-cell comparison.

## Reconnect and sustained receive

Actual DOS8086 COM3/IRQ5 tests cover BUSY then bounded exit, BUSY then successful
browser redial, and three successful calls separated by local hangups in one
parent process. The three-call case requires three complete initialization/dial
pairs, three actual CPR/DA responses and exactly one each of the typed words
one/two/three. PRM, application bytes, UART/PIC/vectors and DOS return are checked.
The modem peer is synthetic; this does not reproduce the reported physical lockup.

The endurance case schedules601 ANSI frames over300 seconds. Every frame's
cursor response arrives in order; delivered bytes, final row glyphs/attributes,
a real Alt-Z/return and subsequent keyboard input are checked. The measured DOS
runtime must also exceed300 seconds. BOTH flow is selected. This is paced
receive endurance, not saturation throughput or physical CTS timing.

The older fixtures contained deliberately opaque A5A5 display values. The current
startup importer correctly refused those before dialing. The fixtures now supply
valid explicit25-row/status-visible preferences only when the selected parent
imports display settings. The old two-step reference/browser redial recipe also
failed to issue a second dial; the repeat uses the documented direct browser
route. Those failed runs remain excluded from acceptance.

## Stock editor and local helper return

All sessions use the actual SynthModem Telnet proxy and owned loopback servers.
Enigma's baseline editor test covers its existing Home/End, Insert/Delete, Tab,
page-key and Ctrl-Y recipe, plus an observed Alt-Z/refusal and return. Two more
sessions enter24 numbered document lines and exercise Page Up, then Page Up with
Page Down. They require the exact numbered viewport, document-coordinate
transitions, edits and final footer. The initial Page Up semantic audit rejected
an8000-byte extended video capture solely because it expected4000 bytes; its
body, footer text and page transition already matched. The corrected semantic
oracle checks the first display page and accepts the two supported capture sizes.
It does not search extra video memory for a footer.

Synchronet runs the matching ASPECT interpreter's automatic login script, enters
its stock editor, opens the source keyboard mapper and context17 Help, saves a
selected profile in an existing seven-profile synthetic KBD, returns to the exact
editor frame/cursor and continues ordinary editor input. The real application
exit status is zero. Official message/mail/transfer state must remain unchanged;
no draft is published by these tests.

Independent audits compare all1920 logical cells and cursor replies for each of
these four25-row/status-visible snapshots. Every cell matches. Two corruption
suites each accept the original capture and reject eight variants: changed glyphs,
attributes, bottom-row cells, cursor, truncated prefix, unsupported font selection
and truncated proxy input. The reference uses the complete delivered prefix at a
real final CPR boundary, with explicitly documented non-cell font probes. Font
pixels and every intermediate frame are outside this oracle.

## Laboratory status-wrapper memory

The first Synchronet mapper workflow cannot load ASPECT. A bounded real-DOS EXEC
trace records error8 with8565 free paragraphs (137040 bytes). ASPECT's MZ minimum
is136480 bytes before DOS copies its environment. The ordinary status-report
wrapper consumes part of that already narrow conventional-memory margin.

The optional high wrapper places the test launcher in UMBs, preserves its entire
owned environment and selects ordinary first-fit allocation before launching the
application. It restores the inherited allocation strategy before returning.
The environment copy is compared byte for byte before the old owned block is
freed; an already-high environment is handled too. The test does not move PCPlus
or its interpreter high or reduce their capacities. The default wrapper remains
byte-identical. This helper is not included in the17-file application package.

Four isolated DOS controls verify a conventional-memory child with a high wrapper,
inherited synthetic environment values, known child exit17, missing executable
error2 and refusal when the wrapper is not high or UMBs are absent. Allocation
strategy and complete MEM reports match before/after. The final Synchronet run
also checks the environment-copy proof and actual application exit status.
The upper-memory selection follows the DOS allocation interface documented in
[FreeDOS's definitions](https://github.com/FDOS/kernel/blob/master/hdr/mcb.h) and
[allocator](https://github.com/FDOS/kernel/blob/master/kernel/memmgr.c); these are
API references, not new runtime dependencies.

## Remaining acceptance

Physical deployment, private configuration, memory admission and the complete
Boca/SPA2102/SynthModem route still require the user's machine. Additional
stock-editor Backspace/right/up/down semantics, saturation/CTS timing and other
profile/geometry/owner combinations remain separate work. Full ASPECT, every
advertised emulation/protocol, Host mode and native helper/UI equivalence remain
in scope under F01–F16. This checkpoint closes none of those whole-feature gates.
