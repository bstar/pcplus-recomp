# Live ordinary XMODEM uploads

Alt-S opens an upload filename prompt. Enter an existing DOS8.3 source path of
at most63 bytes. Use HARD or NONE to match the modem; SOFT is rejected before
prompting or opening because its ISR consumes valid binary flow-control bytes.
Escape cancels, and Alt-X cancels then exits through normal cleanup.

Select the remote upload protocol and wait for the complete receiver-ready
message before pressing Alt-S. The recovered initial handshake has a bounded
attempt count that can be exhausted by a receiver's banner if the local sender
starts too early. A linked reproduction confirms this sensitivity; it has not
been fixed by changing the native sender. The
[same-call audio retry work](SYNCHRONET_AUDIO_RETRY.md) preserves a failed early
start and tests a recipe that waits for the complete remote banner.

The source is opened read-only and remains unchanged. The maintained bridge
supplies the recovered sender with one checked physical handle, full32-bit
length/read accounting and exactly-once close. See [source ownership and
recovery](UPLOAD_SOURCE.md). A source error or uncertain close prevents successful
completion. The source closes before EOT is sent; the ordinary peer must ACK EOT.

The native protocol2 sender chooses1024-byte blocks for files at least1024 bytes,
otherwise128. It shrinks later blocks to128 when fewer than897 declared bytes
remain. The final block is padded with1Ah; ordinary XMODEM carries no exact-size
metadata. Empty files send EOT without a data block. `C` selects CRC and NAK selects
checksum. Native `G` also selects CRC without enabling streaming; this is not a
claim of XMODEM-G support. Alternate U/W/metadata handlers remain explicit failures.

One exclusive owner shares the11264-byte near arena with downloads. Receive and
send counters/checkpoints remain separate. The real UART ring/count and recovered
ISR are used. Waiting services flow, carrier, receive overflow, Escape/Alt-X and
full-clock deadlines without running the parser, macros, PROGRAM or dialing.
The outer nonlocal context exists before native open/UI/setup callbacks.

Uploads use the same36-tick physical transmission stall limit and540-tick
no-progress budget as downloads, with2160 ticks below1200baud. The native timed
read adapter uses19 BIOS ticks per requested second; a block/EOT ACK wait requests
10 seconds. Native retry bounds are15 block attempts and10 EOT attempts, with
the maintained overall no-progress budget able to stop earlier. Failed sessions
send a bounded best-effort CAN pair once transmission has started.

The native block counter advances even on its fifteenth failed attempt. Live
progress instead counts actual ACKs returned to the recovered block-wait return
site, with a separate DWORD of padded bytes accepted. Handshake/EOT ACKs and
rejected attempts do not count. Successful close/completion also requires those
accepted bytes to cover the source snapshot. A protocol abort closes through the
abort path even when the source was partly prefetched; this preserves peer-CAN
cancellation and retry-timeout status without manufacturing a disk error. Native baselines
remain unchanged and independently testable. UI keys and safety adapters are
maintained application behavior, not a claim of recovered original upload UI.

```sh
./tools/dev --command python3 standalone/check_terminal_upload_live.py
./tools/dev --command python3 standalone/test_terminal_upload_dos.py \
  --sha256 SHA256_OF_TERMINAL_EXE --label my-upload-run
```

The linked checker executes the actual controller, sender, C file ownership,
UART ISR and UI. Only hardware/BIOS/DOS syscalls are modeled. Its independent
peer validates frame integrity, sequence and padding, and covers retry-counter
misreporting, source-close-before-EOT, storage faults, early cancellation,
carrier/CTS/THRE, timeout/wrap and ownership rejection.

The actual DOS peer checks serial frames and source immutability, then verifies
parser/keyboard/video use and independent UART/PIC/vector restoration. Large and
rollover cases are available explicitly; inspect retained case lists and hashes
rather than assuming every recipe ran. Evidence is in
`docs/validation/terminal-upload*.json`.

Batch/window/streaming protocols, the other advertised protocol families, full
settings/progress UI, logging and physical DOS/modem/BBS transfers remain open.
This upload path and ordinary downloads are part of the full PCPlus rebuild,
not completion of the complete application feature inventory.
