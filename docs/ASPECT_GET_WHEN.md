# WHEN actions during a full-interpreter GET

Two additional compiled-source cases now compose the recovered WHEN machinery
with a live GET field in the complete capability22 parent and experimental
interpreter. The cases cover an immediate TRANSMIT action and a deferred CALL,
using both plain and locally framed handlers. This is additional runtime evidence
for the existing binaries; it does not change the selected or installed package.

Each script waits for LOGIN, registers slot0 PING→TRANSMIT INLINE and slot1
PONG→CALL worker, transmits GETREADY, then enters string GET. The owned peer
sends PINGPONG after that marker. The worker increments a global integer,
transmits WORKER and returns. The framed variant also allocates, assigns and
reads a local integer37. Main verifies exactly one worker execution before
transmitting the edited LoC42 value and the explicit directory password.

The passive timer observer first requires a live, configured GET field with its
native cookie and the native receive gate at0. It records that waiting state.
Only after observing the same field active with a pending native CALL gate of1
and an empty BIOS queue does it inject the field's answer. Thus the field exists
before the CALL is staged; its completion cannot precede the pending action.
The observer neither calls the worker nor mutates interpreter/receive state.
The peer's quarter-second delay helps arrange the scenario but is not its proof.

Both cases produce the exact ordered suffix
`GETREADYINLINEWORKERLoC42`, CR, `Synth42`, CR, followed by cursor report row1,
column27 and normal terminal input/hangup. INLINE and WORKER each occur once.
The CALL body executes on the normal dispatcher after GET completes, preserving
the recovered deferred-action model rather than recursively interpreting a
handler inside the receive callback. Both GET-waiting and pending-gate samples
are1. Exit/error/file status are0; file-table/sink/history/keyboard restoration
checks pass. The actual source-built native matcher, action, FILE seek,
flow/frame and dispatcher code run; this is not a stubbed action callback.

The DOS8086 compiler produces both complete ASX programs, byte-identical to the
host compiler. The full parent test uses DOS386/UMB and640KB conventional memory,
with an owned synthetic serial modem peer. Parent `b25fe6d2…`, interpreter
`54590fd3…`, optional compiler `db9de7ca…` and the default binaries are unchanged.

```sh
./tools/dev --command python standalone/test_aspect_get_vm_dos.py \
  --parent-dir build/PARENT --child-dir build/GET_CHILD \
  --get-compiler-dir build/GET_COMPILER --when-cases \
  --allocation-probe --output build/FRESH_WHEN
./tools/dev --command python standalone/prove_get_vm_source.py \
  --parent build/PARENT --parent-profile keymap --child build/GET_CHILD \
  --compiler build/DEFAULT_COMPILER/ASPCOMP.EXE \
  --checks build/FRESH_WHEN/checks.json --output build/FRESH_SOURCE
```

The isolated proof repeats both WHEN cases with exact wire, waiting/gate,
observer and allocation observations. It additionally repeats the two
[GET/EXECUTE lifetime cases](ASPECT_GET_LIFETIME.md), six ordinary GET cases,
compiler grammar/executor/serial regressions and CLI/file/MZ checks. Sources and
reports are bound by the [receipt](validation/aspect-get-when.json).

This covers one ordered event pair and one CALL per field. Multiple/rearmed or
nested CALLs, action errors, EXECUTE from a WHEN handler, cancellation/carrier
loss during event handling, full memory/feature pressure and other field types
need separate tests. No physical Boca/SPA2102/SynthModem/BBS or three-process
compiler-residency acceptance follows from this matrix. Floating GET, broader
ASPECT/app parity and package promotion remain open. An initial fixture failed
before parent execution because nested bytes were not JSON-serializable;
using textual peer specifications corrected the harness, not the application.
