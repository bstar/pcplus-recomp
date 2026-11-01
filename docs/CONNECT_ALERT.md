# Original successful-connect speaker alert

The successful-connect alert is now implemented in the sound-enabled controller.
Previously it entered the connected state, captured DCD, recorded the call and
restored the status notice without starting a speaker sequence. Existing
PROGRAM notice sound support was a separate event.

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

The implementation uses the existing maintained speaker owner, with no DOS,
keyboard read, UART access or calibrated busy wait in the sequencer. Native
far entries preserve registers, flags and DS=SS. Each pair uses two 880-Hz,
three-BIOS-tick tones with two ticks between them and seven ticks between pairs.
The saved countdown determines the interval; expiry finishes the current pair.
That approximates the native cadence without depending on CPU calibration.

Any key cancels the alert while retaining that key for normal dispatch or BBS
transmission. Hangup, confirmed carrier loss, program/transfer handoff, disabled
sound, invalid time and exit release only its own speaker claim. An already
active speaker is not stolen or silenced. Failed calls do not start the alert.
The saved duration is imported at startup and refreshed by accepted setup reload;
the existing sound field controls both notices and the connect alert.

Physical audible output remains unverified until the updated executable is put
on the DOS card and exercised. This is PC speaker audio, separate from analog
handshake audio.

[Validation receipt](validation/connect-alert.json): 23 linked timing/ownership
cases; four actual DOS8086 cases for quiet mode, expiry, key cancellation and
ASPECT handoff; COM3/IRQ5 package execution with the BIOS entry omitted; the
20-case carrier qualification regression; and 2,012 public-source inputs
reproducing all five executables and ten package files exactly. The passive DOS
observer sees 14 tone starts/42 sounding ticks for its five-second fixture,
with the BBS banner visible during sound, and quiet gates after exit. The key
case has fewer tones and transmits its key exactly once. These are hardware-port
and video observations with the emulator mixer muted, not an acoustic test.

The ready archive is `build/connection-test-package-alert-01/PCPLUS-UPD.zip`,
containing application files under `PCPLUS/` with launchers adjusted for
`C:\PCPLUS`. It includes no private configuration. Keep the existing resources
that match `C:\UTILS\PCPLUS` when applying the update. The executable also
contains the preceding BIOS-omitted UART and carrier-qualification fixes.
