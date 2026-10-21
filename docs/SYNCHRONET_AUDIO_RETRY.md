# Same-call cancellation and retry

The next audio integration gate exercises the ordinary DOS XMODEM sender twice
on one stock Synchronet connection. The first attempt must receive an ACK and
cancel at a complete CRC packet boundary. The second must send the same local
file, without an application restart, to a fresh remote filename and complete
the receiver's two-EOT NAK/ACK exchange. Files and Main must remain interactive.
This gate does not establish physical Boca/SPA2102 compatibility.

The reference connection in
`build/bbs-lab/synchronet-audio-retry-reference-01` passes eleven checks:
one connection, CRC/ACK/CAN, Files, a fourteen-block full retry, exact source and
padding, official metadata and preservation of the first partial and prior
files. This is a TCP reference, not evidence that the DOS/audio route passes.
The DOS keyboard probe passes six checks; fifteen initial ASPECT waits also
match the reference's raw bytes. Those are preparation checks only.

The actual audio attempt is
`build/bbs-lab/synthmodem-synchronet-retry-audio-01`. A read-only observer has
captured the first 2,048-byte partial, including its inode, modification time,
content and complete official FileBase metadata, before the second target was
indexed. Actual retry acceptance remains pending. The watchdog is intended to
return normally to DOS and capture the final visible screen if automation
cannot advance.

The producer and independent audit bind the native executable, source,
ASPECT compiler and script, keyboard helper, runtime, server inputs and raw
transport captures. `audit_synchronet_retry_metadata.py` compares the retained
partial against that live snapshot and checks the full retry's bytes, padding,
official hashes and receiver records. `check_synchronet_retry_controls.py`
rejects twelve timing, source, cancellation and finish counterexamples using
copies of the captured streams. Its synthetic thirteen-check self-test passes;
the actual-capture checks require a completed, passing independent audit.

Stock Synchronet has already been observed publishing cancelled partials.
Retaining an indexed partial is a separate server cleanup gap even if a later
full retry succeeds. Neither an upload log entry nor an indexed filename alone
proves successful delivery. No test deletes the partial or changes the receiver
to make that gate pass.
