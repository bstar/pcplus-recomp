# Chat viewer display-change protection

The current opt-in Chat profile uses API0106. It now checks the saved display
contract while Redisplay has detached Chat's presentation: keyboard admission,
receive admission, idle service and viewer close all honor that contract.
Changing height, active text page or video mode holds the continuation and
retains its temporary arena. It does not copy the old screen into a mismatched
display or unload code that still owns the viewer.

When the original display returns, a remembered hold restores the saved live
Chat frame through the existing before-receive hook. The viewer then redraws
from its retained frozen view. Local input, remote pane and normal terminal
underlay survive. This is maintained protection around the existing viewer;
it does not establish full original D95C recovery or global Help.

## Reproduced defect and correction

The API0105 development candidate passed ordinary nesting, but its detached
presentation bypassed the normal cursor/geometry check. An actual DOS fixture
changed BIOS height from25 to50 while the viewer was visible. Key and RX hold
queries incorrectly admitted work, forced close released the arena and the
old25-row frame overwrote the changed display. The retained failing receipt is
`build/chat-view-geometry-negative2-20261106/result.json`.

The module now validates the suspended presentation without selecting a cursor
or painting. A held close keeps ownership. The parent honors the frontend's
hold result before its own viewer idle continuation, preventing a later paint
after Chat has already refused work. Recovery explicitly restores the live
frame before redraw; merely waiting for a matching BIOS mode would leave a
cleared screen with a stale viewer visibility cache.

The lease adds one held word in borrowed frozen storage; its12 bytes occupy
14600–14611. The parent CODE descriptor grows to54 bytes, including the
existing before-receive far entry. API0106 retains the50-byte request,
480-byte session,28-byte live binding and12KiB code window. The module image is
11396 bytes, with four relocations and no DGROUP, own stack or CRT. The parent
is479392 bytes,16 below the earlier479408-byte Chat parent. DS=SS65504,
resident CS65386 and all stack/stream/history/frame/FIFO capacities remain.

## Verification

[The checked receipt](validation/chat-view-geometry.json) binds the exact
parent/module to these checks:

- Twelve real DOS recovery cases:25/28/43/50 rows, each with an external BIOS
  height change, page change and graphics-mode change. Initial canonical layout
  is supplied by the caller; actual BIOS services establish and perturb the
  display. No product instruction, ownership flag or ready flag is patched.
  Tests require held key/RX/close operations, retained arena and local input,
  unchanged video, automatic redraw, both Chat panes on return, normal underlay
  restoration and complete memory cleanup.
- Four separate normal-main cases import saved display preferences for each
  height. Passive observation verifies actual BIOS rows, an initially empty
  remote pane, later hidden-frame CP437 RX while browsing, preserved local AB,
  resumed visible panes, one line transmission and ordinary parser return.
- 26 nested-ASPECT checks, all ten TEXT bindings, nine native-echo CPU groups,
  four40-key pressure/cancellation cases and XOFF/queued cancellation checks.
- 25 Synchronet and16 Enigma regression checks, with an independent exact
  65539-byte retry audit and unchanged ASPECT interpreter. Chat stays inactive
  during those BBS regression cases.
- A5257-file public-source export rebuilds identical parent/module bytes without
  originals, analysis artifacts, prior objects or ancestor Git. It repeats the
  75085-assertion DOS lease test, normal-main50-row case and50-row graphics
  quarantine/recovery case.
- The disabled API0104 control is byte-identical to the preceding control,
  including its unchanged module. Its real DOS saved-buffer pointer/lifetime
  check passes again.

The first graphics fixture incorrectly compared the disabled B800 text
aperture after switching to graphics. Its failures are retained in
`build/chat-view-geometry-matrix-20261106/result.json`. The corrected fixture
checks all64000 visible graphics bytes at A000, with successful readback before
applying the held continuations. No product change was needed for that fixture
correction. All16 cases in the final matrix pass.

## Exact build and reproduction

Parent: `0ba3c1f6f9af368a5d62d4dd43b9d4ff3f19b561e5d0de946faaa65a78121a0e`.
Module: `6845e2c8e3faa4de505736e9fe6da715d5984da66c06b2617846646c08c16448`.
ASPECT remains `cbdee1949f0ac6bba34f56ae9c594a17888ef9b5143ee5dca9cd76498737ccfd`.
The descriptor/lease change is versioned; keep the matched parent and module
together. The existing public profile builds the current code:

```sh
./tools/dev --command python standalone/build_chat_redisplay_profile.py --output build/chat-view-current
./tools/dev --command python standalone/test_chat_view_geometry_matrix.py --terminal build/chat-view-current/TERMINAL.EXE --output build/chat-view-current-matrix
```

## Scope still open

These BIOS perturbations occur at a viewer-visible foreground boundary.
Asynchronous changes during a frame copy or a pending-RX screen update are not
proved. DOS free-error injection, export cancellation during carrier loss,
logging/printer faults, sustained saturation and physical flow/carrier tests
remain open. A held display intentionally waits for its original mode/page/
height; it does not guess a replacement layout.

No physical Boca/SPA2102/SynthModem audio test or card deployment occurred.
Private PRM/DIR/KEY/KBD/XLT/FON, selected physical package and production
network/bridge configuration remain unchanged. Global Help/Alt-Z and the
remaining ASPECT/emulation/protocol/Host inventory stay in the active objective.
