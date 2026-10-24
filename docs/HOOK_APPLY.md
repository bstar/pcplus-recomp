# Interactive helper adoption

The optional `--hook-apply` executable now runs KEY kind2 helpers through the
normal PROGRAM safe point and applies supported returned settings and register
banks together. It uses the existing file/screen/mouse/UART handoff rather than
running a helper from the keyboard or parser callback. Other build variants
retain their previous behavior.

## Foreground route

A type2 definition in the selected `.KEY` file queues a direct helper filename
through `terminal_program_start`, using PROGRAM kind5. The51-byte KEY payload
remains bounded. The source-owned exchange constructs the native `PCPLUS`
argument and packed integer/string/PRM pointers with context3. The helper gets
private exchange storage, not live application addresses.

After the child returns, PROGRAM first quiets its UART and restores the original
vector. Only then are modem and input resources staged. An online helper returns
without a console acknowledgement pause; offline helpers retain the normal
return-key prompt. Application happens after the saved screen is restored and
before UART/mouse ownership resumes. Rejection shows the native-sized
`Helper failed` notice and preserves accepted settings/registers.

The phase sequence is validated return2 → modem offer3 → input offer4 → checked5
→ published6 → idle0. Execution/projection use phase1. Last/completed status words
retain execution100+, modem200+, input300+, application400+ or cleanup500 detail.
The DOS child result remains separate from application rejection.

## Checks and publication

`terminal_hook_apply_check(result6)` requires the actual foreground DS=SS,
IF=1/DF=0, PROGRAM kind5/status4, a live input binding and quiet application
owners. It reprojects the current session and compares it with the pre-helper
image, checks accepted register epoch/seal, revalidates the returned image/bank,
and verifies modem and input offers against current/staged resources. Keyboard
slots stay bounded; translation readiness/identity is checked without consumption.

Mouse settings are offered and checked while the driver is closed or suspended.
The new publication methods copy already-checked settings without driver IO.
UART checks verify BIOS-listed register addresses, saved/restored IRQ vector,
PIC mask, IER0, DLAB0, RTS-low, shift-register readiness and overrun state.
Transport edits additionally require empty receive/transmit queues and no pending
RBR byte. Old-format software pause release uses the existing bounded handoff.

`terminal_hook_apply` repeats these checks. Any requested COM move is the final
fallible operation, using the existing target-port ownership check/handoff with
kind5 admission. All accepted-state publication follows that successful move:
mouse preferences, translation/table identity, modem commands/responses, serial
format/flow, transfer/sound/display/BREAK settings, raw baseline and register bank.
No interrupt or port service occurs in this publication sequence. Register
epoch/seal advance together; the retained baseline uses kind3 and a new generation.

The existing profile finisher then installs/reset-captures the checked4/6 view
before input resumes. Driver resume can still fail and require the existing
typed shutdown/retention path; no physical driver or peer-timing guarantee follows
from logical accepted-state publication. A live baud/format change also requires
a peer that uses the requested format. Helpers are trusted DOS programs, not a
sandbox; arbitrary asynchronous memory/vector corruption remains outside this gate.

Application status0–8 means success, argument, owner state, stale state, returned
data, input resources, modem offer, mouse and UART failure. Failed checks do not
publish accepted state. Private offers, old-format pause handling and hardware
overrun accounting may change during preparation. Cleanup discards private offers;
uncertain exchange ownership stops the application instead of allowing another EXEC.

## Evidence

[The receipt](validation/hook-apply.json) binds40 linked application cases,
the existing39 input/3,394 modem/4,822 return/152 admission checks, twenty offline
and nine online8086 application workflows, nineteen input-resource workflows,
fifty helper staging attempts, fourteen ASPECT register recovery workflows,
two combined HOOK→ASPECT→HOOK workflows and seven products reproduced from712
source files without original inputs.

The application workflows use actual Alt-digit KEY actions and three source-built
helper invocations. Subsequent helpers independently capture the parent's accepted
registers, baseline, configuration, input tables and completed status. They also
read actual UART divisor/LCR, IER, RTS, PIC and vector state. Cases cover control
settings, profile/translation adoption, baud, software flow,7E2, translation mode2,
both COM directions, malformed returned data/strings, nonzero child exit, missing
resources and a real loopback-injected pending RBR byte. Offline exit restores both
UART snapshots; online exit checks the selected port.

Online cases use an owned synthetic modem and prove actual RX/parser/TX replies
to a fresh DSR query after all helper invocations, including rejection recovery
and baud/flow changes on COM1/2. These are not new live ENiGMA/Synchronet or physical
modem results. The combined script cases prove native per-script register reset,
opaque string-tail retention and epoch handback after a nonzero HOOK bank; the
script makes no integer assignments and does not close the compiler bank-selection gap.

The linked test seeds UART input values explicitly, rejects stale/corrupt state
and a changed prepared transaction, and forbids interrupts/port writes. It also
forbids all IO after the first publication entry. The DOS tests separately cover
acquired hardware ownership. Earlier rejected test runs exposed an oracle error
comparing an untouched raw baseline with normalized projection, an online fixture
with a different dial prefix, and stale companion manifests; those were corrected
without changing acceptance requirements.

DGROUP remains65,520 bytes. Compared with the preceding input-staging product,
resident code grows144 bytes to65,052, HOOK_CODE grows2,963, CONFIG_CODE114 and
MOUSE_CODE205 bytes. New retained status/epoch storage is eight far bytes.
The previous input-staging product, BBS-tested register product, ASPECT and
PRMEDIT all reproduce byte for byte.

```sh
./tools/dev --command python3 standalone/build_terminal.py \
  --external-render --mouse --notice-sound --notice-input --aspect-keys \
  --directory-keys --process-bank --session-capture --session-projection \
  --session-baseline --register-handoff --session-controls --hook-return \
  --hook-execute --hook-modem --hook-input --hook-apply
./tools/dev --command python3 standalone/check_hook_apply.py \
  --output build/hook-apply-linked-next
```

The result is `build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply/TERMINAL.EXE`.
It reads ordinary PRM/KEY resources; the build option adds no DOS command-line switch.
`standalone/test_hook_apply_dos.py` selects a mode/port and optional synthetic
`--online` case. Existing reproduction/component/register tools accept `--hook-apply`.

This closes the supported interactive helper transaction checkpoint. Remaining
native fields/metadata and helper lookup parity, combined exit/trap ownership,
full application gates, current live BBS acceptance and physical modem integration
remain open. The ENiGMA immediate-forwarding gap remains conditional as documented
in the separate BBS evidence.

The subsequent [live helper/BBS checkpoint](HOOK_BBS.md) adds current normal
product script/helper/editor evidence and retains immediate ENiGMA and nested
source-compiler memory failures explicitly. It does not broaden the scope of
the original synthetic receipt above.

The later [guarded helper composition](GUARDED_HELPER.md) combines the supported
interactive transaction with trap and final-exit owners. It supplies separately
bound DOS, source-compiler and BBS evidence; native parity and full application
gates remain open.
