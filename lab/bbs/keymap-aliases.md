# Rejected ENiGMA control-alias experiment

The stock ENiGMA multi-line view advertises single-byte aliases for Home
(Ctrl-A), End (Ctrl-E) and Insert (Ctrl-V). A candidate KBD map tested whether
those aliases could avoid incomplete escape-sequence decoding without modem
packet buffering. The actual DOS/editor test failed. The candidate is a lab
fixture, not a supported compatibility profile.

`standalone/build_keyboard_profiles.py` assembles the existing source-owned
network-default declarations and expands the native 79-by-12-byte KBD layout.
It generates seven profile blocks, sufficient for zero-based supported terminal
profiles 4 and 6. No original factory KBD data is used. `NETWORK.KBD` contains
those maintained defaults. `ENIGMA.KBD` changes exactly six slots per block:
both navigation banks of Home/End/Insert. Every other binding and padding byte
is identical. Generating these fixtures does not change the terminal defaults.

The [32 linked-input checks](../../docs/validation/keyboard-profile-fixtures.json)
compare generated network defaults against the actual linked default builder
and exercise both BIOS navigation banks, arrows, Delete, page keys, Tab and Enter
through the linked keyboard normalizer, dispatcher, TX ring and UART sender.
They prove emitted bytes, not successful editor behavior.

## Actual stock-server result

The [paired report](../../docs/validation/bbs-enigma-keymap.json) retains actual
DOS runs with the same E212 terminal executable, PRM, COM2/19200/8N1/HARD,
physical-key recipe and immediate byte-transparent modem. Only the explicit KBD
bytes differ. Both load their KBD with the actual DOS reader, preserve it and the
PRM, restore sampled UART/PIC/IRQ state and close without posting.

The candidate sends `ABCDE 01 H 05 E` and later `16` for Insert, as expected.
However, body cursor status stops after `ABCDE`; the subsequent draft text is
handled outside the body. Both Home-position and overtype checks fail. The
control map retains the known default-key failure. Server/user state was not
reset between these sequential runs.

The stock compose form binds Ctrl-A to `editModeChangeSubject`. Its controller
handles action keys before the focused view, and that method focuses the subject
field. This conflicts with the multi-line view's Ctrl-A/Home alias. The observed
wire and display support that explanation; the test did not trace server view
dispatch with a runtime breakpoint. Once focus has changed, failure to observe
overtype does not independently disprove Ctrl-V while the body has focus.

Static identities and the exact stock template/config match are recorded in the
paired report. Relevant pinned upstream sources:

- [Multi-line aliases](https://github.com/NuSkooler/enigma-bbs/blob/6c25317168b762f7d9088a54d3f8295438827a0e/core/multi_line_edit_text_view.js#L64)
- [Compose action key](https://github.com/NuSkooler/enigma-bbs/blob/6c25317168b762f7d9088a54d3f8295438827a0e/misc/menu_templates/message_base.in.hjson#L886)
- [Subject-focus action](https://github.com/NuSkooler/enigma-bbs/blob/6c25317168b762f7d9088a54d3f8295438827a0e/core/fse.js#L208)

This candidate is rejected as a general workaround. The existing
[30 ms modem-buffering experiment](packetization.md) remains separate; its local
pass does not guarantee TCP boundaries or physical modem behavior. A robust
server-side solution must retain incomplete escape sequences across input
events. Neither the stock server nor default compatibility aggregate was changed
to make this experiment pass.

## Reproduce on owned loopback media

These commands exercise synthetic unsaved drafts only. Use fresh labels:

```sh
./tools/build test-keyboard-profiles
./tools/bbs-dev --command python3 lab/bbs/enigma.py start
./tools/dev --command python3 lab/bbs/enigma_keymap_probe.py \
  --profile enigma-editor --label alias-candidate-new
./tools/dev --command python3 lab/bbs/enigma_keymap_probe.py \
  --profile network --label alias-control-new
./tools/dev --command python3 lab/bbs/record_enigma_keymap.py \
  --enigma alias-candidate-new --network alias-control-new
```

A successful probe exit means the experiment was recorded and the connection
closed safely. Check `editor_passed` for the actual compatibility outcome.
The `ENIGMA.KBD` filename identifies this rejected fixture; it is not a
recommendation to load it when calling other boards.
