# Menu entry during a partial ANSI sequence

The maintained terminal now defers an otherwise eligible Alt-Z request until
normal receive parsing yields. Following keys stay in the existing32-word
foreground typeahead FIFO. They become menu input after the live screen is
saved and all opening guards are rechecked. No new key buffer is allocated.

The controlled before/after DOS probe sends an incomplete `ESC [` and completes
it1.7 seconds later as a color command, text and a cursor-position query. Alt-Z
and two Right keys arrive during that interval. On the earlier `c0d64834` build,
the actual BIOS-read observer records `terminal_parser_active=1`, other opening
guards clear, and the menu never opens. Both Right sequences reach the synthetic
remote peer. The new build retains the request and keys, opens after parsing,
and sends the actual cursor reply plus later ordinary typing without leaking
those arrows.

This reproduces a specific refusal class. It does **not** establish why the
earlier stock Synchronet attempt missed the menu. A separate instrumented run
using its original1500ms recipe succeeded on the unchanged earlier executable;
its observed guards were clear. That observer changes memory layout and timing,
so the original isolated refusal remains unattributed.

## Policy and ownership

Only normal parser ownership can defer Alt-Z. Macro, PROGRAM, transfer,
monitor/controller, ANSI discard-wait, snapshot, BREAK, modem-control and
unsupported geometry retain their existing refusal policy. Redisplay and direct
clipboard hotkeys also retain their parser-busy refusal behavior.

The distinct resident `terminal_menu_pending_poll` service checks a pending
request at foreground polls and preserves AX. It calls the existing key entry
with the retained Alt-Z intent only when parsing has yielded. Every BIOS key
value retains its original key meaning: the recovered keyboard can return AX0,
which is tested through the real view-key event rather than used as a signal.
Repeated Alt-Z coalesces. Pending navigation uses the same FIFO as older deferred
keyboard input, so an existing prefix stays before newly read keys. The queue's
existing33rd-key overflow policy stops explicitly with exit3.

Escape cancels the pending request locally. Alt-X and Alt-H cancel it, then use
their ordinary exit/hangup paths. Cancellation, foreground stop and failed
opening revalidation discard the owned typeahead. That discard itself changes
neither macro execution state nor the UART TX queue. Parser replies use their
normal transport. A newly active unrelated view is preserved rather than
reentered. Revalidation includes the C-side mode/page/height/history checks.

The two-byte request flag adds16 bytes after alignment to near data/stack,
now64,192 bytes. Resident code is64,932 bytes, with604 bytes spare. The existing
85 far bridges and argument contracts are unchanged. The retained parent,
including PSP, is312,848 bytes.

## Evidence boundaries

`check_menu_pending_live.py` executes linked product code with modeled hardware.
Its36 declared inputs cover deferral without another key, FIFO order, local and
emergency cancellation, late guard failure, unrelated-view preservation, queue
capacity/overflow, repeated requests, unchanged non-menu behavior and real
zero-valued key delivery to menu/history/clipboard owners.

The ordinary command-menu DOS suite adds a fourth workflow with the split ANSI
sequence. An independent INT1C observer sees the View group after the queued
Right keys. The peer verifies the real cursor reply and absence of arrow bytes;
the final screen and typed output prove normal service resumes. This workflow
does not read application state.

`probe_menu_parser_dos.py` separately uses `menu_guard_watch.asm` to read guard
words at actual BIOS key returns. Its map-derived offsets, CS/DS/SS checks, raw
records and observer source are retained. Unlike the behavioral observer, this
diagnostic deliberately reads application memory; it never writes it, supplies
keys or replaces product callbacks. The TSR chains the actual BIOS read,
preserves its return registers/status, restores its INT16 vector and verifies
that restoration when collected.

The stock transfer diagnostic adapter in `lab/bbs/menu_guard_probe.py` only
installs/collects that TSR around the existing harness's DOSBox process. It does
not change its peer, terminal input, framing or validation. A successful
instrumented attempt does not override an earlier unobserved failure.

```sh
./tools/build test-command-menu
./tools/dev --command python3 standalone/probe_menu_parser_dos.py \
  --label YOUR_FRESH_LABEL --sha256 YOUR_TERMINAL_SHA256 --expect deferred
```

[`validation/menu-pending.json`](validation/menu-pending.json) binds the raw
before/after guard records, baseline source commit, linked checks and independent
DOS workflow to the current executable. The baseline probe and executable
identity are retained separately from the current runtime. Source-only reconstruction, original UI parity, other terminal
emulations, physical UART/modem validation and the remaining application plan
continue; no whole-application gate is closed by this change.
