# Transfer reliability on the current connection candidate

The Screen Pause candidate remains
`501629c093d731be8f3324f185e128af76e00c2942e5ad3463c1ce7da54edb6e`.
This checkpoint tests that existing source-built application; it does not select
a different executable or change original-command availability. The
[receipt](validation/transfer-release-readiness.json) binds the tested products,
source sets, independent peers and reports.

## Successful transfers and cancellation

The release transfer harness selects the real original-reference PgUp/PgDn
actions through BIOS Alt-Z, acknowledges the original splash, and loads an
explicit synthetic COM3/3E8h/IRQ5,19200,8N1,HARD configuration in DOS8086.
It uses fresh owned media, clears PCPLUS environment lookup, checks the PRM
and source files afterward, and compares UART/PIC/IRQ state before and after.
It does not read a private configuration or mount a physical card.

Independent Python X/YMODEM peers validate framing, integrity, sequence, padding,
EOT policies and binary files. ZMODEM uses the pinned Nix lrzsz peer. Binary data
contains every byte value, embedded XON/XOFF, NUL and SUB; batches include empty
and odd-length files. XMODEM has no length metadata: complete receive blocks and
the sender's defined padding are checked rather than trimming arbitrary SUBs.

The matrix includes CRC/NAK retries, local Escape, peer CAN, and a bad subsequent
YMODEM header after a committed file. A separate YMODEM case cancels negotiation,
proves ordinary parser/keyboard return, starts the real transfer menu again and
completes a new batch on that same DOS process and serial connection. Each
non-exit case requires a post-transfer DSR response and actual keyboard bytes,
the restored application screen, and no partial transfer stage files.

The first XMODEM preflight completed its file and DSR checks but scheduled the
keyboard marker after its peer's ten-second application window. That run is
retained as failed fixture evidence. The final harness schedules small XMODEM
markers inside that bound; batch/independent peers retain longer bounds.

## Real emulated carrier loss and reconnect

The existing call-log/carrier harness uses DOSBox's modem device on COM3/IRQ5.
The peer closes its TCP connection; the modem device generates NO CARRIER and
changes the virtual DCD level. The observer reads actual application/hardware
state rather than writing a synthetic carrier result into the product.

Four XMODEM cases cover negotiation, staged receive progress, an unacknowledged
upload and an upload with accepted progress. Ten Y/ZMODEM cases cover metadata,
data, earlier committed receive files and uploads. Four additional cases drop
inside metadata/header fragments under legacy and acknowledged initialization.
All require clean owner/handle/stage retirement, a second connection in the same
parent, restored keyboard/query processing and preserved call history. The
completed files from earlier batch items must survive loss of a later item.

Four ASPECT cases exercise disconnect while waiting or in WHEN handling, with
and without the parent script window. These prove those child-return scenarios;
they do not close the complete ASPECT feature-parity gate.

## Fixed DTE and slow-carrier timeouts

The deadline checker now accepts an explicit release image and fresh output,
so evidence cannot silently describe the historical default terminal instead.
The linked receiver runs with modeled1200bps wire time at both1200 and38400 DTE.
It also receives a maximally quoted8KiB packet at the supported300bps floor,
retains the direct-session budget and expires a silent peer through ordinary
retry handling. UART, DOS and clock boundaries are modeled here. This is not a
measurement of SynthModem DSP or an analog carrier.

## Remaining acceptance

The DOS transfer success matrix uses nullmodem delivery; carrier-loss matrices
use the emulated Hayes modem. Neither traverses SIP/audio through the SPA2102
or measures the Boca's real flow-control/IRQ timing. Enigma/Synchronet editor
and rendering receipts remain separate; these transfer fixtures do not claim
a successful upload/download through those BBS file areas.

The physical BUSY/reboot outcome and transfers through the actual Boca → SPA2102
→ SynthModem → BBS route remain open. The management endpoint timed out during
this checkpoint, so the selected installed payload and private settings were
not changed. No live BBS or SynthModem service was restarted. Elapsed Time,
remaining original commands and the full-parity inventory remain active work.

```sh
./tools/dev --command python standalone/test_release_transfers_dos.py \
  --terminal build/SELECTED/TERMINAL.EXE --label new-unique-label --jobs 4
./tools/dev --command python standalone/check_carrier_transfer_deadline.py \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW-deadline/result.json
./tools/dev --command python standalone/test_phone_log_carrier_terminal.py \
  --terminal build/SELECTED --label new-carrier-label --batch
```
