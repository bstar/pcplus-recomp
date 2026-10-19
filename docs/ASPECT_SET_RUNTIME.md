# Native SET runtime

The production ASPECT child now links all225 recovered SET bytes and a complete
256-entry owned selector table. Eleven selectors execute native setters; the
other245 stop explicitly. The dispatcher reads through the existing checked
DOS FILE adapter and always tail-calls the status boundary after a successful
setter. The source compiler grammar and emitted bytes are unchanged.

| Setting | Actual state/consumer |
| --- | --- |
| DISPLAY | Received-lead rendering gate; translation and WHEN matching continue. It does not retire the resident renderer or suppress status/direct output. |
| DUPLEX | Native child local transmit echo. Explicit changes project HDX/FDX into the parent status row; drawing does not commit parent settings. |
| FINDCASE | Native E392 state, initialized0 for a fresh interpreter invocation. The [recovered FIND consumer](ASPECT_FIND_CASE.md) awaits application integration. |
| KEYS | Native E380 keyboard-disable word. ON stores1 and disables native local-key dispatch; maintained immediate Escape cancellation remains available. |
| MSG_CRLF | Native MESSAGE trailing CR/LF selection, initially1. |
| PAUSECHAR | Checked32..126 integer, stored as one byte; native TRANSMIT waits rather than sending that character. |
| RXDATA | Writes the existing E382 flow/deferred-service/receive-echo gate itself, overwriting its current value. It is not a separate receive-enable flag. |
| SWITCHCASE | Native E394 state, initialized0. The [recovered SWITCH/CASE consumer](ASPECT_FIND_CASE.md) awaits application integration. |
| TXPACE | Checked0..999 units consumed by native TRANSMIT; nonzero production values use the calibrated service described below. |
| WAITCASE | Actual native WAITFOR comparison mode. |
| WHENCASE | Actual native receive/disconnect matcher comparison mode. |

Native E6BB stores every raw byte0..255 as a word for boolean/duplex settings.
This corrects the earlier maintained WHENCASE-only rejection of2/255. Source
grammar still emits OFF/ON or FULL/HALF. Raw-byte acceptance does not establish
arbitrary-bytecode safety. Numeric bounds use the recovered integer readers and
existing typed native-error unwinding. GET/query helpers link to the native
integer destination service, but GET source grammar remains unsupported.

SET status uses capability2 STATUS while the UART lease is live. With an
admitted renderer, successful setters draw through the actual parent native
status body even when DISPLAY is OFF. Raw-only/offline callers have no status
drawing owner. Before an explicit child DUPLEX change, status selects the
parent's current duplex; afterward it projects the child's value. Child SET
values currently have interpreter-invocation lifetime. Original shared-session
adoption into the suspended parent and complete PRM-derived startup defaults
remain unfinished; this checkpoint does not claim those native lifetimes.

## Calibrated transmit pacing

The original startup calibration masks all master IRQs except the timer. Doing
that inside an already connected child would suppress its UART. The maintained
service therefore measures batches of the exact38-byte native6B72 busyloop
against the standard BIOS clock while leaving PIC/vector/MCR ownership intact.
It uses bounded alignment/measurement, rejects IF0, stalled/invalid clocks and
insufficient resolution, and publishes its count only after transport polling.
The calibration policy differs deliberately from native7956; see
[ASPECT_TXPACE.md](ASPECT_TXPACE.md) for measurements and limitations.

Before the one-period measurement, the child polls flow/errors/cancellation and
requires at most2048 queued bytes in its4096-byte ring. UART IRQs remain enabled
during alignment, so each alignment poll rechecks that headroom before entering
the uninterrupted measurement. A linked regression first reproduced successful
measurement after the queue grew to2049 during alignment, then verifies typed
rejection before any busyloop unit. The failed candidate is retained at
`build/aspect-txpace-history/alignment-headroom-677a/`. UART IRQs also remain enabled
during measurement; overflow and cancellation are checked afterward. This
headroom assumes the standard DOS BIOS timer and supported UART divisors (at
most115200baud). It is not a physical-modem throughput guarantee. No callback
enters WHEN, matching, parser or a resident RPC. Delay calls service low-level
transport and immediate cancellation between native units, including a final
poll. That adds cooperative overhead absent from the original uninterrupted
busywait. Changing emulator/CPU speed after calibration requires recalibration.

The actual native TRANSMIT path still decides where to pace: ordinary bytes
are delayed after sending, including the last byte. Decoded FF (`^@`) sends NUL
without local echo or pacing. A pause-character match waits ten BIOS transitions
and sends nothing. Diagnostic builds record requested units/calls without
inventing elapsed clock time; real calibration timing has separate DOS proof.

## Evidence and remaining work

[validation/aspect-set-runtime.json](validation/aspect-set-runtime.json) binds
the product pair, sources and scoped reports. The runtime suite passes853 DOS
cases/19000 checks, including38 new integration vectors,245 rejected selectors,
raw boolean2/255, numeric bounds, status-tail snapshots and pacing request counts.
Diagnostic snapshots observe actual native writes before cleanup; they do not
replace a production status renderer. Historical WHEN-only reports remain in
`build/aspect-runtime-history/when-only/`.

Six actual DOS UART cases independently check nonzero pacing wire bytes, NUL
bypass, pause-character suppression, HALF echo and WAITCASE ON/OFF, with exact
stdout, unread handback and restored IRQ/PIC/MCR/guards. Six full-terminal cases
check native status rows and owners, including DISPLAY OFF, HALF projection and
an actual paced password transmission. Existing WHEN/client/BBS regressions and
the fresh-source proof are recorded separately rather than counted as SET
semantic coverage.

The separate [FIND/SWITCH/CASE component](ASPECT_FIND_CASE.md) contains401 exact
native bytes and passes2642 CPU cases, visiting all199 recovered instructions.
Near allocation and FILE/operand boundaries are explicit models; it is not yet
linked into the application. Fresh source builds reproduce124 checked outputs.

Next work is to integrate the recovered FIND and SWITCH/CASE consumers, preserve
their source grammar and native failure behavior, then continue the remaining
ASPECT families, compiler/recorder, keyboard/UI and session configuration owners.
Full emulation/protocol/Host and physical Wi-Fi modem requirements remain open;
none of F01–F16 is closed by this checkpoint.
