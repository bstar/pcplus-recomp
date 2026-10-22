# Wait for the bottom filter before recorder readiness

Marker placement alone did not complete the normal audio workflow. The
[stopped attempt](validation/recording-marker-layout-stopped.json) reached Files
and SCRIPT.OK but produced no recorder navigation. The owned emulator was
deliberately aborted for diagnosis. Its private helper remained phase0 with no
recipe keys or BIOS queue retries, and15 initial-dwell ticks still pending.
This is not an accidental application crash or a normal cleanup/audio result.
Extracted temporary cores were deleted. Packed-screen candidates were not
identified through a resolved VGA-storage symbol and do not prove screen state.

The first added completion condition incorrectly used a raw ANSI footer suffix.
[That failed TCP attempt](validation/recording-footer-ANSI-control-failure.json)
is preserved. Connected display handling sends parser continuation bytes directly
through the parent renderer; WAITFOR sees display leads, not the full raw ANSI
stream. See [receive policy](ASPECT_RECEIVE.md). Raw capture presence alone does
not make an ANSI pattern suitable for this interface.

The recording fixture now waits for plain `By Date Added` after the early File
Base title, then performs its existing quiet wait and local readiness MESSAGE.
The bottom filter label follows the page body, while the case-insensitive early
title can match the heading before that body has finished. The same source-owned
completion label is used by audio and TCP controls. This is specific to the
owned lab's current filter/theme; it is not a universal BBS completion marker.

[Eight component cases](validation/recording-footer-boundary.json) execute the
actual parent IRQ/parser to obtain leads, then the native WAITFOR/string/caret
instructions at the explicit boundary. The rejected ANSI suffix matches raw
bytes and fails on leads; plain footer text matches both. Hardware/time callbacks
are modeled. A fresh connected DOS/TCP control passes all13 recording, compiler,
replay, manual Search and hardware/timer checks.

The ordinary helper binary, initial dwell, final-screen stability and key pacing
are unchanged. Application executables retain their admitted identities. The new
normal run now [passes full selected-route acceptance](validation/recording-footer-audio.json):
26 producer,34 independent and12 serial checks, with77 independently waveform-
decoded online bytes, actual ASP DOS compilation/replay, manual Search and normal
hardware/timer/SIP/VM cleanup. Its [sealed preparation](validation/recording-footer-audio-preparation.json)
remains separate. This accepts one software V22/1200 route; no diagnostic or
stopped run, physical Boca/SPA2102,14.4 negotiation or full application acceptance
is implied.
