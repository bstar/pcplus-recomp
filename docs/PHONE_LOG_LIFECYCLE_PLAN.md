# Call-log lifecycle integration

This is an implementation audit of public commit `898d702`, following the
[startup/claim checkpoint](PHONE_LOG_RESERVATION.md). It identifies integration
sites and acceptance requirements; it is not evidence that event hooks or disk
polling are implemented. The source excerpts and hashes are retained in the
[audit record](validation/phone-log-lifecycle-audit.json).

## Connection boundaries

| Path | Current owner | Required logger behavior |
| --- | --- | --- |
| Successful MODEM response | `connection.asm`, `.connected` | Capture one START after response classification succeeds and before the connected callback can schedule a script. |
| DIRECT start | `terminal_connection_start_impl`, DIRECT branch | Capture one logical session START without requiring DCD. |
| MODEM carrier loss | `.carrier_low` after a previously observed high DCD | Capture one END when this loss is observed. Initial low DCD alone must not create an END. |
| Successful hangup/abort completion | `.retire` | End an established session once; failed dialing must not produce a completed call. |
| Failed hangup with high DCD | `.finished` returns to state 6 | Keep the same call active. State/status 8 is not proof of disconnect. |
| DIRECT hangup | `terminal_connection_cancel_impl`, DIRECT branch | End the logical session; preserve the lack of carrier dependence. |
| Normal exit | `terminal_connection_exit_impl` and eventual retirement | Avoid a second END at final shutdown. |
| Exceptional exit | `terminal_shutdown` | Finalize any remaining logical session after restoring a known stack, without replacing a preexisting errorlevel. Mark this as application termination, not proof of remote carrier loss. |
| Redial | `transport.asm`, `.redial` | Admit a fresh generation only from idle, after retaining the preceding call's end event. |
| ASPECT/PROGRAM serial ownership | `program_actions.asm`, `script_launch.c`, `aspect_renderer.asm` | Preserve the generation across handoff. Reconcile observed carrier loss on return; do not treat child entry/return itself as disconnect/reconnect. |

Do not implement this by looking only for state 6 in the outer application
loop. `terminal_poll_io` can run the modem controller and dispatch a hangup key
in one call; a DIRECT session can therefore start and end between sampled loop
states. Producer hooks belong at the actual accepted transitions. Existing
`terminal_directory_note_connected` only performs directory work when option
bit 64 is set, so it cannot be the sole entry for direct/non-directory logging.

Connection state values are internal controller phases. State 9 is a hangup
attempt, not a completed disconnect; state 8 is the DTR wait. Only the accepted
retirement paths may close an active generation. The public hotkey redial gate
already requires idle state; retain that gate rather than allowing an active
session to be replaced.

## Events, clock and backpressure

Keep a nonzero 32-bit generation for the process lifetime. Increment only for
an admitted new connection, skip zero on wrap and leave the identity unchanged
on duplicate callbacks, failed dialing, rejected redial and script return.
Capture the name and target from the accepted live directory plan at START,
not when disk polling eventually runs. Non-directory calls need an explicit
bounded label and the actual configured target; do not invent a BBS identity.
A later directory adoption must not rename an already captured call.

The existing four-record queue can reject both START and END with `PLQ_FULL`.
The actual DOS saturation diagnostic explicitly demonstrates a START accepted
after one drain followed immediately by an END refused until another drain.
Consequently a void callback that ignores return codes would lose call data.
The producer must retain the original end timestamp across a deferred enqueue,
and must prevent another START from overtaking that retained event. Reserve
capacity for a call pair before admitting a new logged call, or retain a
bounded pending transition with an explicit admission gate. Do not solve this
by increasing the queue, silently dropping records or delaying the captured
end time until retry.

`phone_log_read_stamp` uses DOS date/time/date (INT 21h functions 2Ah/2Ch).
It is not an ISR-safe timestamp provider and must not be invoked while DOS is
already active. A clock failure or backwards time must remain visible and must
not silently fabricate a timestamp or consume the event. DOS clock changes
are not monotonic time. The existing queue's timestamp rejection policy must
remain distinguishable from a transport disconnect.

ASPECT execution is a distinct unresolved boundary: while a child owns the
UART, ordinary `terminal_poll_io` delegates to `terminal_render_poll`, which
performs a checked child callback rather than ordinary connection polling.
Do not report the child's exact physical disconnect time from a parent return
observation. Either add a checked event/clock handoff for child observations or
explicitly record the parent observation boundary. Adding a parent DOS clock
call inside the renderer RPC without establishing DOS reentrancy is unsafe.

## Foreground placement and memory

Keep transition hooks and the producer implementation in MODEM_CODE and
PHONE_LOG_CODE using explicit far bridges and the existing DS=SS convention.
The currently verified image has only 22 resident code bytes spare, while its
logger bank is 8,493 bytes and near data/stack has 976 bytes spare. Those are
measured headrooms, not permission to assume the next link fits. Extend the
memory/relocation inspector for every new entry, storage region and far call;
preserve both 63,000-byte histories, the 8KiB stack and compiler/VM limits.

Keep disk polling out of `terminal_poll_io` and connection callbacks. That
service is used by nested prompts and rendering paths as well as the main
loop. A logger disk operation that pumps the same service must not recursively
enter another append. Use an explicit foreground owner/reentry guard, service
UART traffic between bounded work, and reject unsafe contexts such as active
child UART ownership. A single DOS write can still stall despite an empty RX
ring, so test actual sustained traffic and flow-control behavior rather than
accepting a ring-empty precheck as proof of losslessness.

At shutdown, capture any outstanding logical end before releasing the session
identity. Drain only through the checked append backend; preserve retry and
ambiguous-close ownership and show a failure if data cannot be committed.
The existing capture/history/monitor cleanup order and preexisting errorlevel
must survive. No automatic blind retry is permitted after uncertain close.

## Required implementation tests

Before enabling live logging, extend the native full-terminal tests to cover:

1. Successful MODEM and DIRECT calls with exact START/END rows and one heading.
2. BUSY, NO CARRIER, timeout and cancellation before CONNECT: no completed call.
3. Repeated connected callbacks, redial and generation wrap: no duplicates.
4. High-DCD hangup timeout followed by recovery: one continuing session.
5. Observed DCD loss, delayed initial DCD and always-high-DCD profiles.
6. A DIRECT start/hangup in the same outer loop iteration.
7. Full queue and failed writes across a disconnect/redial: retained original
   timestamps, no overtaking, visible refusal/retry and later exact records.
8. Ambiguous close: no duplicate append, including exit and redial attempts.
9. Normal exit and exceptional shutdown while online; preserve earlier errors.
10. Script handoff/return while online, loss during child execution and a new
    directory selection afterward: one generation and original identity.
11. Nested capture/menu prompts during logging, with no recursive disk poll.
12. Sustained simultaneous serial traffic with hardware/software flow control,
    exact byte accounting, unchanged rendering and no RX overflow.
13. Logging disabled and feature disabled: existing behavior and byte controls.
14. Clean public-source rebuild and repeated tests, then full feature-combination,
    BBS, physical Boca/SPA2102, transfer and card deployment acceptance.

The next implementation must address event admission and retained timestamps
before adding the disk scheduler. Neither this audit nor the preceding 25-case
startup/claim proof closes live logging, F07/F10 or the full application plan.
