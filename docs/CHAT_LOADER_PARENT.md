# Resident Chat loader admission

The opt-in `--chat-loader` parent links the checked loader while keeping the
Chat implementation in the separately built `PCCHAT.OVL`. With the reviewed
parent size profile, parent `03a2149b` needs 478,000 minimum module bytes,
32 fewer than the previous `61757956` parent. Near data remains 65,488 bytes;
no stack, history, screen-frame or script capacity is reduced.

This is a loader/admission checkpoint. It does not enable Alt-O, claim shared
snapshot storage or change the selected package or physical installation.
The source manifest explicitly records those missing bindings.

## Build and identity

`src/chat/loader_link.py` builds the source-only MZ module, generates its exact
identity header, and compiles the loader using `-ox -os -oe=0`. It checks the
loader's import set and zero private data before linking its two objects into
`CHAT_LOAD_GROUP`. The parent map must contain the complete bounded loader
bank and must omit the module implementation. The builder copies the separate
module beside the parent and includes all inputs in the parent source manifest.

The loader bank is 1,264 bytes: 1,131 C bytes, five linker-alignment bytes and
128 kernel-wrapper bytes. It is 64 bytes smaller than the earlier 1,328-byte
bank. The module remains exactly `77270fb6`, 3,386 file bytes/3,338 image bytes.
Disabling both new opt-in options retains parent `61757956` exactly.

The exact reviewed flags are the deferred connection recipe's terminal flags
plus `--optimize-size --chat-loader`. Use the pinned `./tools/dev --command`
environment. This does not update the canonical recipe or package selection.

## Validation

The optimized loader passes the full actual DOS8086 overlay fixture: six loads
at two relocation bases with all remaining free paragraphs reserved, unchanged
PSP/JFT/free memory, far callbacks/DS=SS, malformed-file, bounds, lifetime and
loaded-image corruption controls. The composed Chat proxy workflow still
matches 568 complete frames and 1,071 ordered effects against the fresh scoped
native reference, including all 1,024 RX effects while TX is refused.

`check_chat_loader_parent.py` compares parent loader/kernel code, data, symbols
and fixups with those tested objects, plus the exact MZ module and generated
header. Only one Watcom generated-header dependency comment may differ in its
build-directory filename/timestamp; its header contents must match. Every
other OMF record is exact and every record checksum is validated.

The actual parent passes normal DOS8086 six-stream/missing-file recovery with
three child launches. Stock Synchronet's editor, actual graphics-child return,
full frame/cursor and subsequent editing pass through the isolated real
SynthModem Telnet proxy, using the existing 386/UMB observer/helper profile.
A cold 629-file public-source export reproduces parent, module and identity
header exactly without originals, private configuration, prior objects or
ancestor Git.

Enigma also passes with this exact parent: one DOS8086 process, two actual
ASPECT logins, socket interruption after a 4,096-byte source-prefix write,
virtual-modem DCD/carrier loss, empty staging before redial and an exact
65,539-byte retry. The independent raw-capture audit checks CRC/finish/controls,
bridge/logoff return, both authentications and hardware/settings restoration.
The [acceptance receipt](validation/chat-loader-parent.json) binds all seven
reports and the separate unchanged disabled control.

```sh
./tools/dev --command python standalone/test_chat_module_dos.py \
  --optimize-loader --output build/NEW-loader-fixture
./tools/dev --command python standalone/check_chat_loader_parent.py \
  --terminal build/PARENT/TERMINAL.EXE \
  --fixture build/NEW-loader-fixture --output build/NEW-loader-audit
```

## Remaining work

The parent does not call this loader yet. Establish exclusive ownership of the
borrowed frozen snapshot storage, preserve every existing user's admission,
and bind original Alt-O/reference/browser entry, pre-dequeue input hold,
receive filtering and foreground service. Retain direct TEXT-only native
Alt-number dispatch, help/notices, history/log/TX effects, traps/cancellation,
frame/cursor restoration and full geometry checks.

The remaining resident margin is tight. Linking the loader proves its own cost
fits; it does not prove that adding the frontend fits. Repeat actual ASPECT and
Enigma/Synchronet admission with the final bindings, then package/source and
reversible deployment checks and physical Boca/SPA2102/SIP/audio observations.
Full original ASPECT, emulation/protocol and Host parity remain separate work.
