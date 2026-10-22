# Foreground ASPECT recording

The [current mapped-lead checkpoint](validation/recording-matcher-ui.json)
supersedes the earlier raw-RX tap for normal prompts: recording now follows
input translation and excludes parser continuations, matching native WAITFOR.
The [actual BBS replay failures](BBS_RECORDING.md) remain open; the selected
DOS/linked workflows below do not establish general BBS recorder compatibility.

The source-built terminal now exposes recording through its command menu.
Press **Alt-Z**, select **File**, then use:

| Key | Command | Behavior |
| --- | --- | --- |
| C | Record / save ASPECT script | Start a recording, or save the active recording. |
| D | Cancel ASPECT recording | Confirm before discarding unpublished work. |
| F | Recording status / recovery | Inspect the fixed destination, retained files and error codes. |

Starting asks for a writable DOS 8.3 `.ASP` path; Enter accepts `PCPLUS.ASP`.
An existing destination requires explicit **Y** before replacement is authorized.
The original remains intact while recording. Successful start returns directly
to the terminal. Prompts and accepted user output are recorded; native terminal
query replies are excluded. The generated prompt timeout is 30 seconds.

Choose File/C again to save. A boundary with queued output, an unfinished
parser operation or another serial owner is refused; let the operation finish
and retry. Saving uses the checked publisher, including exclusive scratch
creation, close checks and backup/restoration for replacement. File/D asks Y/N;
N continues recording, while Y discards unpublished work and preserves an
original destination. Exiting the terminal cancels unpublished recording.

Compile the saved source with the maintained DOS compiler:

```dos
ASPCOMP PCPLUS.ASP PCPLUS.ASX
```

File/A (Run script) runs the compiled `.ASX` through the source-built ASPECT
runner. The recorder uses this project's `TRANSMITRAW` extension. Its compiled
output is for the maintained runtime; compatibility with original PCPlus
bytecode runtimes is not established.

## Recovery and ownership

File/F reports the target, owned scratch, original backup, first status, DOS
error, close error and restore error. **U** offers explicitly confirmed cleanup
when retained ownership is eligible. Cleanup preserves the first failure for
diagnosis, even after temporary files are resolved. An uncertain close keeps
its files and claims; cleanup does not retry it. A backup retained after failed
restoration is never discarded here. End the session and inspect the named
files from DOS before recovering an original.

Transfers, automatic download admission, scripts/PROGRAM, setup, translation
reload/edit, monitor, controller, BREAK and modem connection changes cannot
acquire their serial ownership while recording retains claims. The UI checks
queue/parser/owner boundaries at start and save. Existing key dispatch flushes
a held automatic-transfer prefix before the menu key is processed. Independent
capture, screen and printer operations retain their existing canonical file
checks. A recording file error does not recall bytes already sent to the UART.

## Evidence and limits

[The current validation record](validation/recording-matcher-ui.json) binds the keyboard and
mouse build inputs, ten linked recorder UI campaigns, 153 command-menu inputs,
ten TX and ten RX campaigns, 60 PROGRAM inputs, five autostart campaigns,
78 ZMODEM workflows, 623 ABI counterexamples and eleven actual DOS capture
scenarios. Three actual DOS runs cover new/save, confirmed replacement/save,
and confirmed cancellation. New/replacement recordings compile in DOS and
replay exactly the accepted user bytes over an independently observed emulated
UART; query replies are excluded. Replacement preserves the original during
recording; cancellation preserves it afterward. Sampled DOS/UART state restores.
The standalone replay fixture explicitly establishes its required asserted-DTR
baseline. This is a software fixture, not a physical modem result.

The keyboard binary is
`f041eeaaaeff9e38d8169625f499cd1f26ead00695e343d3e8fe36a4d61987c6`;
the mouse binary is
`a65b8d799579daa2dfd1f1281f07a78f4699498b308ec710729dbeab95736c49`.
Near data has 112/64 bytes spare and resident code has 366/216 bytes spare,
respectively. Nine actor guards and three UI boundary calls are verified.
Two compiler/linker optimized same-segment far calls retain the required far
return frame; the remaining call has its checked MZ relocation.

Testing exposed code-segment string pointers losing their segment in conditional
expressions. Explicit branches now preserve the far pointers for the search,
script and recorder status views; the complete command-menu regression passes.
A verifier counterexample also exposed missing validation of the recorder
ownership predicate's segment, which is now checked. Failed receipts are retained
with the accepted evidence rather than presented as passes.
The original UI checkpoint remains [preserved separately](validation/recording-ui.json).
The current standalone DOS replay fixture sends its native query before the
printable prompt; a raw-only runner has no renderer to consume query continuations
after a matcher has completed. Its earlier pending-input close failure is
retained, and this fixture does not accept raw-only replay of arbitrary ANSI
recordings. Normal File/A replay uses the admitted parent renderer.

Acceptance covers selected 80 by 25 keyboard workflows. Mouse runtime workflows,
other geometries, immediate asynchronous file-error notification, complete
original UI/ASPECT language, current-binary modern BBS/audio and physical modem
acceptance remain open. File/F exposes retained asynchronous failures; existing
shutdown error reporting remains in effect. This checkpoint closes no full
F01–F16 application gate.
