# Keyboard mapping during connected BBS editing

The Alt-F8 parent and matched source helper now pass edit/save/return inside
authenticated stock Enigma and Synchronet editors. Each test changes only ANSI
F1 to `ZZZ` in an owned full-size KBD, saves, exits the helper and continues the
existing unsaved draft. The local definition never reaches the BBS. Full4000-byte
before/after frames, cursor, shape, mode and row count match; both final editor
screens independently match1920 reference cells and the cursor. Actual DOS EXEC
and application exit status are zero. [The receipt](validation/keymap-bbs.json)
binds the parent, helper, fixtures, captures and test sources.

Enigma uses DOS8086 and a conventional-memory passive observer. Synchronet uses
the existing386/XMS/UMB test setup, with measured upper-memory observer and BIOS
key producer segments. This is an emulator fixture choice, not a new application
CPU requirement or a physical386SX test. A small source COM launcher records the
application's actual DOS status before COMMAND.COM consumes it; separate DOS
cases verify zero, exit42 and missing-executable behavior. The launcher adds a
small retained test allocation; it is not an application package component.

## Serial flow during the helper

The earlier transparent null-modem fixture did not convey RTS, despite selecting
HARD in the terminal. Enigma completed in that fixture, but Synchronet returned
receive-overrun code6 after the helper. Its exact KBD save and frame restoration
already passed. We retain that failure instead of treating a good-looking frame
or the helper's zero exit as a successful application return.

The optional `--hardware-flow-model` uses DOSBox-X's nontransparent null-modem
envelopes: escaped literal FF and separate RTS/DTR/break flags. The loopback
modem holds peer CTS/DSR asserted and pauses single-byte BBS delivery when RTS
drops. It does not infer RTS from a screen, timeout, ANSI sequence or application
memory. The protocol follows upstream
[readChar/setRTSDTR](https://github.com/joncampbell123/dosbox-x/blob/master/src/hardware/serialport/nullmodem.cpp).
813 independent framing cases cover every binary byte across every packet split,
all eight line states and mixed control/data. The default transparent fixture
remains available; eight existing observer/key-producer variants are byte-identical.

In the accepted Synchronet run, RTS drops with DTR held high for8.896 seconds
after the actual KEYTEST subject. The model's delivered count remains23018
throughout that pause, then delivery resumes. The original editor workflow,
draft abort, unchanged message bodies/statistics and exact screen oracle pass.
This distinguishes the transparent-fixture overrun from acceptance with modeled
RTS flow. It does not establish real modem latency, CTS transitions, DCD loss,
FIFO behavior or physical Boca/SPA2102/SIP/audio performance.
The model also changes delivery granularity from32 bytes to one. The subsequent
[matched pacing control](KEYMAP_PACKAGE.md) holds that granularity and framing
fixed: ignoring RTS still exits6, while respecting it passes. This supports the
flow-gating explanation within the model; physical behavior remains unverified.

Failed sessions left synthetic Synchronet draft files, which were preserved in
ignored lab storage before retrying. The extra draft-recovery prompt caused two
later login attempts to miss Subject; those are precondition failures, not mapper
return evidence. No live BBS configuration or SIP/audio service was changed.

```sh
./tools/dev --command python lab/bbs/test_synthmodem_proxy_dos.py \
  --runtime build/menu-size-accepted-20261104/candidate \
  --terminal build/keymap-live-verified-20261107/TERMINAL.EXE \
  --label my-keymap-enigma --framing-ms 250 --byte-delay-ms 20 \
  --size-probe --screen-reference \
  --keymap-helper build/keymap-helper-lowpeak-20261107/PCKEYMAP.EXE
./tools/bbs-dev --command python lab/bbs/test_synchronet_screen_reference_dos.py \
  --runtime build/menu-size-accepted-20261104/candidate \
  --terminal build/keymap-live-verified-20261107/TERMINAL.EXE \
  --runner build/keymap-live-aspect-verified-20261107/ASPECT.EXE \
  --label my-keymap-synchronet --size-probe \
  --keymap-helper build/keymap-helper-lowpeak-20261107/PCKEYMAP.EXE
```

Run the separate size/screen and Synchronet flow audits too. Use new labels and
the owned loopback fixtures; do not substitute private BBS settings. Matched
package admission, selected KBD shape/compatibility, targeted refusal/close-fault
injection and physical acceptance remain open. RA608E10 is still installed;
neither the application bytes nor the selected deployment changed here.
