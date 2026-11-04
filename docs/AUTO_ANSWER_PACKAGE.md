# Auto Answer package and BBS regressions

Candidate d9eae89d, built from source commitc3edf02, is staged separately at
`build/connection-auto-answer-retired-20261103/PCPLUSSE`. Its ten public files
contain no private settings/directory/key files or call history. The archive
`pcplus-auto-answer-test.zip` is262071 bytes, SHA256
`4950ab9964e2666f0a434d2edf0490ce79b73fff0a90c45a23f17d754731fb81`.
The separate pointer `build/auto-answer-current-candidate.json` identifies it
without replacing the active installation selection.

The [receipt](validation/auto-answer-package.json) binds:

- Exact reproduction of all five executables and ten files from2055 committed
  public sources in an empty export with ancestor Git unavailable. ASPECT remains
  byte-identical84160498; compiler/setup/translation identities also remain.
- Four actual DOS8086 COM3/3E8h/IRQ5 package workflows: START with precompiled
  ASX, SETUP/cancel/return, splash-only START and START with the BIOS COM3 entry
  omitted. Existing environment, UART/PIC/vector, synthetic private-file and
  packaged-binary preservation checks remain active.
- Actual owned Enigma multiline page-up/edit/discard and Synchronet ASPECT
  login/editor/abort sessions through the installed SynthModem TelnetProxy.
  Both use the established250ms escape framing/20ms per-byte input delivery.
  Call-log checks pass. Independent full24-row cell/cursor audits find zero
  differing cells:87171 delivered Enigma bytes/cursor22,14 and23079 Synchronet
  bytes/cursor5,8. The oracle retains its documented default-font projection.
- Four actual DOS virtual-DCD transfer regressions pass: receive negotiation/
  partial payload and upload unacknowledged/partial frame. The DOSBox modem
  supplies carrier transitions; cleanup, flow, call-log accounting and
  same-process redial retain the existing strict checks.

The BBS sessions exercise ordinary compatibility with the final dispatcher
present. They do not inject AT commands into BBS input. Separate
[Auto Answer DOS checks](AUTO_ANSWER_LIVE.md) exercise quiet direct and
Alt-E-enabled echo/sound reference-menu commands against a synthetic serial
modem. These scopes do not establish every BBS page, original font pixels/
notice appearance/calibrated sound timing, physical flow or analog/SIP/DSP.

The original magenta Special Edition splash and sysop bstar are preserved.
Precompile ASX at the DOS prompt: nested source compilation while retaining
the terminal/interpreter still has the documented conventional-memory limit.
The partial PRM importer still does not adopt saved duplex; Alt-E sets the live
value used by the answer sender. Full configuration/command parity remains open.

No machine/card/private files or live BBS/bridge services have been changed.
Installed9f2a37e7 and active selection93a9db94 remain unchanged. If deploying,
preserve actual C:\PCPLUS launchers and PRM/DIR/KEY/KBD/XLT/FON; staged test
launchers use C:\PCPLUSSE. Reboot out of IRQ5 Network management before Boca
tests. Physical BUSY/reboot, same-process calls, display/input/flow/transfers/
reconnect/audio acceptance remain open, along with13 unavailable reference
commands and the broader full-feature inventory.
