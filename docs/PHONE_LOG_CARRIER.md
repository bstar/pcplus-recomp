# Carrier loss, logging and same-process redial

The 24-row call-log candidate now passes three real virtual-modem workflows:
ordinary loss, loss during a HARD log write, and loss during a SOFT log write.
All three redial in the same DOS parent, restore interactive input and save
exactly two complete call pairs. The application image remains unchanged.
This extends selected connection/logging composition; full application and
physical acceptance remain open.

## Actual carrier rather than a serial-text simulation

DOSBox-X's built-in modem owns CONNECT/NO CARRIER responses and its virtual
MSR/DCD signal. An owned loopback peer sends ANSI cursor/capability queries,
waits for both actual replies, sends an incomplete CSI and aborts TCP. It never
supplies a modem result string or patches product state. A second accepted
connection supplies a fresh screen and queries; real BIOS Alt-D redials and
later keyboard text provokes another real cursor reply.

The fixture uses 8086 code, COM3/IRQ5, 19200 baud and 8N1. Its real emulated modem
initializations are AT&K3 for HARD and AT&K4 for SOFT, twice per case. Those are
fixture settings, not a prescribed initialization for unidentified Boca hardware.
Each case requires an actual NO CARRIER emulator event, two TCP connections,
new terminal replies, keyboard input after redial and normal DOS exit.

## Drop during a write

The first real START append is held for 36 BIOS ticks with interrupts enabled.
The existing delay fixture additionally reads the actual modem-status port.
In accepted delayed cases it records DCD high at entry and low while the hold
is still active. UART receive-drop counters stay zero. A zero-tick HARD control
records high carrier through its write and experiences the later ordinary drop.

The fixture captures the first original START timestamp at write entry, before
carrier loss. It is compared with the final saved row. Stable parent samples
independently bind the second START. The ordinary observer deliberately skips
busy queue snapshots, so it cannot supply the first timestamp witness during
the held write; the entry capture closes that observation gap.

END records the foreground observation time after the stall. Physical-drop
ordering is retained separately in the fixture's event/MSR trace. The checks
do not invent an earlier END time or claim an ISR-level timestamp.

## File, directory and restoration checks

Each owned log starts with an old heading/call. That entire prefix must remain
byte-exact, followed by precisely two START/END pairs with the selected directory
name and loopback target. The queue finishes at generation 2 with four committed
events, four append attempts, no pending records, no retry acknowledgements and
no logger error. The synthetic directory's connection/date accounting advances
exactly twice. PRM and fixture executables/configuration remain unchanged.

The second connection requires fresh CPR/DA and positioned-screen replies,
then `ready` keyboard text and the expected response to a new row 3 query.
The native 42-byte hardware snapshot and the observers' vector restoration
checks must pass. No new DOS process substitutes for the original parent's
redial. Reading MSR clears its delta bits; this is declared instrumentation,
and the native connection policy uses the carrier-level bit.

## Reproduction and remaining work

The [receipt](validation/phone-log-carrier.json) binds the final three native
cases and a clean committed-source rebuild/replay of 45 workflows: these three
plus 42 existing logging/access/flow regressions. Default and watermark delay
fixtures remain byte-exact with their earlier accepted versions when the new
carrier option is disabled. Earlier peer-collection and timestamp-witness
attempts are excluded; only the final matrix and public repeat are accepted.

Image: `build/terminal-phone-log-bank-d882144fee4f/TERMINAL.EXE`.
SHA256: `003bc6b7a0529c737b697c1149d2cfecfef930b5e96406df9dba31d9c137380f`.
The prior [stock-BBS screen/log evidence](PHONE_LOG_STOCK_BBS.md) still applies
to these exact unchanged bytes; this checkpoint does not repeat those sessions.

```sh
./tools/dev --command python3 standalone/test_phone_log_carrier_terminal.py \
  --terminal build/terminal-phone-log-bank-d882144fee4f --label carrier-check-01
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/terminal-phone-log-bank-d882144fee4f \
  --output build/phone-log-carrier-public-repeat-01 \
  --commit e319654 --extended --permissions --slow --watermark --carrier
```

Use fresh lowercase labels/output directories. This is real virtual DCD with
synthetic ANSI peers, not physical Boca/SPA2102/SIP/analog acceptance. Loss during
ASPECT, transfers, generic children and exceptional exits, all response-deadline/
menu/feature combinations, long transfers and every BBS frame/profile remain
open, alongside full F01–F16 and deployment acceptance. The published package,
card, live BBS, installed bridge service, ATA and host network were not changed.
