# Transfer packet deadlines with fixed DTE

The first [audio download](audio-download.md#first-audio-counterexample) exposed
a real receiver defect: a38400-bps UART deadline expired while a valid4KiB
packet was arriving over a1200-bps modem carrier. Raising or lowering the actual
UART rate is not a suitable correction for a modem using fixed DTE.

`terminal_transfer_set_budget` now distinguishes connected modem sessions from
direct-directory and raw serial sessions. A modem CONNECT from the current
first-completion result matcher does not supply a reliable carrier-speed lower
bound. For that context the owner therefore uses its existing300-bps worst-case
packet allowance:17280 BIOS ticks for ZMODEM/ZedZap and2160 for X/YMODEM.
These cover a fully quoted8KiB receive packet and a1KiB ordinary packet before
CRC-accepted progress can exist. Direct/raw sessions retain their UART-derived
budgets. The change adds no data storage and does not alter the configured DTE,
divisor, result strings, protocol codec or server configuration.

This is an outer verified-progress deadline, not a promise to wait that long for
a silent peer. Protocol idle reads/retries, physical TX/CTS stall bounds,
carrier loss, local cancellation and storage checks remain active. Unverified
bytes do not refresh accepted progress. The code still bounds a peer that keeps
delivering data without a verified packet. Carrier-speed reporting and a user
override for this allowance remain future configuration work.

## Evidence

The [paired linked proof](../../docs/validation/carrier-transfer-deadline-fixed.json)
uses the same checker against the saved pre-fix executable and current source
build. Both execute the actual receiver, watchdog, UART ISR and file owners;
UART/BIOS/DOS boundaries are modeled. The old fixed38400-DTE case times out at
1200-bps carrier input; the corrected case installs the file exactly. Matched
1200-DTE input also passes. A fully quoted8KiB first packet passes at the modeled
300-bps floor. Direct budgets stay unchanged and a peer silent after metadata
still fails after612 modeled ticks, without installing a file or retaining an
open handle. The original failed probe prerequisites remain recorded separately.

```sh
./tools/dev --command python3 standalone/check_carrier_transfer_deadline.py
./tools/dev --command python3 standalone/check_carrier_transfer_deadline.py --counterexample
```

The second command uses the ignored saved baseline under
`build/terminal/carrier-deadline-baseline`; it deliberately records
`counterexample_reproduced`, not product acceptance. The default checker is part
of `test-terminal-zmodem-live`.

The [native regression receipt](../../docs/validation/carrier-transfer-deadline-regression.json)
also records78 passing linked ZMODEM workflows, five foreground cancellation
cases and three far-call/IRQ/layout groups on the corrected executable. This
keeps prior protocol, file-owner and ABI checks separate from the new timing
model and subsequent audio call.

The [actual DOS regression](../../docs/validation/carrier-transfer-deadline-dos.json)
passes all14 checks against pinned lrzsz: automatic ZedZap receive without
transfer keys, three exact files including65797 bytes, subsequent DSR/keyboard,
normal return and restored UART state. This is a fast direct link, separate
from slower-carrier acceptance.

The normal audio repeat is `synthmodem-audio-download-02`, using the unchanged
11521-byte BBS fixture, full artwork and stock helper. Its producer freezes the
corrected source, executable/map, checker and native receipt. No audio acceptance
is established until the complete same-run byte, CRC/control/finish, file,
post-helper input and cleanup audits pass. The
[stock helper's pinned source](https://github.com/SynchronetBBS/sbbs/blob/e7a825704ef5329c7ef8408749671291a85ef7f2/src/sbbs3/zmodem.c)
also has its own receive/retry deadlines. A local correction alone does not
prove the peer's delayed replies, retransmissions or finish will succeed.
