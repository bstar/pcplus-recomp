# Mid-frame carrier loss and command resynchronization

The modem controller now requests its existing retry separator when a previously
observed carrier falls. This resolves an independent mid-frame reconnect defect:
bytes already accepted from an upload could enter the modem's command buffer
after carrier loss and prefix the next initialization. Skipping cancellation
bytes after fault 4 was necessary but did not resolve those in-flight bytes.

## Failing old-image control

The fixture starts a real manual YMODEM or ZMODEM upload, validates exactly the
first 16 bytes of its metadata frame, then immediately aborts its owned TCP peer.
It does not wait for a complete frame, provoke retries, supply modem result
strings or write product variables. DOSBox-X owns the modem's command parser,
CONNECT/NO CARRIER messages and actual virtual DCD.

All four old-image cases fail: YMODEM and ZMODEM, each with legacy initialization
and acknowledged `/I:1`. Legacy cases can dial again despite the corrupted
initialization; strict cases fail the second initialization and never establish
the second TCP connection. That distinction prevents an apparently successful
redial from hiding failed modem setup. The old binary remains intact at
`build/transfer-carrier-fixed-source-01/build/terminal-phone-log-bank-d882144fee4f/TERMINAL.EXE`
(SHA256 `512f782e9befeef39db1f8dfe03b6b786e89d44910cc99bb0ea4f7d83bbb3eba`).

## Reuse the existing initialization policies

After a genuine high-to-low carrier transition the maintained controller sets
`connection_resync`. The next MODEM initialization already consumes this flag:
legacy mode emits the retry CR with its existing pacing, while acknowledged
mode emits it and drains responses for the configured guard before starting the
new command. A separator ERROR/OK belongs to that drain; it must not be mistaken
for the new initialization's result. Cold startup, direct links, configured
initialization bytes and the optional acknowledgement policy remain distinct.
No new modem dialect or assumed Boca command is introduced.

Only `src/terminal/connection.asm` changes among application build inputs. The
change lives in MODEM_CODE and does not consume additional resident CS: 65,534
bytes remain allocated with two spare. Data/stack remains 64,752 bytes with 784
spare. The fixed image is
`a6f8a847b6b0161693efeb5bee80d9c7d33685e85d8886ec7eb0553254a33f25`.

## Accepted validation

The four fixed native cases require the deliberate 16-byte cut, confirmed
carrier fault 4, closed/unambiguous upload ownership, unchanged source bytes,
and normal DOS exit with the 42-byte hardware snapshot restored. The original
DOS parent initializes cleanly and reconnects, answers new cursor/capability
queries, accepts keyboard text and saves exactly two call pairs. Original START
stamps, the old log prefix and directory accounting are checked. The actual
modem log must show OK for both clean initialization commands; a separator
response is permitted before the second command.

The linked initialization-policy suite passes 40 cases. Three additions observe
ordinary DCD loss and reinitialization with wait settings 0, 1 and 3, including
strict draining of an ERROR before the new initialization. Existing CLI ranges,
atomicity, echo/result parsing, malformed commands, cancellation, timeouts,
CTS/THRE/XOFF stalls, direct links and default policy remain covered. The linked
suite models BIOS/UART boundaries and does not replace actual DOS modem evidence.
The broader linked connection controller also passes eight groups/46 inputs,
covering hangup/cancel, result/autobaud handling, UART backpressure, full-width
deadlines and notice restoration on this exact image.

The [receipt](validation/midframe-modem-recovery.json) binds the four old failures,
four fixed native cases, the 40-case initialization suite, 46 linked connection
inputs, a clean committed-source
67-workflow replay, and fresh ENiGMA/Synchronet editor screen/log sessions.
The public export reproduces TERMINAL and ASPECT without original executables,
previous objects, installation data or Git metadata.

```sh
./tools/dev --command python3 standalone/test_phone_log_carrier_terminal.py \
  --terminal build/midframe-carrier-fixed-source-01/build/terminal-phone-log-bank-d882144fee4f \
  --label fragment-carrier-check-01 --fragment
./tools/dev --command python3 standalone/check_modem_init_policy.py \
  --product build/midframe-carrier-fixed-source-01/build/terminal-phone-log-bank-d882144fee4f \
  --output build/midframe-init-policy-repeat-01
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/midframe-carrier-fixed-source-01/build/terminal-phone-log-bank-d882144fee4f \
  --runner build/aspect-register-parent-custom-irq/ASPECT.EXE \
  --output build/phone-log-midframe-carrier-public-repeat-01 \
  --commit 9448e95 --extended --permissions --slow --watermark --carrier \
  --aspect-carrier --transfer-carrier --batch-carrier --fragment-carrier
```

Use fresh labels/output directories. The accepted old matrix follows a reporter
fix for missing second-call timestamps; the first incomplete reporter attempt
and an initial linked check of a private non-exported symbol are excluded.
These are 8086 COM3/IRQ5, 19200/8N1 HARD virtual-modem header cuts, not every
frame offset, flow/profile or physical Boca/SPA2102/SIP/audio timing. Responses
later than the configured strict guard cannot be correlated generically.
Generic-child/fault coverage, broader rendering, full original UI/F01–F16 and
physical/card acceptance remain open. The validated terminal is still separate
from the published helper bundle; matched package staging/acceptance remains
necessary before deployment. An isolated attempt to compose the original Alt-Z
reference option with this logging variant exceeds resident CS by 50 bytes;
additional banking is required to retain both. This exploratory layout is not
an accepted application build. Published package/card, live BBS, installed
bridge service, ATA and host network are unchanged.
