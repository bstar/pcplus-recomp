# Capability18 BBS regression checkpoint

The staged normal terminal `61757956` and ASPECT `b61f3a03` retain separate
software evidence from the installed physical release. The exact hashes and
reports are bound in
[`validation/snapshot-lease-bbs.json`](validation/snapshot-lease-bbs.json).
No package selection, deployment or production bridge restart is performed.

## Stock editor return

Both owned stock Enigma and Synchronet pass actual editor sessions through the
isolated SynthModem Telnet proxy. Inside an unsaved editor, the ordinary Alt-V
command invokes a source-built COM viewer with parameters. That child leaves
graphics mode13h active. A completion marker gates capture after the real child
returns; the complete4000-byte editor frame, cursor and shape match, and normal
editing continues. The fixture does not alter product memory.

Each final editor also matches an independent interpretation of the actual
delivered stream at a real CPR boundary:1920 cells per server, zero differences,
matching cursor. Enigma uses DOS8086; Synchronet uses a separate386/XMS/UMB
profile and authenticates the current ASPECT login. Its passive observer and
keyboard producer must both be loaded high. This is not an8086 conventional
memory claim for that instrumented Synchronet workflow.

Six compiled fixture controls remain identical to their historical baseline.
Five copied corruptions (cell, cursor, premature completion, child argument and
leaked local parameter) are rejected. The recorder now binds its selected runner
to the actual Synchronet producer rather than hardcoding a historical child
hash; a copied mismatched runner identity is explicitly rejected too.

The terminal's external viewer command is separate from nested ASPECT PROGRAM
SAVE. These BBS sessions exercise the current parent and the scripted login;
they do not replace the direct lease ownership/recovery tests.

## Larger BBS layout

A separate DOS8086 Synchronet session passes at50 physical/logical rows with
the status line hidden and a size-probed NAWS80x50. All4000 cells and the actual
cursor match the independent reference. The current ASPECT login, editor input,
normal abort of the unsaved post, unchanged message bodies and hardware/settings
checks pass. This establishes the BBS layout, not a nested8000-byte SAVE lease.

## Transfers

The current normal parent passes all16 independent DOS8086 transfer cases:
XMODEM CRC/NAK retry, binary receive/send, local Escape and peer CAN; YMODEM
binary batches, local Escape, same-process cancellation/retry, retention of an
earlier file after a bad subsequent header and NAK retry; and ZMODEM receive
CRC16/CRC32 and default/escaped upload with the pinned independent lrzsz peer.
Actual parser/keyboard return, cleanup, configuration and UART/PIC/vector
restoration remain checked by the existing harness. These independent peers
are distinct from real BBS helpers.

The normal parent also uploads and then downloads the exact same65539-byte file
through the isolated proxy to stock Enigma's actual transfer helper. Independent
audits in both directions verify raw Telnet and
application stream identity, the owned size prefix and NAWS80x24, all256 byte
values, embedded size-negotiation lookalikes, sender CRC/length/ZEOF/ZFIN/OO,
opposite protocol controls and exact destination. Upload also verifies official
FileEntry metadata. These are separate DOS processes and sessions; they do not
prove same-process reconnect or cancellation composition.

The first download used the default30-second transfer wait. It advanced into
later local input before completion: the observed receiver response began at
85.566 seconds and the eight-CAN cancellation began at119.075 seconds, a33.508
second interval. That failed run is retained and excluded from acceptance. A
fresh run with the explicit90-second wait used for upload passes all unchanged
protocol, byte, storage and post-menu checks. No application or bridge change
was required. This demonstrates the fixture timing limit rather than accepting
the failed transfer as successful.

## Scope and remaining acceptance

The lab runtime is the existing `menu-size-accepted-20261104/candidate` snapshot.
Its source hashes are verified before/after each session. The proxy uses250ms
input framing and20ms byte pacing. It owns Telnet; the DOS client talks to a
synthetic Hayes serial modem. No running production service is reconfigured.

Actual SIP/audio/DSP, Boca CTS timing, the physical Enigma header and sustained
hardware operation need physical acceptance. Current-pair real-BBS
[cancel/retry now passes](SNAPSHOT_LEASE_RECOVERY.md). The carrier test found
DOS insufficient memory while launching ASPECT; carrier-loss/reconnect remains
unaccepted for the old child. The separate
[deferred-storage candidate](DEFERRED_SCRIPT_BUFFERS.md) now passes that complete
carrier workflow; it has not changed the installed selection.
[Nested SAVE at25/28/43/50 rows](SNAPSHOT_LEASE_ROWS.md) now has separate exact
full-frame evidence. WAIT transport faults, broader application commands,
ASPECT/emulations/protocols and Host parity remain separate gates.
