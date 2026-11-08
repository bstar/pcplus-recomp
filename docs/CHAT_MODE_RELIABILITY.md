# Current Chat-mode reliability checks

The complete current17-file candidate passes BUSY cleanup, three calls in one
DOS process, five-minute paced receive, Enigma cancel/retry and live-source
startup through carrier loss/redial. The
[validation record](validation/chat-mode-reliability.json) binds these results to
the exact [package](CHAT_MODE_PACKAGE.md) and [BBS checkpoint](CHAT_MODE_BBS.md).
This establishes selected software admission for a controlled hardware test;
the physical installation and selected deployment remain unchanged.

## Connection and sustained receive

Actual DOS8086 COM3/IRQ5 cases cover BUSY followed by bounded exit, BUSY followed
by successful explicit redial, and three calls separated by local hangups in one
parent process. Initialization/dial pairs, CPR/DA responses and the distinct
one/two/three keyboard inputs are checked, along with settings, executable bytes,
normal DOS return and UART/PIC/vector restoration. The peer is a synthetic Hayes
modem, not a reproduction of the physical lockup.

The endurance run schedules601 ANSI frames over300 seconds. The native process
runs319.533 seconds. Every cursor response arrives in order; complete scheduled
bytes and final glyph/attribute cells match. Opening/closing the command window
and subsequent keyboard input do not interrupt the sequence. BOTH flow is selected.
This is paced receive endurance, not saturation throughput or physical CTS timing.

## Cancellation and carrier recovery

The Enigma cancellation test runs the actual DOS8086 parent through the actual
SynthModem Telnet proxy and owned stock BBS. It observes an exact4096-byte source
prefix on disk before BIOS Escape, validates the cancellation wire, requires an
empty receive area before retry and finishes with the exact65539-byte binary.
There is one authenticated session and one DOS process, with two server helper
executions. An independent raw-capture audit passes. Controls accept the original
and reject eight partial/hash/timing/staging/key/geometry/hardware/session/payload
counterexamples, with explicitly named mutations in the receipt.

The carrier test uses DOSBox's actual virtual modem/DCD behavior, the actual
SynthModem Telnet proxy and stock Enigma in an explicit386/XMS/noEMS/UMB layout.
The bootstrapASX is absent initially; the attached ASPECT interpreter invokes the
matching source DOS compiler while the full parent is present. Its generatedASX
matches exactly. The first authenticated session loses carrier after a4096-byte
partial file. Staging clears before the second login. The same parent redials,
authenticates again and receives all65539 bytes, with complete ZMODEM CRC/offset/
finish validation and subsequent BBS menu interaction. Normal BBS exit, bridge-only
QUIT, DOS return, synthetic configuration and directory accounting and hardware restoration pass.
The established150000ms transfer window is retained.

The independent carrier audit verifies raw proxy/Telnet bytes, modem/DCD history,
notice capture, both authentications, disk-prefix timing, staging cleanup and exact
retry. Its controls accept the original and reject15 source-count, timing/hash,
staging, notice, geometry, hardware, compiler, connection, binary payload,
live-source and CPU-claim counterexamples. No post is saved.

## Excluded diagnostic run and limits

The first carrier invocation added an optional20962-byte witness in conventional
memory that was absent from the previously passing profile. That run did not
publish the startupASX or complete login/retry, although normal DOS return and
hardware restoration passed. Its files are retained and excluded from admission.
The exact DOS error at its failed startup boundary was not captured.

The ordinary-profile repeat removes only that extra witness. It publishes the
exact runtime-compiledASX, logs in and completes all recovery checks. No application
bytes, capacities, modem settings, transfer window or compiler/interpreter limits
are reduced to obtain the pass. This is evidence of observer sensitivity in a
narrow memory budget; it does not establish compatibility with arbitrary additional
resident utilities or diagnose an exact error code for the excluded run.

All these tests are on owned software fixtures. SIP/DSP/audio, physical CTS/DCD,
the actual Boca/SPA2102 path, other machine/video/profile combinations and full
original ASPECT/emulation/protocol/Host parity remain separate requirements.
