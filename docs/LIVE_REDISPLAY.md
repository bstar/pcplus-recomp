# Serviced redisplay

Ctrl-PgUp opens the terminal's recorded history. Up/Down moves one display row,
PgUp/PgDn moves 23 rows, and Home/End selects the oldest/newest page. `/` opens a
search field; Enter searches without ASCII case distinctions, F3 finds the next
match and wraps, and Escape cancels the field or returns to the live screen.
Alt-X restores the live display and exits normally. Viewer navigation and search
text stay local. The current viewer supports BIOS mode 3, page 0, 80 by 25 cells.

The native writer now owns a separate 63,000-byte circular buffer. Redisplay
makes a chronological, frozen copy when opened: incoming bytes continue through
the UART, parser, capture and native history writer, while the page under review
stays stable. Close and reopen to review newer history. This is recorded text,
including native compressed CR/LF and backspace handling, rather than a replay
of past ANSI screen states. CP437 bytes remain literal; CR starts a row, Tab
advances to an eight-column stop, and long rows wrap at 80 columns.

The viewer preserves a private live screen and cursor. Before top-level terminal
input resumes, it restores that live screen; at idle it saves the updated display
and repaints the cached viewer. Native parser continuations share that live view.
It does not rerender the complete history for each received character. Serial
flow, normal output and incoming terminal replies keep their existing owners.
A sparse row index bounds line/page navigation. Search processes at most 64
candidate positions per foreground turn; the main loop continues polling serial
and keyboard between chunks. Escape can cancel a long search. A sustained
receive backlog can defer idle repaint and search work until input catches up;
physical throughput remains unverified.

Entry is refused while a parser, transfer, PROGRAM, macro, monitor, controller,
ANSI wait, snapshot or BREAK owns the terminal. Unsupported video/page/viewport
geometry is refused without exiting. A new connection/error notice returns to the live screen before saving its
underlay and drawing. Once open, viewer keys own local dispatch;
settings, transfer and capture prompts cannot open over the history page.

The live ring, frozen copy and two raw screen frames are distinct far owners.
They do not alias the native shadow, snapshot or the three existing packed UI
frames. MZ/map checks validate segment extents, relocated pointers and four
near/far viewer entries. PROGRAM retains every new allocation. The current build
retains 297,184 bytes including the PSP before DOS/environment overhead; this is
not evidence for the original product's 192 KB limited configuration or a full
295 KB application configuration. Physical UART throughput and video hardware
remain unverified.

## Recovery boundary

The writer and pair helper retain the recovered resident instructions at 5832h
and 58CEh. Their current REA assembly Evidence IDs are
`ev_48c26fed90db1a41e030acafe59551473a6d214b4954cc40c16504a968729250`
and `ev_3775c89edd0f1d5e0bd9d993c04b86e97018e049f17a1776a5801c6cc8c917e6`,
bound to the original SHA-256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The private retained exports live under `analysis/redisplay-native`.

Previously retained overlay-15 exports establish circular traversal and CR
expansion during file output: `ev_e854b856393980bfcdae0b4d6d559b1a9ed34e7302600cc34501f1a86e83cfdf`
(entry DB5Fh), `ev_b67855b15b831e6f70a46c8e36f8f8c2365efd7ec6b63d0d8c99bdd24dcc7688`
(E60Ch), and anchored `ev_1fbfae25e909f4dce2aacc7720d25245a1b18830da899e1d95923cfa1828e74e`
(D8BDh). These are static observations from explicitly synthetic analysis
contexts; those executables are never run. The live viewer, search scheduling,
frame swaps and fixed capacity are maintained source implementations, not a
claim to have recovered the complete original redisplay UI.

## Verification and remaining work

```sh
./tools/build test-redisplay
./tools/build test-terminal
```

[Hash-bound validation](validation/redisplay-live.json) combines 39 linked inputs,
one actual DOS observer workflow, the full 68-command terminal regression and
63 byte-identical source-only outputs.

The linked tests run actual transport dispatch, far viewer code and native
UART/parser/history instructions; only hardware/BIOS boundaries are modeled.
They check navigation, search wrapping, all 63,000 snapshot bytes at four ring
origins, independent live-screen updates, ownership refusals, a repeated-prefix
search with continued input, cancellation and 50-row refusal. A separate native
writer regression fills/wraps the complete ring and checks neighboring canaries.

The DOS workflow uses an independent INT1C observer to sample history pages,
search prompts and matches. The peer sends new text and requests a cursor reply
while redisplay is open. It checks that new text appears on the restored live
screen, viewer keys stay local, ordinary keys resume transmission, fixtures stay
unchanged and UART/PIC/IRQ state returns to its independent baseline. Actual DOS
child allocation/fill separately checks retained native-history endpoints.

History export, clipboard filename extraction/list editing/paste, full original
redisplay commands and other video geometries remain open. This implementation
does not close F11 or the full-application checklist.

[Export and clipboard recovery](REDISPLAY_CLIPBOARD_RECOVERY.md) records original
append/CRLF output and the15-entry filename clipboard behavior for the next work.
