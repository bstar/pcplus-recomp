# Original Chat controller recovery

The original Alt-O dispatch table at DS44E0 selects resident BAC3, a PLINK
trampoline to overlay15:E828. The recovered controller E828..EAF2 and duplex
log/history helper EAF2..EB20 total760 bytes. Flat assembly matches the genuine
2.01 file at108424..109184 exactly; relocatable OMF assembly also succeeds.
Ordinary assembly reads authored source and the recorded region digest only.

REA verified the controller and helper in the existing loader-derived overlay
analysis image, SHA256 `4ae6ee164991ab772dcb0dba4974fe30d00ee97429719dbbe0b56d5756fbc868`.
This image is never executed. Its pointers/calls retain the analysis-image
limitations; original file and overlay manifest bytes independently establish
the region identity. The genuine original SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.

REA assembly Evidence:

- Controller: `ev_a1102a9ca1c8cd961517e2dcad8fe603db710c271e68720d8d8b574b349ebe0a`.
- Echo helper: `ev_1ecfcddbd56817869467b7c15da370d82800ca9c2a034331e7663df7b7188761`.
- Logger09B6, history5832 and transmitterAB0B were inspected separately; their
  existing recovered behavior remains the integration boundary. Complete
  session records stay in ignored `analysis/chat-overlay15-20261106.rea.json`.

## Observed contract

The controller separates REMOTE and LOCAL areas and an Escape-to-end footer.
It chooses packed remote/local positions1200/1400 when DS7A74 is at most28,
and2000/2200 above28. Rendering, cursor movement, screen setup and help remain
explicit service calls; this is not a screenshot-equivalence claim.

Received bytes use the DS:D00A translation table; translated NUL is suppressed.
Other received bytes reach the render, history and logger services. Ordinary
local keys render in the local area. DS1D76 selects immediate transmission or
buffered input. Immediate keys use AB0B; duplex DS1D1A additionally selects log
and history handling. Ctrl-Q/Ctrl-S bypass line buffering and transmit directly.

Buffered input uses298 bytes of a306-byte stack region before flushing.
Backspace0E08 removes a buffered byte and clamps at the start. Enter000D and
E00D submit the accumulated NUL-terminated line through0A62. An LF is additionally
sent when DS3986 or duplex is nonzero. Escape exits without flushing an unfinished
line. Alt1..Alt0 select ten54-byte KEY records starting3758 through the existing
48CC action service;6D00 invokes the Redisplay service sequence. The earlier
Help label was incorrect; see the [static correction](CHAT_REDISPLAY_ENTRY.md).

The echo helper does not transmit. It walks a NUL-terminated string only when
duplex is nonzero, promotes each signed byte with CBW and calls the actual logger
and history interfaces. Logger uses caller cleanup; history uses RET2. Native
BP/SI/DI and DS=SS are preserved in the component checks. The helper has no string
length parameter, and the original transmitter has blocking waits; these are
native observations, not recommendations for the maintained application.

## Checks and next integration

`standalone/check_chat_native.py` executes the recovered instructions in a16-bit
CPU with declared keyboard, UI, translated receive ring, TX, logging and history
boundaries. Its1089 cases cover all255 nonzero byte values under four duplex
values, empty strings, both send modes, five row counts, LF/duplex combinations,
298-byte boundaries and repeated flushes, backspace, both Enter codes, flow keys,
ten KEY records, help return and translated receive bytes. Stack cleanup and
preserved register/data ownership are checked on each return. These are modeled
callees; no DOS, real UART, complete callee or physical acceptance is claimed.

The same cases pass with optional exact original comparison and from a separate
three-file source export containing only assembly, provenance and the checker.
The [receipt](validation/chat-native.json) binds both results.

The [serviced send owner](CHAT_SERVICED_OWNER.md) now preserves those native
keyboard/effect branches with bounded sink work, caller-owned far storage and
actual DOS near/far-bank checks. It is not yet bound into the application.

Next integrate Chat as a serviced foreground owner with checked bank interfaces:
defer entry under parser/macro/child/transfer ownership, keep UART RX/TX and flow
control running, maintain separate pane state and bounded input, preserve local
shortcut semantics, and define disconnect/notices/exit restoration. Verify those
against actual DOS observations and isolated Enigma/Synchronet workflows. Segment
pressure must be addressed without reducing existing stacks or capacities.
Alt-O remains unavailable in the selected application. No package, selector,
physical file or production bridge changes in this recovery checkpoint.

```sh
./tools/dev --command python standalone/check_chat_native.py --output build/NEW-chat
```
