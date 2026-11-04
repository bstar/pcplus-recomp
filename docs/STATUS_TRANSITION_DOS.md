# DOS foreground status diagnostic

`--status-probe` is a separate startup diagnostic for the internal status owner.
After normal configuration, UART acquisition and reset capture, it enables the
receiver, calls the probe in the real foreground, and exits through ordinary
hardware shutdown. It never starts dialing or adds a command binding. Application
packaging explicitly refuses its diagnostic manifest.

The [receipt](validation/status-transition-dos.json) binds the diagnostic467d45d6,
ordinary component3756c6d7, disabled7df99c1f, object identity and runtime evidence.
All three reproduce exactly from declared sources in empty Git-free trees.
381 ordinary object files match byte for byte in the diagnostic build; the only
unmatched ordinary object is `src/terminal/main.asm`, which contains the guarded
startup call. The diagnostic adds its own C/ASM observer and exclusive DOS writer.
The transaction implementation itself is not replaced or modified for the run.

## Actual DOS observations

DOSBox-X executes the8086 build using COM3/3E8h/IRQ5,19200baud,8N1 and the real
virtual UART interrupt path. A loopback peer waits for closed diagnostic state
files, then sends ANSI cursor/save/wrap sequences. The diagnostic invokes the
same receiver, connection/monitor/controller/transfer filters and autodetect
services as the main loop. Escape continuations consume the actual UART ring.
No callback, instruction, modem reply or product field is patched by the host.

Six actual44-byte state records and six4000-byte video dumps establish:

1. Initial24-row state with independent per-row video patterns.
2. Hiding status exposes row25, preserves the first24 rows and initializes the
   new row with the configured status attribute; captured reset rows become25.
3. Received ANSI moves/saves the cursor on row25. Showing status invokes real
   scrolling, clamps to row24/column8 (zero-based23,7), and produces video offset
   3694 and attribute offset1847. Actual BIOS cursor agrees.
4. Actual RIS consumes the updated24-row defaults and clears/homes the content.
5. A received last-column character leaves a pending wrap; hiding preserves it,
   and the subsequent received X wraps to the next row.
6. The complementary nonscrolling show preserves another pending wrap; received
   Y wraps correctly, with24-row geometry and restored status text.

The peer completes five ordered delivery stages and sees no outgoing modem
commands or other bytes. Ordinary shutdown restores the independently sampled
42-byte IRQ-vector/UART/PIC state. The synthetic PRM and diagnostic executable
remain unchanged. Existing output files cause exclusive diagnostic creation to
fail rather than overwrite them.

The first attempted wrapper supplied one escape byte at a time directly to a
synchronous decoder, without queued continuations. A second wrapper serviced
TX/keyboard but omitted the main loop's inline receive sequence. Both were
rejected by the runtime checks. The accepted diagnostic uses real serial input
and the complete production receive/filter service sequence. These were harness
corrections, not changes to the status transaction.

## Scope and identity

The diagnostic is467d45d6, resident code65462 bytes (74 spare), CONFIG_CODE59665.
It is not a distributable replacement application. The ordinary internal owner
remains exactly3756c6d7; the option-disabled executable remains exactly the
software-accepted7df99c1f package. Neither active installation selection nor the
physical DOS machine was updated.

This adds actual DOS/virtual-UART evidence for the named successful offline
transactions. Owner/refusal/failure-rollback cases still have their separate
[linked CPU evidence](STATUS_TRANSITION_OWNER.md). It establishes no modem
carrier, SynthModem/Telnet BBS, SIP/DSP/analog, physical throughput or full mode
acceptance for the new transaction. Online size policy, actual command bindings,
other modes and physical acceptance remain open.

```sh
./tools/dev --command python standalone/test_status_transition_dos.py \
  --terminal build/DIAGNOSTIC/TERMINAL.EXE --output build/NEW-dos-probe
```
