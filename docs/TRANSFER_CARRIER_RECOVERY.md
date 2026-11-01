# Transfer carrier loss and modem command recovery

The call-log candidate now skips protocol cancellation output after a confirmed
carrier-loss failure. Previously the native receive workflow emitted two CAN
bytes after the modem had returned to command mode. The next initialization
became `CAN CAN AT&K3` and returned ERROR, although a later ATD could still connect.
That could hide failed modem initialization behind an apparently successful
redial. The fixed terminal sends a clean initialization on the second call.

## A retained failing case

An independent XMODEM peer requests CRC and sends eleven valid 1 KiB frames,
requiring each real ACK before continuing. The native receiver buffers 10 KiB
before its first DOS write. Before dropping TCP, the fixture independently reads
at least 8 KiB of the exact owned stage prefix from the host filesystem. DOSBox's
buffering can retain part of the successful 10 KiB DOS write until close, so host
visibility and the product's successful-write count are checked separately.

The prior `003bc6b7...` image fails only the clean-two-initializations check in
the final counterexample. Its first call, frame ACKs, exact staged prefix,
10 KiB successful-write count, cleanup, call records, original START stamps,
second-call terminal replies and hardware restoration all pass. Its modem log
records the cancellation prefix and ERROR on the second initialization. Earlier
stage-visibility probes are excluded from accepted evidence.

## The application change

The maintained foreground failure owner checks for carrier fault 4 before
sending cancellation. Receive/upload storage cleanup has already run; the
ordinary finish path still restores UI and returns ownership. Other failure
reasons retain their bounded cancellation behavior. The second CAN uses the
existing writer's preserved AX rather than reloading the same byte.

This is a confirmed-carrier-loss guard, not a new modem command dialect or a
change to recovered UART code. Carrier falling during some other cancellation
reason, broader protocol combinations and physical timing remain separate work.
The fixed image is `512f782e9befeef39db1f8dfe03b6b786e89d44910cc99bb0ea4f7d83bbb3eba`.
The near data/stack group remains 64,752 bytes with 784 bytes spare. Resident CS
has 65,534 bytes and only two spare; further resident growth needs code banking.

## Actual DOS workflows

Four 8086 COM3/IRQ5, 19200/8N1 HARD cases use DOSBox-X's built-in modem and real
virtual DCD. The peer supplies protocol/ANSI bytes, never fake modem responses
or product variables:

- Receive loss after the actual CRC request, before any file data.
- Receive loss after eleven ACKed 1 KiB frames and the first real DOS write.
- Upload loss after independently validating the first complete frame and CRC,
  before ACKing it.
- Upload loss after ACKing the first frame and validating the next complete
  frame, leaving it unacknowledged.

Every case requires fault 4, resolved transfer ownership, closed and unambiguous
receive/upload handles, no receive destination or stage, and an unchanged upload
source where applicable. The same DOS parent redials, initializes cleanly,
answers fresh terminal queries, accepts keyboard text and saves exactly two call
pairs while preserving the old log prefix and original START stamps. Directory
accounting advances twice and the 42-byte hardware snapshot is restored.

The independent linked regressions cover 44 receive inputs, 54 upload inputs
and five ZMODEM foreground cancellation cases. These execute the application
instructions with modeled BIOS/UART/DOS boundaries; the four modem workflows
are actual DOSBox DOS runs. Neither is physical modem evidence.

## Reproduction and remaining work

The [validation receipt](validation/transfer-carrier-recovery.json) binds the
failing old-image case, four passing native cases, linked regressions, clean
public-source replay, and fresh ENiGMA/Synchronet screen/log sessions.

```sh
./tools/dev --command python3 standalone/test_phone_log_carrier_terminal.py \
  --terminal build/transfer-carrier-fixed-source-01/build/terminal-phone-log-bank-d882144fee4f \
  --label transfer-carrier-check-01 --transfer
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/transfer-carrier-fixed-source-01/build/terminal-phone-log-bank-d882144fee4f \
  --runner build/aspect-register-parent-custom-irq/ASPECT.EXE \
  --output build/phone-log-transfer-carrier-public-repeat-01 \
  --commit adee836 --extended --permissions --slow --watermark --carrier \
  --aspect-carrier --transfer-carrier
```

The source replay rebuilds the fixed terminal and unchanged ASPECT runner without
original executables or previous objects. It repeats all 53 logging/access/flow/
carrier/script/transfer workflows. Use fresh labels and output directories.
The candidate was built separately so earlier accepted binaries remain intact.

YMODEM/ZMODEM carrier-loss workflows, generic-child/fault exits, every emulation
and BBS frame/profile, full original UI/F01–F16 integration and physical
Boca/SPA2102/card acceptance remain open. The published package/card, live BBS,
installed bridge service, ATA and host network are unchanged.
