# Recording bytes accepted by the UART

The [TX checkpoint](validation/recording-tx.json) connects successfully emitted
user bytes to the stable recorder owner. Queued bytes carry an origin bit, so
terminal replies are excluded even when interleaved with user output. This is
a TX component checkpoint: Record controls, received-prompt taps and complete
owner exclusions remain required. All F01–F16 application gates remain open.

Each of the1024 TX ring slots has one bit in128 bytes of initialized loaded
CONFIG_CODE storage. Every enqueue overwrites its bit. Ordinary keys, expanded
keyboard bindings and clipboard packets use the user enqueue entry; reports
and dedicated monitor/controller/transfer producers retain the ordinary entry.
Successful UART acceptance clears the head bit and feeds only tagged user bytes
to the recorder. Busy UART or CTS leaves both the queue and origin unchanged.
Dropped slots cannot leak provenance after wrap/reset because reuse always
sets or clears their bit. The ring capacity remains1024; near data is unchanged.

Both ordinary transport and the transfer owner's queue-drain loop call the same
banked delivery helper after `uart_try_write` succeeds. TEXT bindings write
directly to the UART and call a separate banked entry after success. All three
far entries preserve registers, flags and stack, including across the recorder
callback. The source owner asserts its state-field offset at compilation; the
helper checks initialized/active state before calling it. No byte is recorded
merely because it was admitted to a queue. Once a byte has reached the UART,
a recorder file error cannot undo or suppress that successful transmission.

| Evidence | Scope |
| --- | --- |
| Ten linked TX campaigns |All256 user octets interleaved with report bytes; THRE/CTS stalls;1024-slot wrap with dirty tags; reset/reuse; paste-prefix cancellation retaining later reports; expanded FF-to-NUL output; TEXT pause suppression; actual transfer-drain/protocol instructions; recorder write-error continuity;21 far-entry register/flag/stack vectors at bit boundaries. |
| Six linked owner cases |Stable initialization, exact source, shutdown cancellation, independent/conflicting capture and modeled file errors against the current binary. |
| Six transport cases |Existing UART/IRQ/keyboard/queue behavior. |
|837 key-output vectors |All79 binding slots and supported profiles/duplex paths; declared echo/cursor endpoint fixtures remain explicit. |
|343 TEXT inputs /46 clipboard inputs |Existing pacing, cancellation, queue ownership and pointer/size behavior. |
|78 linked ZMODEM workflows |Current engine, file ownership and protocol behavior with modeled hardware/kernel boundaries. |
|574 ABI corruption checks |Adds initialized tag storage, three helper segments, four resident far bindings and the exact one-word recorder callback/relocation to prior checks. |
|11 actual DOS capture scenarios |Current terminal with recorder idle: startup/shutdown, existing capture UI/UART/files and XMODEM coexistence. This does not establish actual DOS recording from the UI. |

The ten TX campaigns execute actual linked product instructions. Hardware,
BIOS and DOS kernel boundaries are modeled; no product callback is skipped or
patched. The transfer case initially froze the BIOS clock, so its timed finish
notice could not complete. The corrected fixture advances the clock. That
initial failure receipt is retained beside the accepted evidence.

The current keyboard binary is
`b74a70d667e2906d9f77aed1785df4e6c3a8d0d3776ad2edc5f486f8e5134f14`;
it leaves112 near-data bytes and440 resident-code bytes. The mouse build is
`1c3edaadb788681b36c0b645c8a9b6e49abb0a8e457df4171a6f7e7393a741b0`;
it leaves64 near-data bytes and290 resident-code bytes. Both pass the static
bank, state and relocation audit; runtime mouse acceptance remains separate.

Next expose Record/save/cancel/recovery choices and connect received prompts,
including parser continuation paths. Apply transfer/autostart, script, PROGRAM,
setup, port-change, monitor/controller and error/exit exclusions. The component
transfer test deliberately invokes lower-level owners to prove queue draining;
it does not accept the final UI transition policy. Then test actual foreground
DOS recording, compiler/UART replay and affected BBS/audio workflows with those
resulting binaries. Physical modem compatibility remains unverified.
