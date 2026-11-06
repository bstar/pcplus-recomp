# Chat panes and translated incoming characters

`src/chat/screen.c` implements the native Chat pane contract in a separate code
bank, using a caller-owned far frame and30-byte far context. It is not bound into
the selected application. This extends the
[serviced send owner](CHAT_SERVICED_OWNER.md), which remains a separate component.

## Native evidence and scope

REA recovered the original resident3D94..3EA4 renderer (272 bytes) and6C4A..6C5E
BIOS character wrapper (20 bytes). Both assemble exactly against the genuine
2.01 file. Four previously recovered cursor units contribute370 more bytes to
the reference: cursor-left, cursor-state update, cursor packing and cursor output.
The reference therefore executes662 native bytes;292 are newly recovered here.
Flat and relocatable assembly of both new units succeeds.

Renderer assembly Evidence is
`ev_40efa426d77ee29c087a8e5cb41f6a1445d395674ff05ba430b335656e1aa188`;
the BIOS wrapper is
`ev_e1e8bee0fadd11cbb037fff1c36e3cd0b42089eff3ad5b8e29c9d0dbb944df33`.
Original identity and ranges are in
[`character-provenance.json`](../reconstruction/chat/character-provenance.json).
Complete REA records remain in ignored `analysis/chat-character-20261106.rea.json`.
The original3FB0 clear entry was not a defined Ghidra procedure; its raw original
instructions establish a clear using DS1D32, independent of text DS1F70 and bar
DS1D38. Undefined procedure status is not evidence that its bytes are absent.

This checkpoint covers ordinary80-column, single-width panes with reverse-wrap
off and no horizontal viewport. It does not claim other terminal emulations,
double-width attributes, reverse-wrap semantics, original screenshots or font
pixel equivalence. Those are explicit remaining application gates.

## Display and input contract

The native controller places REMOTE at row0/column36, LOCAL at the dividing row/
column37 and the Escape footer at the last physical row/column25. At25/28 rows
the remote region is rows1..18 and the local region starts20; above28 the remote
region ends32 and local starts34. The local region ends one row before the
footer. Remote starts at its bottom row, local at its top. The original25-row
DS334A default is23. The maintained owner supports the already-admitted
25/28/43/50 geometries; this is not physical acceptance of all four.

The initial clear, character/scroll-fill and bar attributes are independent.
The default original values are17h,17h and71h respectively. Each pane keeps its
own cursor; writes and scrolling preserve every cell in the other pane and the
three label rows. Last-column output wraps immediately and scrolls only the
active region when it is at the bottom.

For these positive-top regions, CR advances and returns to column0; LF alone
is ignored. Tab moves to the next eight-column boundary without writing spaces;
a boundary beyond79 returns to column0 on the same row. Backspace moves left
when possible and blanks that cell; at column0 it blanks the first cell without
reverse wrapping. Other byte values are literal BIOS-style glyph codes, not
ANSI escapes. Local character input uses the low byte of the original key word.

Incoming input passes through a supplied256-byte far translation table.
Translated NUL is suppressed as in the original controller. Other values reach
the remote pane. The original ANSI parser is not replaced by this renderer;
the eventual Chat receive owner still needs explicit integration and restoration.

Scrolling uses forward overlapping REP MOVSW followed by an80-cell REP STOSW
fill. All local values are loaded before temporarily changing DS; DS/ES/SI/DI
are restored before returning to C, with DF clear. This avoids a per-cell far
copy loop. The actual DOS output is verified, but no physical speed or UART
interrupt-latency measurement is claimed.

## Checks

The actual DOS8086 far-bank fixture compares4837 complete frames and both pane
cursors, after every operation, against the native CPU reference. It uses separate
DOS allocations for context, guarded frame and translation table. A runtime
check rejects a same-CS frontend/bank layout. Tests cover all256 raw byte values
in both panes, translated input, suppressed NUL, high key words, CR/LF/tab/BS,
first/last rows and seven cursor columns, sustained interleaved input, scrolling
and separate clear/text/bar colors. Unsupported geometry, short capacity,
invalid attributes/panes/cursors and near-offset wrap are refused without frame
or valid-context changes.

The native reference uses the real recovered cursor instructions and BIOS wrappers.
BIOS09/02 and scroll2530 remain explicit narrow single-width model boundaries;
the result is not a complete BIOS/scroll-shadow/viewport equivalence claim.
The DOS side executes the maintained production renderer, not a copy of the
reference model. Comparisons cover4000 bytes at25 rows through8000 at50 rows.

A separate16-file source export excludes originals, prior objects, private data
and Git metadata. It rebuilds the DOS fixture exactly and repeats all4837 frame
checks. Report and executable hashes are in
[the receipt](validation/chat-screen.json). Earlier failed/intermediate attempts
remain local; final receipts bind the current source, including separate clear
color and native REP copy.

The [composed Chat session](CHAT_SESSION.md) now checks incoming rendering while
the send owner is backpressured. Next integrate Alt-O/reference/browser, real receive/TX/log/history,
KEY/help and deferred notices. Verify foreground admission, hardware cursor and
frame restoration, no dropped input, conventional-memory headroom and the full
Enigma/Synchronet connection gates before selecting a package. No physical file,
selected package or production SynthModem service changes in this checkpoint.

```sh
./tools/dev --command python standalone/test_chat_screen_dos.py \
  --output build/NEW-chat-screen
```
