# Batch carrier loss, retained files and logged redial

The fixed call-log terminal now exercises YMODEM and ZMODEM carrier loss in
addition to ordinary XMODEM. Each protocol has five actual DOS workflows:
receive loss after metadata, receive loss after data writes, a completed first
file followed by loss during the second, upload loss after metadata, and upload
loss after one ACKed data frame and a second unacknowledged frame.
The terminal binary remains `512f782e9befeef39db1f8dfe03b6b786e89d44910cc99bb0ea4f7d83bbb3eba`.

## Independent wire and file checks

Real BIOS Alt-R/Alt-S opens the transfer dialog; real F2 selects YMODEM or
ZMODEM before the filename/directory is entered. An owned loopback peer validates
protocol headers and CRCs and waits for actual product responses. The Python
peer uses an independent wire oracle, not product callbacks or state writes.
DOSBox-X's modem produces CONNECT/NO CARRIER and virtual DCD from the real TCP
connection lifecycle.

Receive data cases send nine CRC-accepted 1 KiB packets, requiring each actual
ACK before proceeding. The successful DOS-write count must be 9,216 bytes.
Before carrier loss the peer independently reads at least 8 KiB of the exact
stage prefix from the host filesystem; DOSBox buffering can retain the last
part until close. Metadata-only cases require zero data writes. On failure,
the unfinished target and stage must be absent, with closed, unambiguous file
handles and no cleanup error. Retained-file cases additionally complete and
independently read `FIRST.BIN` before offering `ONE.BIN`; the exact first file
must survive cleanup of the unfinished second file.

Upload cases validate the actual SEND.BIN identity and size in metadata. Data
cases validate two complete frames including source bytes/CRC, ACK only the
first, then drop carrier. The source must remain byte-exact and its handle must
be closed without uncertainty. Protocol choice, batch owner state, completed
file counters and the shared storage snapshots are read by the optional observer.
The observer makes no product-memory or UART-output writes; MSR reads clear
hardware delta bits, while the application carrier policy uses the level bit.

Every case requires confirmed carrier fault 4 and resolved transfer ownership,
then real Alt-D redial in the original DOS parent. Both modem initializations
must be clean. New cursor/capability queries, keyboard text and a positioned
reply verify that interaction resumed. The old log prefix and original START
stamps survive exactly two START/END pairs, directory accounting advances twice,
and the 42-byte hardware snapshot is restored.

## Reproduction and scope

The [receipt](validation/batch-carrier-recovery.json) binds ten final native cases
and a 38-workflow committed-public-source replay: these ten, four XMODEM loss
cases and 24 existing-log/menu controls. The previous [53-workflow checkpoint](TRANSFER_CARRIER_RECOVERY.md) applies to this exact unchanged image, including
its linked regressions and stock ENiGMA/Synchronet screen/log sessions. Those
BBS sessions are not rerun at this checkpoint. Across the two public checkpoints
there are 63 distinct workflows; this checkpoint alone repeats 38.

The default and ordinary-transfer observer modes remain byte-exact with the
previous accepted fixtures when the batch extension is disabled. The public
export rebuilds the terminal without original executables, prior objects,
installation data or Git metadata.

```sh
./tools/dev --command python3 standalone/test_phone_log_carrier_terminal.py \
  --terminal build/transfer-carrier-fixed-source-01/build/terminal-phone-log-bank-d882144fee4f \
  --label batch-carrier-check-01 --batch
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/transfer-carrier-fixed-source-01/build/terminal-phone-log-bank-d882144fee4f \
  --output build/phone-log-batch-carrier-public-repeat-01 \
  --commit 52c6671 --transfer-carrier --batch-carrier
```

The first exploratory YMODEM upload peer sent speculative CRC requests while
filename entry was still active, provoking a header retry. Its unintended drop
during that retry left bytes before the next AT initialization. Those runs and
the stopped first public replay are excluded. The corrected peer negotiates
after filename entry. Deliberate mid-frame loss and command-prefix recovery
remain concrete follow-up work; complete-boundary checks do not close that gap.
The existing modem resynchronization path is requested on canceled/aborted dials
but not ordinary DCD loss; its use on reconnect is the next implementation lead.

Use fresh lowercase labels/output directories. These are 8086 COM3/IRQ5,
19200/8N1 HARD virtual-modem cases, not physical Boca/SPA2102/SIP/audio evidence.
CRC16/CRC32/streaming/window/profile combinations beyond the stated peers,
carrier falling during another cancellation reason, generic children/faults,
broad rendering/full original UI/F01–F16 integration and physical/card acceptance
remain open. The terminal has only two spare resident-code bytes. The published
package/card, live BBS, installed bridge, ATA and host network are unchanged.
