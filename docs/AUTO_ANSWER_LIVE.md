# Guarded Auto Answer integration

The experimental `--auto-answer` candidate enables Alt-Y, the original reference
entry and browser search. It sends the saved answer-on field through the shared
bounded command owner, displays `AUTO ANSWER...` and requests the configured
information sound. It is not a toggle or an acknowledged initialization/dial
operation. Source-only executable SHA256:
`d9eae89d8bdfa5156b5d50e31e542bbe0c1851bc10a4b03d9fc826954ec84b03`.

The flag includes manual Init and the typed answer owner. It requires the sound
owner and reserved status row. Admission supports BIOS80x25 color text modes2/3,
page0, with80x24 terminal cells. Other geometry refuses before command/notice/
sound effects. Existing parser/view/PROGRAM/transfer/recording/Break and other
owner guards defer admission; queued ordinary output drains first. Both menu
routes release their old view before executing the command.

## Behavior and ownership

The25-byte configured answer-on field is validated and privately expanded before
the notice/tone is started. The original answer-off field is not selected and
configuration is never rewritten. Incoming ordinary replies and ANSI/CPR remain
on their usual paths. Command bytes own ordinary UART output; typed keys wait
in the existing FIFO. Repeated Alt-Y/Alt-J during sending is consumed. Escape
cancels locally; Alt-H/Alt-X, qualified DCD loss, programmatic connection actions
and shutdown use the existing typed cleanup and partial-line retry handoff.

The live duplex WORD is captured on begin; ordinary bytes echo through the native
renderer only after physical acceptance, once. Pause and FF/NUL do not echo.
Captured duplex/post-acceptance echo and the existing BIOS pacing remain
explicit maintained differences from the original per-byte/pre-write echo and
50 calibrated pacing units. The [typed owner](AUTO_ANSWER_OWNER.md) documents
renderer reentrancy and caller/state preservation separately.

Configured sound zero is quiet; any nonzero value requests440Hz for four BIOS
ticks with a bounded poll count. The owner polls without waiting or reading
keyboard/UART. It records speaker generation, never steals busy hardware and
never silences a replacement tone. Mute/cancel/loss/exit stop only its own tone.
A normal empty command still requests the notice and complete short tone.
Sound timing is maintained, not a claim of original tone-duration equivalence.

The notice uses the existing status-row save/restore service. Its reserved row
stays outside terminal addressing/scrolling; the existing status refresh updates
the underlay while the notice is visible. Completion/cancellation restores that
row without overwriting incoming terminal-body cells. Carrier-loss cleanup
releases Auto Answer's notice before the normal carrier-loss notice is drawn.
Normal retirement also restores the notice in the serial service before deferred
keys run, so it cannot later clear a newer command's notice. A dedicated
completion-boundary regression checks this ordering.

## Validation and limits

The [receipt](validation/auto-answer-live.json) binds27 linked UI/command inputs:
direct/reference/browser, quiet/nonzero sound/echo, normal RX/CPR/typeahead and
new body text, cancel/hangup/exit/loss/redial, flow stalls, empty/invalid commands,
foreign/replacement speaker generations, live mute, owner deferral and unsupported
video. It also binds272 typed-owner,117 Init,31 dispatcher,22 elapsed-window and23
connect-alert regressions, all39 reference labels with13 unavailable entries,
and an exact Git-free source-only rebuild. The disabled feature reproduces
8f76cc4f. Near data/stack65024 (512 spare), resident CS65240 (296 spare); the
checker validates all six speaker calls use the correct CONFIG near-cdecl ABI.

Two actual DOS8086 COM3/3E8h/IRQ5 synthetic-Hayes workflows pass direct quiet and
reference-menu echo+sound. They retain exact answer-on bytes, no extra dial,
typeahead, incoming text/real CPR, notice cleanup, unchanged PRM and restored
UART/PIC/vector state. The echo case uses **Alt-E** to set live duplex: the
existing partial PRM importer does not adopt the saved duplex field. That is a
remaining configuration-parity gap; these results do not imply it was fixed.

Initial checks caught an incorrect far call to the internal near speaker API;
the corrected code and static near-call checks prevent that stack mismatch.
The connect-alert harness now models DOS date/time used by full call-clock
candidates. Its actual speaker/controller routines remain executed. Failed
intermediate artifacts stay ignored and do not support acceptance claims.

These CPU checks model BIOS/DOS/ports; the DOS workflows use a synthetic serial
modem. BBS screen/cursor, package/START/SETUP and physical gates need their own
scoped evidence. No original pixel/calibrated timing, full feature parity or
analog/SIP acceptance is claimed. No installed/private files, card or live
bridge/BBS service has changed. The previous hardware-test package and active
selection remain unchanged pending a separately verified package/deployment.

```sh
./tools/dev --command python standalone/check_auto_answer_live.py \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW-answer-live
./tools/dev --command python standalone/test_auto_answer_dos.py \
  --terminal build/SELECTED/TERMINAL.EXE --label new-answer-dos
```
