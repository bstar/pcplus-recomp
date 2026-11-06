# Chat typeahead at the queue limit

The optional foreground build now keeps cancellation reachable after its
32-key deferred FIFO fills. It retains the oldest32 ordinary keys, consumes
excess ordinary keys with overflow status7, and requests one BIOS bell per
Chat session. Escape, Alt-H and Alt-X continue through their existing handlers.
This is an explicit bounded-input policy; it does not promise unlimited input.

The [receipt](validation/chat-queue-pressure.json) binds the exact build and
checks. Parent SHA256 is
36fcb9f39725c46f34356a2016bbbffdd6af7089847820277a9730dfe3175c1b.
API0104 module83b77da0…bc3eff is unchanged. Retained allocation479408,
DS=SS65504, resident CS65386, stack8192 and all stream/display/history capacities
remain within the established passing profile. No new queue or near data is
allocated; the existing macro-status word supplies the overflow-bell latch.

## Failure and maintained policy

The prior3ea9d89a parent passes a burst of32 keys. With40 ordinary keys ahead
of Escape, however, its full FIFO leaves further input in the BIOS queue.
The full36-tick wait expires before cancellation, and excess X characters
then reach the ordinary BBS wire. The failing40-key control remains negative.

The held-key path now always reads an already-peeked ordinary key and delegates
the limit decision to the existing FIFO producer. In Chat, the producer keeps
the first32 entries and consumes excess input without appending it. A single
bell request and status7 make overflow observable without a blocking bell for
each excess key. Successful Chat acquisition resets that session's bell latch.
Cancelling still clears the retained prefix when the module retires.

Outside Chat, the old full-FIFO behavior remains: cancel the macro, clear its
queue and request exit code3 with status7. The CPU fixture checks both non-Chat
owner values0/1. Disabled builds retain their old instruction path and reproduce
the exact5ecf8774 baseline.

The foreground bridge uses a near CALL preceded by PUSH CS for its same-segment
far C entry. This preserves the exact far return frame while shortening the
optional bridge. The zero-event stub also avoids an immediate word load.
Actual DOS entry/return, pressure, cancellation and nested-child tests exercise
these bridges. No stack or buffer capacity was reduced to fund the policy.

## Actual DOS evidence

The32- and40-key fixtures both run normal DOS8086 main with genuine BIOS input
and the native echo parser. Each fixture completes two Chat sessions in one
process, transmitting exactly the retained32-key prefix in each session.
It then separately tests Escape, Alt-H and a single Alt-X behind a full queue.
The40-key excess is deliberately discarded; it is not reported as delivered.
All cancellation cases require prompt retirement and no abandoned X/TAIL on
wire. Ordinary input and configured hangup/exit still work afterward.

The passive observer records the maximum FIFO count, overflow status and BIOS
INT10 bell requests.32 keys produce no overflow bell;40 keys produce one per
session, including a fresh bell after the second acquisition. This verifies
software bell requests, not physical speaker audibility. The helper tail-chains
the original INT16/INT10 providers without manufacturing product state or keys,
and verifies both original vectors were restored before writing its result.

The nested-ASPECT test separately retains all six streams across three NOCLEAR
DOS children and checks exact viewport return. Native echo/IRQ/clock tests,
all ten TEXT keys, queued cancellation during serial XOFF, source-only export,
stock Synchronet editor/viewer and Enigma carrier-loss/redial/exact-retry checks
remain separate evidence with their declared scopes.

The serial-stall fixture also fills the FIFO with40 keys before Escape. Its
observer requires UART pause still set at first retirement, retained count32
and an empty FIFO afterward, with no X/TAIL leaked to the wire. The initial
fixture released XON after1.2 seconds, before the larger burst could finish;
that failed fixture is retained. The corrected pressure fixture holds XOFF for
3 seconds and explicitly checks retirement precedes XON. This is synthetic
test timing, not a production modem or bridge change. Single-key cancellation
and ordinary XON completion remain separate passing cases.

Physical CTS/RTS, sustained saturation, printer/logging/geometry and retirement
failures, mixed extended-key pressure, original Redisplay from Chat, global
Help/Alt-Z/configuration, package deployment and physical analog/SIP/audio
acceptance remain open. The installed DOS package is unchanged.
