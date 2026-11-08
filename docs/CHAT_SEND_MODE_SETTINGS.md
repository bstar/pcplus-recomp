# Original Chat send-mode setting

The later [live configuration checkpoint](CHAT_SEND_MODE_LIVE.md) connects this
field in an opt-in parent/API0107 module. Statements below about unbound live
construction describe this earlier offline-settings checkpoint.

The original Chat controller selects its send mode using a single byte at
DS1D76h, PRM offset01F2h. Zero sends each key immediately; every nonzero value
selects line buffering. The adjacent byte remains opaque. This is not a16-bit
boolean field, and rejecting noncanonical nonzero values would change the
original import behavior.

Fresh REA instruction evidence for overlay15:E828 observes the byte comparison
atE9F7, the zero branch toEA44 and the existing buffered editing path.
The analysis image is the previously verified loader-derived overlay15 image,
SHA2564ae6ee164991ab772dcb0dba4974fe30d00ee97429719dbbe0b56d5756fbc868.
It was inspected statically and never executed. Evidence identifier:
`ev_e10972d2942871fa8a17cf33cd587285c16cd9d0bdf6f793e65949dc26b362db`.
The [PRM format ledger](CONFIGURATION.md) establishes the memory-image baseDS1B84h;
[Chat recovery](CHAT_NATIVE.md) records the controller and component semantics.

The source codec now exposes `chat_buffered` as a byte. The optional offline
editor field is named **Chat send mode** and preserves all other bytes. Build
with the pinned toolchain and a new output directory:

```sh
./tools/dev --command python standalone/build_setup.py \
  --chat-mode --mouse --notice-sound --custom-irq \
  --output-dir build/my-chat-settings
```

This is an offline settings tool, not a newly selected application package.
The current terminal frontend still supplies buffered mode unconditionally.
Startup import, live adoption and module construction must be connected and
validated before this field changes the interactive terminal's behavior.
The native/component send owner already implements both modes. No physical
configuration or selected payload is changed by these tests.

## Validation

The [receipt](validation/chat-send-mode-settings.json) records1446 linked field-model
inputs across ordinary and mouse-enabled builds, plus separate real-DOS C-runtime
runs. New cases exercise all256 mode bytes with a deliberately nonzero adjacent
byte, invalid-input rejection and exact image preservation. The Python codec's
synthetic roundtrip suite passes all ten tests.

Four actual BIOS-key workflows save0,1 and255, reload each file on the next
invocation, then cancel a change from255 to0. Each compares the complete1264-byte
image and checks that replacement files are cleaned up. Initial Shift-Tab/Up
fixtures crossed to the previous page, attempted the wrong edit and timed out;
they are retained and excluded. The corrected recipe advances through all fifteen
following TERMINAL fields. A separate renamed-main watchdog probe also failed
and supplies no acceptance evidence.

A fresh export containing only30 declared public source files reproduces the
optional editor exactly: SHA256
`1c4ad0636cc611569172315216b0dea13f983b174bbe5f01aa4fca9ad15b3f26`.
Without the new build option, the current mouse/sound/custom-IRQ editor remains
byte-identical to the packagedPRMEDIT: SHA256
`0a8452e70e10514fd03131dcf096283baca7bc7955e4883a380861e5bebef26e`.
The opt-in editor enables scrolling for its longer TERMINAL page, including
builds that do not enable both mouse and sound fields.
