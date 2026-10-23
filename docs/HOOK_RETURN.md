# Returned PRM validation

[Modem preparation](HOOK_MODEM.md) corrects an error in this initial checkpoint:
already-expanded response slots are literal data and must not undergo command
expansion again. Current validation accepts literal caret bytes and tests them
through the actual matcher. The receipt below records the earlier policy.

The optional `--hook-return` terminal links a staged validator for external
helper settings. It validates and classifies a proposed return without changing
active settings. KEY kind2 execution and foreground application remain open.
This is an authored transaction boundary over recovered fields, rather than a
claim that the original helper path used this validation policy.

## Contract

`hook_return_validate` is a far cdecl entry in HOOK_CODE. Its five arguments are
near pointers to the before/after 1,264-byte PRM images, an explicit modem-active
word, and near pointers to the candidate and result. The four objects must be
disjoint, non-null and nonwrapping. Admission requires DS=SS, IF=1 and DF=0.
The function performs no port, interrupt, file or active-state operations.

The caller establishes successful child exit, exchange ownership and stable
inputs. It retains the validated raw after-image until commit or discard;
the decoded candidate alone does not retain every raw representation. The
change mask does not authorize UART switching, resource loading or adoption.

The candidate is 490 bytes:

| Offset | Bytes | Value |
| --- | --- | --- |
| 0 | 6 | modem-active, semantic change mask, raw-changed flag |
| 6 | 44 | decoded serial/display settings |
| 50 | 368 | decoded modem settings |
| 418 | 66 | decoded transfer settings |
| 484 | 6 | normalized sound, selected mouse X/Y scales |

The eight-byte result has status, decoder status, input index and byte offset.
Statuses 0–7 mean success, argument, serial, modem, transfer, controls,
unsupported byte mutation and modem expansion failure. Input index 0 identifies
the before-image, 1 the after-image and 2 comparison/success. Unsupported
mutation reports its first byte offset; other offsets are FFFF. Invalid pointer
geometry or CPU context returns before writing the result. The candidate stays
unchanged on every failure.

Both images must decode. Mouse scales must be 1–999; any nonzero sound word
means enabled. Active modem commands must pass bounded native expansion;
already-expanded responses must be NUL-bounded and remain literal. With an
inactive modem, unchanged private
bytes can be invalid; the candidate clears private settings and explicitly
marks them inactive, while keeping shared pause/delay and BREAK values.

## Permitted byte changes

All offsets below are hexadecimal and inclusive. Only these fields may change:

- Serial words 000–009; the after-selected COM base/IRQ pair at 174+port*2
  and 184+port*2 (each two bytes, port 0–3).
- Profile 194–195; flow/wrap/scroll 198–19F; BREAK 1A4–1A5;
  attributes 1AE–1B7; sound 1BC–1BD.
- Translation/pause 1E0–1E2; character delay 1E4–1E5;
  download path 31C–35B; autodownload 42C–42D;
  mouse scales 4E4–4E7; clipboard separator 4EA–4EB.
- Only with an active modem: 00A–012 and 014–173.

Unknown bytes, byte 013, byte 1E3, inactive modem fields and unselected COM
slots stay opaque and immutable. Known string tails may change without a
semantic change; nonzero-to-nonzero sound edits have the same distinction.
The raw flag records these edits. Semantic categories use existing LIVE_CHANGE
bits plus sound bit 8000. Shared pause/delay changes can affect both mapping
and modem categories.

## Native evidence and limitations

Static REA inspection of the derived overlay16 image SHA256
`e14871502dba5f55646eb6184cf488c216381e6eda2ca47227a06934592b8302`
from PCPlus2.01 SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`
observes direct pointers to DS:D126, DS:D13A and DS:1B84 in wrapper 414C
(Evidence `ev_77bb3db37f77e0ccb69c51194f322155b0d8c63f19d5136c8abaa028bcecbbea`).
Program service 433D calls refresh 03A7 after EXEC and later uses PRM mouse
scales (Evidence `ev_af170f2ad0284898bbd5d70c47ad25cdd0f58e849189d4dc3028c18c3523b68e`).
Refresh reads PRM port/serial state (Evidence
`ev_0c9da399b3a93bb84a596cb3a016114b90f9f78f3bd71d0d9a0efddc13f7e6d7`).
These bounded procedures establish writable pointer and refresh behavior;
they do not establish a complete audit of native validation. The synthetic
analysis image was never executed. The raw REA bundle remains ignored under
`analysis/hook-return-16.rea.json`.

## Verification and reproduction

[The receipt](validation/hook-return.json) binds 1,995 linked cases, five actual
8086 DOS projection/validation workflows, fourteen register recovery workflows
and six products reproduced from 693 source files without original inputs.
Linked execution prohibits interrupts and port IO. DOS tests reject an opaque
mutation with an untouched candidate, accept supported changes, and reproject
the unchanged active session. Startup files, retained baseline and hardware
snapshots remain unchanged. These are diagnostic proposals, not helper EXEC.

The optional build adds 1,749 HOOK_CODE bytes and 22 resident code bytes;
DGROUP remains 65,520 bytes. The older controls product reproduces exactly.
There is no new live BBS or physical hardware acceptance for this variant.

```sh
./tools/dev --command python3 standalone/build_terminal.py \
  --external-render --mouse --notice-sound --notice-input --aspect-keys \
  --directory-keys --process-bank --session-capture --session-projection \
  --session-baseline --register-handoff --session-controls --hook-return
./tools/dev --command python3 standalone/check_hook_return.py \
  --output build/hook-return-linked-next
```

Add `--projection-probe` for the diagnostic product, then run
`standalone/test_session_projection_dos.py --session-baseline --session-controls
--hook-return --output build/hook-return-DOS-next` through the same Nix wrapper.
Source proof and register tests also accept `--hook-return --session-controls`.

Next is an owned foreground transaction: route helper EXEC, stage resources,
validate the return, then atomically adopt registers/settings or preserve the
accepted session on any failure. UART, display, mouse, file and interrupt
owners must participate. Unsupported native field recovery, full application
gates, ENiGMA immediate-forwarding and physical modem tests remain open.
