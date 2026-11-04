# Binary-transfer carrier loss at accepted text heights

The current source-built terminal now has composed transfer/modem recovery
evidence at25/28/43/50 physical rows. Each actual8086 DOS workflow enters a real
transfer, loses the virtual modem's carrier at an independently checked boundary,
cleans up, and redials in the same parent process. The second call must initialize
successfully, answer new terminal queries and accept keyboard text. A separately
reproduced local-cancel/carrier race is fixed in the maintained cancellation
writer. The existing [transfer row leases](TRANSFER_ROW_LEASES.md) remain intact.

## Cancellation during file cleanup

A linked differential probe cancels after a real block ACK and drops modeled
DCD at the real DOS file-close boundary. The old image preserves cancellation
fault2 and cleans its file, then still emits two CAN bytes into command mode.
The writer previously skipped cancellation only when carrier fault4 was already
the first error; it did not account for later carrier loss during cleanup.

The common cancellation writer now checks current DCD before each attempt when
this transfer previously observed carrier high. Known low carrier ends that
output attempt without changing the first diagnostic. High carrier or a link
whose DCD was never observed retains the existing cancellation policy. No parser,
DOS callback or new blocking wait was added. The existing36-tick bound, register
preservation and cleanup path remain.

Twelve baseline/candidate linked cases cover Escape and Alt-X with high carrier,
loss during close, and untracked DCD. The candidate keeps fault2 and closes the
stage/handles while suppressing late CAN only in the known-loss case. Ordinary
real DOS regressions separately cover normal cancellation. Exact coincident
physical timing is not established by the modeled race.

## Failure matrix

There are18 scenarios at each of four heights,72 workflows and144 virtual modem
connections. They use COM3/IRQ5,19200,8N1,HARD flow and the actual original-menu
paths for transfer and redial. The owned peer validates CRC/data/metadata, then
closes its TCP socket. DOSBox-X supplies CONNECT/NO CARRIER and DCD changes. No
modem reply, product variable, file-owner result or parser callback is injected.

- XMODEM receive loss occurs after CRC negotiation or eleven ACKed1KiB frames.
  The latter exercises the real10KiB DOS write and an exact visible stage prefix.
  Upload loss occurs after a validated first frame without ACK, or after ACKing
  the first and validating a second unacknowledged frame.
- YMODEM and ZMODEM each cover receive metadata, receive data, a completed first
  file followed by interruption of the next, upload metadata, and partial upload.
  Receive-data cases require nine ACKed1KiB frames and9,216 successful write bytes.
  Earlier completed `FIRST.BIN` remains exact while the unfinished target/stage
  is removed.
- Each batch protocol also loses carrier after exactly16 validated upload-header
  bytes, before complete metadata, in both legacy and acknowledged modem-init
  modes. These deliberately exercise command-channel resynchronization.

Upload bodies contain all256 byte values, repeated to4KiB. Receive bodies use the
same full-byte pattern. Primary peers validate exact bytes and CRC on the wire,
and read the owned stage prefix before closing the connection. This includes NUL,
FF, XON, XOFF and bytes that would have meaning to an ANSI parser. The completed
retained-file fixture keeps its existing fixed contents.

Every case requires transfer fault4, no RX drops, retired active/pending owners,
closed/unambiguous source and receive handles, absent unfinished files, preserved
upload contents, and exact directory accounting for two calls. The existing
call-log observer additionally verifies four append attempts, two exact START/END
pairs, original START timestamps and preservation of the previous file prefix.
The hardware snapshot must return to its42-byte baseline.

## Command resynchronization

Interrupted metadata can still be leaving a UART when the modem changes to
command mode. In the observed ZFILE-fragment cases, the `IN` suffix from
`SEND.BIN` is terminated by the existing retry separator and receives one modem
ERROR. That response belongs to the retired fragment. The subsequent `AT&K3`
must independently receive OK before the selected dial command connects.

The verifier permits that exact suffix only for ZMODEM-header-fragment scenarios,
where in-flight timing can expose it in either initialization mode. Its single
ERROR must occur after the first NO CARRIER and before the
second initialization. All other cases require no modem ERROR. Every initialization
is separately checked for its own OK; a successful second connection cannot hide
a corrupt initialization. Empty separator lines and a configured final ATH are
allowed, with no other command prefixes accepted. This preserves the existing
[mid-frame recovery policy](MIDFRAME_MODEM_RECOVERY.md).

The first exploratory assertion required zero ERROR responses everywhere and
incorrectly rejected that intended resynchronization path. The final matrix was
rerun with the explicit response-phase check. The cancellation-writer fix is a
separate application change, supported by its own differential probe.
These virtual-modem initialization strings are owned fixtures and are not new
recommendations for unidentified physical modem hardware.

## Display and independent evidence

The passive BIOS observer from the row-lease checkpoint witnesses one transfer
prompt/restore in each workflow. All72 two-row/cursor/shape/font/height leases must
restore exactly. Initial and reconnected streams must both answer a CPR from the
selected final logical row. Fresh redial-position and keyboard-position reports
verify ordinary parser/input ownership afterward.

The [receipt](validation/large-transfer-carrier.json) binds the exact parents,
fresh source rebuild proofs, test sources and immutable case artifacts. The
separate artifact verifier checks raw transfer/storage and BIOS snapshots, file
trees and source vectors, scoped modem responses, two call pairs, scratch cleanup
and hardware restoration. Primary peers perform the pre-deletion stage-prefix
and wire CRC/data checks. The public recipes operate only on fresh owned media.

The ordinary source-built image is
`85b47b183e14e829a433727092d824bd14727ac2db3925c3b2e8b46952295f03`.
Five fresh569-source parent rebuilds reproduce exactly. Near data remains65,120
bytes; resident CS is65,500 bytes, with36 spare. Diagnostic parents use65,526
resident bytes, with10 spare; further resident growth needs code banking.
Recovered UART instructions, original splash and LoC annotation, private
configuration and selected deployment package are unchanged. Startup height
diagnostics remain internal and cannot be packaged.

These are virtual-modem/component results, not Boca/SPA2102/SynthModem audio or
Enigma/Synchronet file-transfer acceptance. Other concurrent cancellation/fault
timings, protocol/flow/profile combinations, remaining
terminal controls and broader original application parity remain open. The
physical DOS machine, installed bridge, network and BBS configuration were not
changed. The full goal remains active.

## Reproduction

Build fresh diagnostic parents using the pinned toolchain and the public flags
bound by this checkpoint's receipt:

```sh
./tools/dev --command python - <<'PY'
import json, subprocess, sys
receipt = json.load(open('docs/validation/large-transfer-carrier.json'))
for rows in ('25', '28', '43', '50'):
    subprocess.run([sys.executable, 'standalone/build_terminal.py',
                    *receipt['images'][rows]['build_flags'],
                    '--output-dir', 'build/carrier-repeat/' + rows], check=True)
PY
./tools/dev --command python standalone/test_large_transfer_carrier_dos.py \
  --build build/carrier-repeat --rows 28 --jobs 2 \
  --output build/carrier-repeat-results/28
```

Use fresh output directories for every run and repeat at the other heights for
the complete matrix. The built-in modem's loopback Internet dial target belongs
to the emulator; real modems continue to dial the adapter and enter the BBS
address after the bridge's carrier connection.
