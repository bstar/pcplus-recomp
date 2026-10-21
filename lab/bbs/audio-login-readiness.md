# Audio login readiness and bounded probe exit

The previous audio editor03 server reached Main Menu while its DOS script
eventually wrote FAIL-MAIN. That failed prerequisite and its nine extra guest
bytes remain retained. There was no guest PCM/timing capture, so their causal
relationship is not established.

An independent actual DOS test now reproduces a readiness race mechanism. Its
peer waits for READY before sending PAUSE. Native WHEN stages an art-handler
call; the handler emits HANDLER and executes WAITQUIET. Only then does the peer
send Main Menu. Checking the earlier WAITFOR result misses that title because
the callback's WAITQUIET consumed it. An active WHEN latch records the same
incoming title. This uses the actual source-built ASPECT child, UART parent,
compiler and DOS BIOS services; the peer does not interpret ASX or replace the
receive engine.

The [readiness receipt](../../docs/validation/synthmodem-audio-login-readiness.json)
contains three cases with24 checks:

- MISSED proves the control misses readiness and transmits MISSED as predicted.
- LATCHED receives the same phased input and transmits SEEN.
- REUSED occupies all three native slots, retires a one-shot handler, arms the
  readiness latch in that same slot, and also transmits SEEN.

All cases verify exact UART output, zero returned unread data, actual ASIO
handback, IRQ/PIC/guard restoration, normal DOS return and peer delivery. The
first retained attempt mistakenly used unsupported ordinary slot3 and failed
before input. It is an invalid probe prerequisite, not a product compatibility
finding. Native ordinary slots remain0,1,2; the runtime was not expanded.

The generated audio login script now retains its three original pause, cancel
and newscan handlers. Once either one-shot cancel/newscan handler is retired,
its freed slot watches the existing Main Menu literal and sets a persistent
main_seen flag. The original short WAITFOR loop remains active as well. Final
cleanup disarms all three slots. The existing main-menu marker, authoritative
BBS menu sequence, actual editor entry and every editor/byte gate remain required.
No server code, theme, artwork or recovered ASPECT semantics change.

This mechanism test does not prove the exact cause of editor03, nor that the
new complete audio/editor route passes. Those require their own captures.

The separate [linked display replay](../../docs/validation/synthmodem-audio-display-replay.json)
consumes all35360 bytes of editor03's recorded caller display with no unsupported
CSI stop or remaining UART bytes. It executes the actual linked UART/receive,
CSI and video instructions, modeling only hardware boundaries. The first replay
exposed an omitted BIOS INT10/AH01 cursor-shape service in the checker; that
failed attempt and checker are retained. Adding that BIOS boundary stores the
shape word in the modeled BIOS data area. No product service is replaced.
The final replay excludes an unsupported CSI stop in this explicit environment;
it does not reproduce actual DOS callback timing, live UART load or the original
screen state, and does not alone prove why the live script missed readiness.

## Failed prerequisite exit

The test-only BIOS keyboard helper previously waited indefinitely for KEYTEST,
even after the script had already failed. Its new12600-tick watchdog injects
the actual BIOS Alt-X key before the outer720-second process deadline. It then
restores its original INT1C vector. This uses the product's ordinary exit path,
so failed probes can still collect a screen and UART restoration evidence.
It writes no pass marker, game/script state or synthetic serial response.

The separate [watchdog receipt](../../docs/validation/synthmodem-audio-editor-watchdog.json)
tests the same helper with a36-tick deadline and no KEYTEST screen. An actual DOS
BIOS key reader receives exactly2D00; the timer vector restores and DOS returns
normally. The regular editor recipe and its three-second key spacing remain
unchanged. A watchdog exit cannot satisfy script completion, actual key recipe,
editor entry, cursor/mode behavior or unsaved-text checks.

```sh
./tools/dev --command python3 lab/bbs/check_audio_login_readiness.py \
  --output build/bbs-lab/audio-login-readiness-new
./tools/modem-dev --command python3 lab/bbs/check_audio_editor_watchdog.py \
  --output build/bbs-lab/audio-editor-watchdog-new
```

Use fresh directories. These scoped harness checks close no whole-application
or physical modem gate.
