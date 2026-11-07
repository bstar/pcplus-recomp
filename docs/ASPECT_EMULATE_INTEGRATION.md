# EMULATE production bridge and WHEN integration

The optional source-built parent `856a9c85` and interpreter `5c641ac4` now have
additional bridge, deferred-handler and modern-BBS evidence. Application bytes
and installed R59A85A8 remain unchanged. The matched compiler is `ac58a8a1`.
This checkpoint does not select or deploy the optional pair.

## Production bridge

The linked production parent passes 81 cases through its real far bridge, BEGIN
allocation validator, RPC 20 dispatcher and profile owner. Rejected clients/MCBs,
parent redzones, DS/SS mismatch, reentry, owner conflicts, changed PSP/caller,
returned serial handoff, END/re-BEGIN and stale tokens after revoke/reprepare
all exercise actual product instructions. Repairable fixtures successfully retry.

Eight caller FLAGS combinations cover unsupported/nonbyte selectors and actual
VT220/ANSI resets, retaining every checked non-AX register, FLAGS and stack.
There is no IF-enabled DS/SS mismatch. RPC 20 leaves the modeled UART registers,
IRQ/vector, RX/TX bytes, device reads and port writes unchanged. Sampled body
stack use is 20–172 bytes in these selector cases; this is not a global stack
bound. Sampling excludes the CLI-protected intermediate SS/SP transition until
parent DS=SS is installed.

The child caller frames, DOS current PSP/MCB, BIOS, files and UART are modeled.
The unused authored child callback is checked never to execute. No product
instruction is substituted or patched. This is stronger parent composition
coverage than the earlier direct-owner checks, but not a real ASPECT child or
DOS EXEC/IRQ-timing fault proof.

## Actual deferred WHEN

Two actual DOS 386 workflows use ordinary products, a synthetic modem peer and a
passive UMB exit observer. The compiled main registers a native deferred CALL,
then waits for END. The peer sends TRIG/END only after WHENREADY; the worker
performs EMULATE before the main script resumes.

- Success: 31 checks. Two workers switch VT220→ANSI, receive profile-specific
  parser DA replies and transmit completion before main resume. All four script
  exits are clean, with DS=SS and zero checked cleanup/native-owner fields.
- Error: 38 checks. TTY in the first worker produces native error 3/opcode 2F and
  never reaches the following worker/main statement. Three subsequent scripts
  succeed, including a later deferred worker's VT220/ANSI switches, six streams
  and missing-file recovery. All checked owners retire cleanly.

These observe external handler ordering and exit state, not every internal WHEN
slot or native abort/fatal-reset path. The observer changes memory footprint;
these are integration/recovery runs, separate from unobserved capacity proofs.
The specialized harness checks the reset view, rather than retaining the old
banner that EMULATE deliberately clears.

## Modern BBS checks

Stock Synchronet passes 25 editor/connection checks and 12 external-viewer return
checks through the staged SynthModem proxy. The external child leaves graphics
mode; the actual 4000-byte editor frame, cursor shape and subsequent editing
survive. The independent cell audit consumes 22,494 delivered bytes and matches
all 1,920 editor cells and cursor position, with zero differences. Actual NAWS is
80 × 24; the size metadata is consumed locally.

The exact parent/interpreter/compiler also pass 16 Enigma carrier/retry checks.
One actual DOS 8086 parent makes two authenticated script logins, loses carrier
during a partial transfer, removes the staging file and redials. The successful
retry is exactly 65,539 bytes. The independent raw-proxy audit verifies protocol
CRC/finish/control behavior, exact file contents, local size-metadata handling,
cleanup and restored hardware. These loopback tests do not establish physical
SIP, DSP, audio, analog carrier or hardware CTS acceptance.

A separate DOS 8086 normal-terminal Enigma editor workflow passes 9 integration
checks and 12 external-viewer return checks. Its independent reference audit
consumes 48,367 delivered bytes: all 1,920 cells and the cursor match, with zero
differences. The full editor frame survives the graphics child and subsequent
editing. Actual NAWS is 80 × 24. No ASPECT interpreter executes in this editor
fixture; the carrier workflow separately exercises the matched three products.
These are bounded stock-editor snapshots, not every BBS screen or intermediate
frame, the installed LoC theme, or a promise of universal rendering perfection.

The [machine-readable record](validation/aspect-emulate-integration.json) binds
current products, source hashes, independent audits and captured evidence.

## Remaining

Expand native abort/fatal-reset composition and measure sustained receive
service during keyboard import and screen reset. Complete matched capability 20
package/source reproduction before selection, then physical Boca/SPA2102/SynthModem acceptance. Other
emulations/protocols, Host and the wider original feature inventory remain open.
