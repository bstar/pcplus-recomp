# Cancellation behind Chat typeahead

The optional foreground TEXT build now retains ordinary keys in the existing
32-word deferred FIFO while Chat cannot accept them. Escape, Alt-H and Alt-X
can then reach the BIOS queue head and cancel a blocked native echo. The FIFO
is replayed when TEXT can accept input again, or cleared when Chat is retired.
This is a maintained input policy, not execution of the full original Chat
controller. The installed package and physical PC are unchanged.

The [validation receipt](validation/chat-queued-keys.json) binds the exact
parent, unchanged API0104 module, current source and positive/negative evidence.
Parent SHA256 is3ea9d89a3ad29a3ee5cdeec4a188f126375dccfe3a5ae66e08f42f18efff4fb0.

## Failure reproduced

The previous7497a973 parent passes cancellation at the BIOS queue head. With
ordinary X typed first, however, all three cancellation keys remain behind it.
The actual DOS control observes36 BIOS ticks of native wait, then retirement
at37 ticks; X is subsequently emitted to the BBS. A whole-process successful
exit alone therefore does not prove prompt cancellation or safe typeahead
retirement. The control report remains a failing result with its exact old
producer identity; its earlier observer/test revision is not relabeled current.

## Input ownership

The normal BIOS peek still precedes every actual read. When the frontend holds
an ordinary key, the parent reads that already-available key into the existing
FIFO instead of leaving it ahead of cancellation in the BIOS queue. A full
FIFO holds further input without calling the overflowing producer. A held
Escape stays in the BIOS queue until its existing phase barrier clears.

Before removing retained input, a zero-key frontend query asks whether the
current TEXT/native continuation can accept it. An empty FIFO bypasses that
query, avoiding an extra frontend call on ordinary polling. Module-busy paths
never reenter, unload or change its request. They only retain input through the
existing parent producer and let the established cancellation dispatcher run.

Chat admission already requires an empty deferred FIFO. Once the foreground
owns Chat storage, native echo permits its bounded retained count0..32; counts
above32 still refuse before output. Earlier non-foreground echo builds retain
their empty-FIFO requirement. Pending typeahead consequently cannot reject the
next byte of an otherwise valid native echo operation.

After the module has finished retirement, the frontend release calls the
existing macro-cancel service to clear the retained FIFO before releasing
storage. Ordinary completion preserves keys for the local Chat pane; session
cancellation or failure abandons its retained keys. In particular, the tested
X ahead of Escape/hangup/exit never becomes ordinary BBS input after return.
The implementation adds no queue, near data, heap, stack or module ABI field.

The FIFO remains bounded at32 entries. Full-FIFO/BIOS residual pressure and
broader retirement-failure cases still need dedicated tests; the finite native
wait deadline is unchanged. This checkpoint does not claim unbounded typeahead
or out-of-order cancellation through a completely full pair of queues.

## Memory and ABI

The parent retains479408 bytes, the existing passing foreground budget. Its
DS=SS65504 bytes, resident CS65368 bytes, application stack8192, all six script
stream buffers and the interpreter's512-byte growth policy remain unchanged.
Actual DOS nested-ASPECT testing separately checks three NOCLEAR children with
all six streams held and exact viewport recovery.

To fund the input gate, the optional assembly bridges use the C result's
nonzero value directly as carry before restoring registers, compute the storage
claim's boolean result without a branch island, and tail-call the storage
release after FIFO cleanup. The old non-foreground branches remain available
byte-for-byte; the disabled build reproduces5ecf8774 exactly. An initial
prototype placed the carry edit in the wrong conditional branch; review caught
it before DOS execution, and that untested image is not accepted evidence.

## Evidence and remaining work

The queued BIOS fixture runs actual DOS8086 main with imported TEXT and the
native parser. Its passive INT16 observer sees X in BIOS before dequeue, the
retained FIFO count during the wait and an empty FIFO after retirement. Delayed
CSI completion preserves X/Enter order. Separate X-before-Escape/Alt-H/Alt-X
cases require prompt retirement, no later TEXT bytes and no abandoned X on the
wire. The observer only writes its own buffer and chains the BIOS provider;
it does not manufacture product state, keys or UART data.

The actual serial XOFF/XON fixture also tests X before Escape while TEXT's T
byte is held by flow control. It observes remote RXD during the stall, retained
X, retired TEXT/owner and an empty FIFO, with neither abandoned X nor TAIL on
the physical synthetic wire. The ordinary XON-completion case remains separate.

Eight CPU groups cover the native echo/parser/IRQ boundaries, now including
retained counts1/32 and a refusal at33. Owner/cursor are supplied preconditions
and hardware remains modeled there. A fresh public source export rebuilds the
exact parent/module/header and repeats actual queued BIOS cases plus the CPU
suite without originals, private settings, prior objects or ancestor Git.

Stock Enigma and Synchronet regressions use ordinary terminal workflows with
Chat inactive. They do not establish interactive Chat inside each BBS, perfect
rendering, hardware CTS/RTS, sustained saturation, printer/logging failure,
all geometry/mouse/binding lifetimes, Chat Help/Alt-Z/configuration, final
package deployment or physical analog/SIP/audio acceptance. The wider original
feature-parity inventory remains open.
