# Live XMODEM receive integration

Alt-R opens a DOS filename prompt and starts one foreground XMODEM download.
Use HARD or NONE to match the modem. SOFT is rejected before prompting or
creating a file: the original software-flow ISR consumes valid binary11h/13h
bytes. This is a maintained live receive policy built around the recovered
native engine; it is not a complete transfer/settings implementation.

## Files and completion

Enter an explicit normalized DOS8.3 destination of at most63 bytes, including
its path. The destination must not exist. `PCRX.$$$` in the same directory is
created exclusively; a preexisting stage is never adopted or removed. The
native engine writes through the checked DOS bridge into that prepared stage.
Close seals it; checked no-overwrite rename installs the completed file.
Ordinary XMODEM has no exact-length metadata: received128/1024-byte blocks,
including sender padding, are retained without guessing the original length.

The recovered engine normally ACKs EOT before final file IO and ignores final
write/close results. Its exact diagnostic remains unchanged. The live adapter
suppresses that final ACK until the maintained owner independently verifies
writes, close and installation. Failed or uncertain storage never receives a
success ACK. A complete stage whose rename failed is retained for recovery;
an uncertain close is never retried against a possibly recycled handle. Inspect
`PCRX.$$$` after an RX recovery notice; do not delete an unfamiliar existing
stage. A saved file whose final ACK cannot be sent remains saved and reports
`RX saved; ACK?`.

## Ownership and waits

One native receive invocation owns its BP frame, receiver state and11264-byte
near arena. Its queued-byte aliases use the actual UART receive count. The live
callbacks service UART flow, cancellation, carrier loss and receive overflow;
they do not run the ordinary parser, macros, PROGRAM or dial controller while
binary reception owns the link. Escape cancels; Alt-X cancels and exits through
normal hardware cleanup. The maintained outer setjmp context exists before
the first native handshake, allowing safe cancellation even before the native
receiver establishes its inner context. No ISR performs a nonlocal unwind.

Prior queued text drains before negotiation. Only actual transmission progress
refreshes the36-tick stall deadline. Native timed reads use19 BIOS ticks per
requested second, clipped to30 seconds. A separate no-progress deadline is540
BIOS ticks, extended to2160 below1200baud. Midnight wrap is handled explicitly.
The unresolved native calibrated delay6b72 is replaced by a serviced two-tick
quiet interval; this is a documented maintained timing choice, not recovered
original timing. The native6b98 BIOS-tick wait remains a distinct callback.

The first EOT receives NAK, followed by the second EOT and checked installation.
For190 ticks after completion a repeated EOT is ACKed without reopening or
rewriting the file. The first non-EOT byte returns to normal parsing unchanged.
Failure always returns storage ownership to the maintained cleanup path, even
when the native timeout returns with its file logically open.

## Memory and PROGRAM

The8192-byte erase shadow and4096-byte history ring retain their full sizes in
an ungrouped FAR_STORAGE segment. Original helpers already use far pointers;
startup/RIS clearing now loads the actual segment. History survives RIS.
The11264-byte receive arena stays near to preserve the recovered ABI.

`standalone/terminal_memory.py` verifies the map, serialized far pointers and
MZ relocation/allocation records at build time. DS equals SS and DGROUP must
remain below64KiB. PROGRAM retains the higher of STACK end and FAR_STORAGE end,
even when Wlink places far storage after STACK. Linked tests cover original far
movers, history wrap, RIS and parent memory retention. An actual DOS child
allocates/fills its own16KiB block and checks parent shadow/history canaries.

## Validation and remaining scope

`standalone/check_terminal_transfer_live.py` executes actual linked owner,
native receiver, C storage, UI and UART ISR instructions. Only hardware,
BIOS and DOS filesystem syscalls are modeled. It covers binary block receipt,
installation-before-ACK, bounded stalls/wrap, early cancellation, storage
faults and ownership/ABI guards.

The independent actual DOS peer uses the real Alt-R prompt, IRQ/UART path and
DOS files. Run against an explicitly frozen build:

```sh
./tools/dev --command python3 standalone/test_terminal_transfer_dos.py \
  --sha256 SHA256_OF_TERMINAL_EXE --label my-owned-run
```

Retained tests cover CRC/checksum128/1024, mixed blocks, duplicates, bad CRC and
sequence retries, peer/local cancellation, existing destinations, SOFT rejection,
no-peer timeout, exact file bytes, post-transfer parser/keyboard/video use and
sampled hardware restoration. Check each result's executable hash and scope.
Initial harness failures are retained separately from corrected runs.

These peers are synthetic and local. They do not establish physical Wi-Fi modem
compatibility or file transfer against the BBS packages. Ordinary uploads now use the native sender and checked read-only source
ownership; see [LIVE_UPLOAD.md](LIVE_UPLOAD.md). Batch/window/streaming and other
protocol families, full transfer UI/settings, additional
emulations and physical DOS hardware remain part of the full application goal.
BBS navigation/editor results are recorded separately in `lab/bbs/README.md`.
