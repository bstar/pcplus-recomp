# Chat Help during native parser work

The unchanged6fd8aafc parent now passes actual DOS8086 Help admission while
Chat TEXT is inside the native echo parser. Eight sessions cover25/28/43/50
rows, each with either one ordinary key followed by Alt-Z, or31 ordinary keys
followed by Alt-Z. The latter reaches the existing32-key FIFO capacity exactly.
[The receipt](validation/chat-help-busy.json) binds sources, products, raw
captures, cold rebuild and the negative observer control.

```sh
./tools/dev --command python standalone/test_chat_help_busy_matrix.py --package build/chat-help-review-20261106 --output build/my-busy-help
./tools/dev --command python standalone/prove_global_help_source.py --package build/chat-help-review-20261106 --output build/my-busy-help-source --busy-help
```

Use new output directories. No application change or deployment is part of
this checkpoint. The same product's earlier [BBS and recovery evidence](CHAT_HELP_RECOVERY.md)
is retained by identity; those BBS cases were not rerun here.

## Actual admission and input

An imported source-owned KEY TEXT sends `GO`, then echoes ESC through the real
native parser. The synthetic UART peer supplies the delayed CSI continuation
after one second. Real BIOS typeahead puts ordinary `X` keys ahead of Alt-Z
during that wait. A passive INT16 observer validates the parent DS=SS, loaded
module header/API, foreground TEXT operation, Chat owner and native parser/wait
state before recording the queued Alt-Z and maximum FIFO occupancy. No pending
or active PROGRAM request may be observed while the native wait is active.
All observed wait spans remain below the unchanged36-BIOS-tick deadline.

At Help, a passive timer verifies Chat owner2, parser/wait both zero, and active
PROGRAM kind11. After Escape it verifies Chat owner2 and no parser/wait. The
entire saved Chat frame and cursor must return, followed by exact wire order:
TEXT `GO ESC TAIL CR`, the retained `X` line with CR/LF, then ordinary terminal
input after Chat exits. Local echo is deliberately enabled in this fixture,
so the buffered Chat line's LF is required, not treated as optional. Retired
typeahead must be empty and no Alt-Z/NUL or excess `X` may leak to the wire.

The before-frame is the actual PROGRAM snapshot read while the helper is
visible, not a separately sampled earlier VGA frame. This avoids requiring a
timer interrupt in the tiny interval between dequeuing the last ordinary key
and admitting Help. Return-frame and cursor checks remain independent actual
VGA/BDA observations.

## Loaded code identity

The INT16 observer saves all11396 initialized Chat image bytes during the
native wait. The host independently rebases the four relocation words in the
source-built MZ and compares every byte against that saved image. The timer
then byte-compares the live image at the same segment against the saved copy
while Help is visible and after Chat resumes. Parent DS and module segment
must remain the same at these samples. Mutable session state and unused window
padding are not mislabeled as immutable code.

A negative run changes only the last byte of the observer's private saved
copy, offset11395. It must fail the independent product-image comparison and
both live-image comparisons while every other check passes. The product image,
parent state and VGA memory are untouched. This confirms that the comparisons
cover the final byte, rather than accepting only a header or prefix match.

These are sampled code-identity observations. They do not continuously trace
every instruction or independently read the private loader handle. Allocation,
unload/reload and presentation fault injection remain separate requirements.

## Fixture corrections and cold reproduction

An initial expected wire string omitted the fixture's configured LF; the
accepted check requires the exact observed/native CR/LF policy. The initial
three-second pause before Escape also closed full-queue43/50-row Help before
the timer obtained two stable frame samples. Those captures had seen the
helper header but no stable frame. A longer diagnostic pause passed the50-row
case; the final script leaves6.5 seconds before Escape. Application code,
native deadlines and strict comparison conditions are unchanged. Earlier
failed and diagnostic captures remain in ignored build storage.

The clean public-source export rebuilds all four products exactly and repeats
reference Help normal/flow, normal Chat Help25/50, and the two busy Help cases
at25 rows. The eight-case height matrix runs separately against identical
products; it is not claimed as eight cold-export sessions. No original binary,
private configuration, previous object or analysis database is a build input.

Help beyond FIFO capacity, other pending native controllers or TX flow stalls,
geometry/allocation/lifetime faults, Help during an actual BBS session and
physical Boca/SPA2102/SynthModem acceptance remain open. Other Help contexts,
ASPECT/emulation/protocol gaps, Host mode and full original parity remain in
the [application inventory](FEATURES.md).
