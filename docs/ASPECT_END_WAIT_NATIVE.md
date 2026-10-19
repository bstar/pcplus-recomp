# Native end-of-script receive wait

Resident4BFF..4C3C is the original61-byte dispatcher end-wait helper. The
dispatcher calls it for owner/context DI=0 when exit state is not999. Script
replacement/EXECUTE999 skips it. It neither closes the UART nor frees script
resources; global-string cleanup, bytecode FILE close and final invocation
cleanup occur later in the dispatcher.

`src/aspect/end_wait.asm` exports near `aspect_end_wait`, preserving the exact
native instructions. It requires DS=SS. BP/SI/DI depend on the usual callee
preservation; AX/BX/CX/DX/ES/FLAGS are volatile. External bindings are:

| Symbol | Original binding | Contract |
| --- | --- | --- |
| aspect_end_wait_delay |6B72| Calibrated delay, word argument, RET2. |
| aspect_end_wait_rx_count |8E20| Actual queued UART receive word. |
| aspect_end_wait_pattern_count |E2F8| Ordinary WHEN active count. |
| aspect_end_wait_display |E37E| Script DISPLAY word. |
| aspect_end_wait_receive |4C3C| Display-selected receive, delayed word argument, RET2. |
| aspect_end_wait_key_ready |651A| Key peek returns nonzero available; does not dequeue. |

It always waits50 calibrated units first. If receive count is then zero, it
returns without changing either pattern count or DISPLAY. Otherwise it sets
E2F8=0 and E37E=1, then calls4C3C(0). If input becomes empty after that call,
it waits15 calibrated units and rechecks receive count, allowing newly arrived
bytes to continue the drain. Empty input returns. Remaining input causes a key
peek; nonzero returns, zero repeats. A pending key therefore does not prevent
the first received lead from being processed. With only one queued byte and
no subsequent arrival, the key helper is never called. No key is consumed.

The loop leaves the changed DISPLAY and ordinary WHEN count in place. It does
not erase registration/action records, clear CWHEN's E2FA arm word, reset the
E382 gate or WAITFOR result, poll native service4DE9, check a deadline, or
explicitly inspect carrier/cancellation. A negative read result receives no
special end-wait handling; actual4C74 skips mapping/rendering it, and this outer
loop still follows the actual receive count.

## Existing exact dependencies

`src/aspect/receive_policy.asm` already exports actual4C3C as
`aspect_receive_policy_displayed`; bind the end-wait receive dependency to that
entry when the admitted platform supports it. Its19 bytes load E37E and call
actual4C74, exported by the same source as `aspect_receive_policy_read`.
4C74 selects raw reads here because the delayed argument is0, applies XLT to
nonnegative lead bytes, monitors ordinary WHEN only if E2F8 is nonzero, and
calls the renderer if its display argument is nonzero. End-wait clears E2F8
before this path, so ordinary patterns cannot fire through that callback.
The full native renderer may itself read raw continuation bytes and emit replies;
that application service remains distinct from a simple console byte callback.

`reconstruction/keyboard/core.asm` exports actual651A as `keyboard_peek` in
KEYBOARD_OMF builds. If the maintained keyboard queue is nonempty, it returns
its peek entry; otherwise it calls the BIOS peek service. It does not remove a
key. An Escape-consuming cancel poll is not an equivalent native dependency.
Calibrated6B72 is already recovered in
`reconstruction/modem_send/delay_calibrated.asm`; its units and calibration are
documented in [BREAK_NATIVE.md](BREAK_NATIVE.md).

## Maintained policy boundary

Continuous input without a key can keep the native loop running indefinitely.
Its calibrated busy wait does not provide foreground cancellation or bounded
hardware ownership. A renderer needing an incomplete ANSI continuation may
enter additional device calls. A nonlocal error during this helper can also
return to the dispatcher's probe and revisit the end-wait path while DI remains0;
the exact code contains no once-only drain guard.

A maintained owner may impose a bounded/cooperative delay, read budget,
cancellation, serial-open policy or once-only error guard. A raw ASIO mode may
preserve queued bytes for parent return. Such choices must be explicit maintained
policy; they do not describe this original helper. Linking the exact source alone
does not establish safe arbitrary-bytecode execution, physical UART timing,
renderer completeness or full original end-of-script behavior.

## Proof

The public fixture `standalone/fixtures/aspect_end_wait_native.json` pins the
61-byte owner at original file5DFFh to original executable SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Retained REA assembly evidence is
`ev_905383bd77df48ac8e3cb20cc751e7b4261fed54f625a46cd51ddf1eb53f2adf`.
The ordinary builder reads maintained source and public hashes only.

```sh
./tools/dev --command python3 standalone/build_aspect_end_wait_native.py
./tools/dev --command python3 standalone/check_aspect_end_wait_native.py
# Optional original comparison:
./tools/dev --command python3 standalone/check_aspect_end_wait_native.py \
  --original analysis/pcplus-install/PCPLUS.EXE
```

The221 CPU cases cover all21 owner instructions and compose the actual83 bytes
of4C3C/4C74. They exercise empty/nonempty entry, DISPLAY and WHEN state, key
availability after different read counts, arrival during50/15-unit waits,
negative raw reads, non-idempotent XLT and an aborted renderer callback.
Raw UART, delay-arrival timing, key peek and renderer emission are controlled
component callbacks. The proof does not substitute a fake full parser or claim
actual DOS execution. The optional original check compares all144 composed
bytes; owner and reused-helper totals remain separate in its report.
