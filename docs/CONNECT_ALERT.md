# Original successful-connect speaker alert

The successful-connect alert is missing from the reconstructed controller.
`connection.asm` enters the connected state, captures DCD, records the call and
restores the status notice, but does not start a speaker sequence. Existing
PROGRAM notice sound support does not implement this separate event.

REA/Ghidra inspection of genuine PCPlus2.01 (SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`)
confirms the original dial-attempt success path at overlay5:EAE1 calls
resident CS:3616. The retained overlay assembly identifies the call at EAE1.
An initialized-memory read at linear `0x13616` is bound by Evidence
`ev_6a07f811803fd1063ba467189d1e429b3a95a795775b4ec69fbc2b97075e5069`.

That routine loads a countdown from DS:1D42 (PRM offset 01BE) and checks
the sound-enable word at DS:1D40 (PRM offset 01BC). Each enabled cycle requests
two 880-Hz tones, each with native duration argument15, separated by calls to
the native BIOS-tick wait at CS:6B98 (arguments1 and6, which wait for2 and7 tick
changes). The countdown decreases on an observed change of the DOS seconds
value, not once per pair. It also checks keyboard input and can end early.
The frequency/duration arguments are static facts; exact acoustic
timing depends on the original calibrated routines and was not measured here.

The local original-profile copies inspected have sound enabled and countdown5:
approximately a five-second alert, not a fixed five pairs. Those files do not hash
identically to the active `C:\UTILS\PCPLUS` profile, so this does not establish
the current card's countdown. Preserve and read the active field at the next
card access instead of imposing a guessed value.

Implementation remains open. Use the saved sound flag and countdown, a maintained
nonblocking speaker owner, UART/keyboard service between phases, cancellation,
and cleanup on hangup/exit. Validate one event per successful connection and
no alert for failed calls; do not block BBS input or reuse the unsafe calibrated
busy wait. This is PC speaker audio, separate from analog handshake audio.
