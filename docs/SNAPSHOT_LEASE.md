# Retained snapshot lease for nested PROGRAM

The opt-in capability17 pair completes the ordinary8086 nested SAVE workflow
that failed under heap pressure. Parent `bad604fb` and ASPECT `7aa7066f` borrow
an existing retained parent frame for the child's saved screen. No additional
screen buffer is allocated. The installed capability16 package remains selected.

The [receipt](validation/snapshot-lease.json) binds the matched products, actual
DOS runs, linked ownership checks, version refusals and clean source exports.
This is a staged application checkpoint, not full PROGRAM or hardware acceptance.

## Storage and service contract

`redisplay_live` occupies8000 retained bytes and aliases the directory editor's
4000-byte `ed_screen` role. The outer PROGRAM/browser frame occupies a distinct
8000-byte block; it remains owned and unchanged throughout the ASPECT invocation.
The cooperative script window uses the separate `redisplay_view` frame.

Capability17 adds three scalar requests to the authenticated existing bridge:

| Operation | Input | Result |
| --- | --- | --- |
|17 acquire |1..8000 bytes | Typed status; requires the attached child's SAVE PROGRAM lease |
|18 pointer byte | Index0..3 | One byte of the retained offset/segment, only while owned |
|19 retire | Zero | Typed status; failed retirement retains ownership |

Existing child PSP, DS=SS, service token/version and checked bridge-stack
admission remain in force. Acquisition rejects active viewer, staged live view,
command menu, editor, chooser, script window or confirmation owners. It reads the
actual parent MCB, checks M/Z type and PSP ownership, and bounds the entire
paragraph-aligned8000-byte frame inside the retained allocation. No client
pointer is supplied for parent dereferencing.

The child's display allocator borrows only while attached. Raw/unattached use
keeps the original heap path. A borrowed pointer is never passed to `_ffree`;
normal restore/discard retires its parent lease. Failed release retains the
child's owner and prevents PROGRAM END, rather than advertising reusable storage.
Invalid byte replies, null segments and wrapping extents are rejected, with
retirement attempted before reporting allocation failure. Parent revoke
invalidates a returned child's service before the frame can be reused.

Ordinary chooser/editor/viewer entry guards also reject the active outer PROGRAM
owner, providing the opposite direction of exclusion. The lease stores only a
small ownership word in ASPECT_CODE; it adds no screen array or parent DGROUP
storage. The parent retains478032 bytes; near data/stack65488 and resident
code65516 remain unchanged.

## Current evidence

- Two actual8086 graphics children leave mode13h active; SAVE restores enough
  state to complete both scripts, six simultaneous file streams, missing-file
  recovery and subsequent keyboard/hangup. A separate NOCLEAR workflow passes.
  All1920 cells of the **final parent viewport** match the expected text and
  attributes. This final capture does not substitute for an inner pre/post-child
  screen/cursor capture, since the outer PROGRAM also restores its own frame.
- Seven register/recovery cases pass43 paired full830-byte snapshots: normal,
  bad token, missing script/helper, divide, execution budget and user abort.
  These do not inject a fault while the borrowed snapshot is active.
- Forty-two linked cases test size bounds, MCB bounds/owner/type, caller identity,
  competing roles, pointer replies, failed-retirement quarantine/retry and actual
  chooser/editor/viewer entry refusals. Caller identity, view admission, window
  close and the child endpoint are modeled boundaries in those tests.
- A386/XMS/UMB witness observes four successful script exits and no DOS48h block
  allocation requests during the matched SAVE workflow. This is separate from
  the passing unobserved8086 case; it does not claim no other memory operations.
- Both mismatched16/17 combinations produce none of the script output files,
  while hardware/settings/input files, the final viewport and subsequent keyboard
  and hangup checks pass. Capability16 defaults remain supported as exact
  feature-disabled controls, not silently admitted to the new service.
- Clean exports reproduce2030 parent-source inputs and1700 child-source inputs,
  including both enabled products and disabled867cb827/23caac93 controls. No
  originals, prior objects, private configuration or ancestor Git are available
  in either export.

The ordinary parent builder selects this with `--aspect-snapshot-lease`, requiring
external rendering, notice input and large view frames. The child builder's
explicit `snapshot_lease=True` selects the matched service. Both defaults remain
off. Repeat the ownership test with fresh output storage:

```sh
./tools/dev --command python standalone/check_snapshot_lease.py \
  --terminal build/terminal-snapshot-lease-v2-20261106/TERMINAL.EXE \
  --runner build/aspect-snapshot-lease-v2-20261106/ASPECT.EXE \
  --output build/snapshot-lease-owner-new
```

Use `test_aspect_heap_startup_dos.py` with the same pair, `--nested-program
--nested-graphics` and a new `--output` for the ordinary8086 SAVE case. Omit
`--nested-graphics` for NOCLEAR. The source-export tools accept
`prove_viewer_terminal.py --feature aspect-snapshot-lease` and
`prove_program_result_probe.py --snapshot-lease` for the respective paired builds.

## Remaining release gates

Direct inner screen/cursor/geometry capture, faults/cancellation during an active
borrowed lease, actual larger-row use, Enigma/Synchronet rendering/input and
transfer/cancellation/carrier-loss regressions remain open for this exact pair.
Only after those gates should it replace the selected package through a verified
configuration-preserving deployment. Physical modem acceptance, broader original
language/emulation/protocol coverage, Chat and Host remain separate requirements.
