# Matched ALARM connection package

The optional ALARM profile now has a complete, matched software package. It
includes the native-error cleanup fix, the current source compiler, Chat and
Help companions, and the original magenta splash with the special-edition
annotation. Fresh Enigma and Synchronet regressions pass on these exact bytes.
Physical acceptance and the remaining original-feature inventory are still open.

The [validation record](validation/alarm-connection-release.json) binds 2,546
source files and 200 receipts/captures. It records software acceptance only:
at the time of that receipt, the package was staged without selection or
installation. A subsequent verified deployment installed this package; all
13 application files matched independent readback, and eight existing private
files remained unchanged. Physical runtime acceptance is still pending.
Deployment journals and machine details remain private.

## Reproduce the package

```sh
./tools/dev --command python standalone/build_connection_candidate.py \
  --recipe standalone/alarm_connection_candidate_recipe.json \
  --output-dir build/alarm-connection-candidate-20261106
```

The explicit recipe selects both parent capability 19 and the optional ALARM
interpreter. Packaging checks the capability published by the actual parent
executable against the interpreter profile. The ordinary recipe is unchanged.

| Product | SHA-256 |
| --- | --- |
| TERMINAL.EXE | `689bdce91c267320b4aad9136a530ab8ce90f733f4a540197e53e6ce4074df06` |
| ASPECT.EXE | `b4f0aecc7a6538920711c2fa866324d2ddad856883a437cbb2f125cd0e26efbe` |
| ASPCOMP.EXE | `c26199a3191ce70097cfbdcf1050d049d01be0ce5fd66ad172004b9c924137a4` |
| PCPLUSSE.ZIP | `4bb269bc9889d8f0884e41a8f6a5ec3c0f6e558e8b7a37e16e965cf719240f18` |

Application source is checkpoint `39c9fcf`; package tooling is `2906b24`.
A fresh export of 2,471 public source files, without original binaries, prior
objects, private configuration or Git ancestry, reproduces all five executables,
all 13 payload files and the complete archive byte for byte. The parent launch
minimum is 479,680 bytes including PSP; the interpreter minimum is 131,168.
Those launch minima do not establish peak hardware memory requirements.

## Observed software behavior

Four DOS 8086 package workflows pass: splash, setup, Chat/Help, and precompiled
script execution. Chat and script cases also exercise BIOS-unlisted COM3/IRQ5.
The packaged script executes DATE, TIME and ALARM 0. All workflows preserve
six synthetic private-file types byte for byte: PRM, DIR, KEY, KBD, XLT and FON.
PCPLUS.FON is call history. No such files are shipped in the public payload.

Synchronet passes all 25 checks, including ASPECT login, editor interaction and
an exact 4,000-byte display/cursor restoration after an external viewer, followed
by further editing. Enigma passes scripted logins, carrier loss and redial,
retained partial transfer and an independently audited exact 65,539-byte retry.
These use isolated stock servers through the staged SynthModem Telnet path;
they do not test the physical adapter, analog audio or modem DSP backend.

The [ALARM cleanup evidence](ASPECT_ALARM_UNWIND.md) separately covers native
transmit errors, speaker/duration retirement, subsequent VM reuse and both
held-stream/nested-child capacity profiles. Its full application cold rebuild
and this complete-package proof have different export scopes and counts.

## Remaining acceptance

Preserve the actual machine's configuration and evolving call history when
installing. Confirm package identity after readback, then test the physical
Boca → SPA2102 → SynthModem → Enigma route, including rendering, editing,
flow control, reconnects and file transfers. Software dummy-UART tests cannot
establish physical RTS/CTS, audio timing or hardware stability. The remaining
ASPECT, other-emulation/protocol and Host inventory remains explicit in
[FEATURES.md](FEATURES.md); this checkpoint does not establish full parity.
