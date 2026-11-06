# Composed Chat and Help connection package

The tested Chat/Redisplay/global Help parent now has a complete public
installation package, including its required overlay and Help companion.
The [recipe](../standalone/chat_help_connection_candidate_recipe.json) pins
all13 payload hashes and the deterministic ZIP. Build with a new output path:

```sh
./tools/build-connection-candidate \
  --recipe standalone/chat_help_connection_candidate_recipe.json \
  --output-dir build/my-chat-help-package
```

The archive is `archive/PCPLUSSE.ZIP` under that output. It contains `PCPLUS/`
with TERMINAL, ASPECT, ASPCOMP, PRMEDIT, XLTEDIT, PCCHAT.OVL, PCHELP.RTE,
authored PCPLUS.HLP and LOCHELP.HLP, START/SETUP launchers, README and VERSION.
No private settings, dialing files, key maps, translation data or PCPLUS.FON
call history is included. Keep the runtime companions beside TERMINAL.EXE.

The source parent isfab5ac9e, Chat6845e2c8, PCHELPf163169f and authored
PCPLUS.HLP45c6cdba, matching the [geometry/compatibility checkpoint](CHAT_HELP_GEOMETRY.md).
ASPECTcbdee194 uses the matching snapshot lease and deferred script buffers;
the package builder rejects a mismatched parent/interpreter lease. Existing
compiler/setup/translation executables retain their preceding hashes.

## Acceptance

The [release receipt](validation/chat-help-release.json) binds the complete
package, matching source/BBS evidence and actual DOS launcher tests. A clean
2413-file public export with no originals, private files, previous objects or
Git metadata rebuilds every payload byte and the319007-byte ZIP. Its SHA256 is
`28a5bee7f00b06c2685465e17fa14ad8caed1fb19494fc208dac34a9d848de24`.
The preceding ten-file packed-UI recipe still produces its exact earlier ZIP.

Four DOS8086 package workflows pass on COM3/IRQ5:

- START captures the original magenta splash with the LoC SPECIAL EDITION note.
- SETUP returns while preserving environment and synthetic private settings.
- DOS compilation followed by START executes the exact compiled script even
  when the BIOS omits COM3; final UART/PIC/vector state is restored.
- START enters Chat, retains `AB` through actual PCHELP context3, restores the
  complete frame and cursor, and exits cleanly with COM3 absent from the BIOS.

All13 staged files remain unchanged. The first Chat test wrote its observer
capture relative to the application directory while the checker expected C:
root; that frame showed correct return, but the missing-path check rejected.
The observer now uses an explicit root path and the complete test was repeated.

The package tests use dummy UARTs. Actual SynthModem-proxy Enigma editor,
carrier-loss/redial/binary retry and Synchronet evidence is linked through exact
product identity, rather than claimed as a new ZIP-launched BBS session.
Physical Boca/SPA2102 flow/SIP/audio acceptance and the remaining original
feature inventory stay open. Building alone neither selects nor installs it;
the private deployment journal and independent readback determine installation.
