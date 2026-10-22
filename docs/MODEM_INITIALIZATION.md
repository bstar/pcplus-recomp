# Modem initialization result policy

[Four independently audited actual DOS cases](validation/modem-initialization-baseline.json)
reproduce an open initialization policy on parent3b453f2b. The maintained
controller completes transmission of the configured initialization string and
immediately starts the dial sender. Initialization-state RX is consumed without
an initialization result parser. No application change is accepted here.

| Owned peer policy | Actual DOS outcome | Interpretation |
| --- | --- | --- |
| Immediate OK | Connects and answers ANSI queries | Existing control passes. |
| Quiet-ready, no initialization reply | Connects and answers ANSI queries | Valid compatibility case; silence alone is not a defect. |
| Explicit initialization ERROR | Still sends ATD; peer rejects it with NO CARRIER | Initialization failure is not acted upon. |
| Ready after750ms | Starts ATD before OK; peer rejects a command started while unready | The sender finishes bytes without waiting for modem readiness. |

The delayed peer declares a750ms readiness interval for a deterministic test.
It does not measure a Boca modem, Wi-Fi modem, firmware reset duration or
physical connection. In that case the first dial byte precedes OK even though
the complete ATD line arrives later. The independent auditor checks this first
byte's time from the raw receive transcript, rather than treating the command
completion time as the beginning of the dial. Response timestamps identify
host-peer writes, not the time each byte was consumed by the guest UART. The
source inspection establishes initialization-state handling; the captured wire
establishes the command/readiness ordering under this declared transport.

Every case retains exact configured ATZ/dial bytes, actual UART/IRQ/controller
execution, peer responses, expected abort or configured hangup, ordinary DOS
exit and42-byte UART/PIC/vector restoration. Only the two control cases connect;
no credentials or external BBS are involved. `passed=true` means the declared
gap/control outcomes are reproduced. `initialization_policy_accepted=false`
remains explicit.

~~~sh
./tools/dev --command python3 standalone/test_modem_initialization_dos.py \
  --output build/modem-initialization/dos-new
./tools/dev --command python3 standalone/audit_modem_initialization_dos.py \
  build/modem-initialization/dos-new \
  --output docs/validation/modem-initialization-new.json
~~~

## Required correction

Add configurable result waiting while retaining the legacy no-wait mode for
quiet profiles. Do not silently reinterpret an unknown PRM field or assume a
newer modem command set. The configured initialization bytes remain owned by
the existing PRM command fields. A maintained invocation setting is appropriate
for machine profiles; its exact CLI and help are not implemented yet.

The implementation must cover these behaviors together:

- Validate the setting and stage it atomically before UART acquisition. Reject
  malformed/range/duplicate settings without partly changing existing options.
  The current16-bit option mask is fully allocated; a new setting must not
  alias an existing flag. Normal/mouse memory headroom must remain checked.
- Keep quiet/no-wait behavior available. In result-wait mode, handle complete
  verbose OK/ERROR and numeric0/4 lines, fragmented CR/LF and command echo;
  unrelated substrings must not produce successful initialization.
- Sequence multiple configured initialization commands and wait for their
  results before dialing. Preserve command expansion, pause-marker behavior
  and existing configurable commands. Empty and incomplete command policies
  need explicit validation and tests, rather than an accidental infinite wait.
- Accept an early reply delivered after the command terminator but before the
  sender's final pacing poll. Do not erase it when entering the response wait.
- Distinguish stale cleanup responses after retry synchronization from results
  of the new initialization. Retained/cleared command parsers, an absent blank-CR
  response and late/fragmented stale responses need separate controls.
- Bound transmission/result waits under CTS, XOFF and THRE stalls. Preserve
  Escape/Alt-X cancellation, DTR policy, hardware restoration and subsequent
  retries. Initialization failure or timeout must prevent ATD in wait mode.
- Preserve direct lines, initial-high/always-high DCD configuration and the
  failed-online-hangup redial guard. Keep the existing configurable11-slot
  connection-result/autobaud matcher separate from initialization results.

Before adoption, compare the corrected DOS results against this baseline and
run normal/mouse linked cases, source-only rebuilds, connection/carrier/startup,
attached PROGRAM and current BBS/audio regressions. The default legacy mode
must continue passing its quiet-profile control. Physical Boca and SPA2102
validation remains separate, including actual modem identification and supported
initialization commands. No full F03 or application gate closes.
