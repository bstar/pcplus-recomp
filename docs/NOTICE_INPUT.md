# Native notice input and executing-child mouse ownership

The [receipt](validation/notice-input.json) accepts a separate notice-input
component with66 actual8086 DOS checks. It combines the recovered mouse/keyboard
producer and consumer with the banked timed-notice controller. Attached ASPECT
input remains open.

## Original input boundary

Fresh REA/Ghidra analysis of original2.01 SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`
confirms the recovered notice's direct input boundaries:

| CS entry | Observed role | REA evidence |
| --- | --- | --- |
| 6530 | Peek mouse/BIOS; gated Alt-Z display callback | `ev_4e1b6a73df0456f0f688846077e41b2a714d0e90ba683c1edd24aeebb38db882` |
| 64fe | Poll, read mouse first, otherwise normalized BIOS | `ev_8e40cf9d5f190f977da1b135d35970d1fcab5cac3261658c9dabbd80eb7dfbd6` |
| 651a | Non-consuming mouse peek, otherwise BIOS peek | `ev_9bc44de1285653267fe1e2c64a2f8d8f3fffa0fb3fcccfe61137d4b9fbc4fcd5` |
| 57ae | Gather contextual values, format and display diagnostic/script dialog | `ev_7a8b8dcc588f1a3338056f8bac107d3c67712bdc0f3aab2c18ec53dd024e19f6` |

The original was statically analyzed and closed. Complete records remain in
ignored `analysis/notice-input-01.rea.json` and frozen custody. No original or
REA record enters the build. This covers the direct path, not every indirect UI
dependency. Calling it “macro keyboard” was too broad: native KEY macro dispatch
uses a separate47b6/TEXT48cc path, described in
[keyboard mapping](KEYBOARD_MAPPING.md). The terminal macro sender rejects an
active PROGRAM owner. Enabling it inside notices would introduce a different
ownership policy; complete KEY macro support remains separate application work.

## Binding and ownership

`MOUSE_NOTICE_INPUT` exposes guarded `mouse_owner_peek`. It applies the read
owner's DS=SS, IF, pointer, phase, callback-depth, scale, event-index, vector,
size and guard checks. Empty input leaves output unchanged. Peek consumes no
mouse repetition or BIOS typeahead. Mouse Enter/Escape peek words1c0d/011b differ
from read words000d/001b; a cached consuming read would lose that behavior.

The optional `NOTICE_NATIVE_INPUT` runtime uses explicit far peek/read bridges.
Input errors retain their mouse status in `notice_result.service_status` and
leave through typed notice cleanup. The foreground service callback still runs
before peek. Builds without the option retain their BIOS-only binding.

The input facade owns an executing-child mouse owner. Open rejects an existing
owner and publishes its claim before driver mutation. Failed open without storage
releases the claim. Close rejects a foreign owner and a live notice. After notice
retirement/unwind it restores its own snapshot. Quarantine retains the claim and
storage until repair; callers must not terminate while ownership remains.
Unrelated direct mutation of the underlying owner is outside this facade's
cooperative ownership contract.

## Verification and remaining work

```sh
./tools/build test-notice-input
./tools/build test-notice-input-source
```

`NINPUT.EXE` uses real DOS heap, VGA windows, BIOS and INT33 state. Injected events
invoke the recovered callback on foreign DS and separate SS. Checks cover repeated
peek without consumption, two mouse Up events before queued BIOS a/b, distinct
mouse Enter/Escape, BIOS Escape preserving the next key, idle timeout, outer C
longjmp, foreign-owner rejection, invalid open and vector quarantine/repair.
The full576-byte driver state and28-byte native state match after cleanup.
Injected events do not establish physical mouse movement.

A fresh86-source tree reproduces NINPUT and both quiet notice diagnostics.
The quiet regression retains583 checks with69 allocations/frees. A separate
632-source tree reproduces all four matching mouse/sound application products
at their preceding hashes; the component changes no published behavior.

Next, move the child-local native input/owner into explicit ASPECT banks, share
the interpreter's BIOS mode through a declared ABI, and pass the parent's current
scales while its callback stays suspended. Bind open/close, quarantine and retry
to PROGRAM notices and every outer fault/child-exit path, then test queued serial
bytes and ordinary products. This component tests BIOS mode0 with the Alt-Z gate
disabled. Original contextual/shared UI, enhanced BIOS composition, attached input,
broader views, physical modem/mouse/audio and all full application gates remain
open. This receipt does not enable KEY macro playback in notices.
