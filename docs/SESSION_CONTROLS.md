# Live sound and mouse settings in PRM projection

The optional `--session-controls` terminal build adds current sound policy and
accepted mouse preferences to the existing session PRM projection. It closes
these two known fields of the helper-input gap; it does not enable HOOK or apply
settings returned by a helper.

PRM word 0x01BC is the sound preference: zero disables it and any nonzero word
enables it. The active terminal stores a normalized Boolean. Projection writes
zero when disabled, preserves a baseline nonzero word when still enabled, and
writes one when enabling a previously zero word. Thus an unchanged enabled
preference does not silently normalize an opaque native representation.

Words 0x04E4/0x04E6 are accepted X/Y mouse scales, each 1–999. Projection calls the
existing far `terminal_mouse_selected_scale` accessor. It reads the selected
preference even if no INT33 driver is present; uninitialized native driver words
are not a replacement for it. Offered settings remain invisible until the mouse
owner's normal commit. Discard and failed offers retain the previous selection.
The field mapping and bounds come from [configuration](CONFIGURATION.md) and the
existing [mouse owner](MOUSE_KEYBOARD.md).

## Transaction and memory

The production API snapshots and validates the three controls before calling
the ordinary full-image projector. Invalid sound/scales return 9 with output
untouched. Existing capture/context, group-policy, extent, overlap and serial/
modem/transfer validation remain in force. Only after that projector succeeds
are the three bounded words written. There is no later rejection path and no
additional PRM image on the stack.

All added code is in HOOK_CODE, which grows 156 bytes. Near code and the 65,520-byte
data/stack extent are unchanged. The old register variant rebuilds to exactly
the [previously BBS-tested executable](REGISTER_BBS.md). The new flag requires
the baseline, mouse, notice-input and sound owners; all declarations and behavior
remain gated. The child ASPECT build and ASIO v7 layout are unchanged.

## Validation

The [receipt](validation/session-controls.json) binds:

- 104 linked full-image cases: existing group/rate and refusal cases, five raw
  sound representations, both active sound states, scale boundaries/interior
  values, absent-driver selection, uncommitted/discarded/accepted offers and
  damaged live controls. Projection must not issue interrupts/port IO or change
  active globals. The pinned getter's verified memory operands locate the two
  deliberately damaged private words; no routine is substituted.
- Five actual 8086 DOS startup workflows: serial, MODEM, directory MODEM/DIRECT
  and invalid inactive modem-private bytes. A diagnostic-only caller toggles
  sound and uses the normal mouse offer/commit APIs to select 999/1 before driver
  acquisition. The original startup spelling is renamed away before projection.
  Exact 1,264-byte results, the unchanged retained baseline/seal, files and hardware
  snapshots are checked. This controlled mutation is not a live editor test.
- Fourteen COM1/COM2 register recovery workflows on the new layout, checking 86
  parent/child bank snapshot pairs and actual post-child RX/parser/TX replies.
- Six exact products rebuilt in an empty tree from 691 admitted source files,
  plus exact reproduction of the older BBS-tested terminal without the flag.

Diagnostic `*-controls-probe` products contain the deliberate mutations and file
captures; the ordinary `*-controls` product contains neither the probe symbol nor
its file names. Both remain source-built 8086 DOS products using pinned Nix tools.

```sh
./tools/dev --command python3 standalone/build_terminal.py \
  --external-render --mouse --notice-sound --notice-input --aspect-keys \
  --directory-keys --process-bank --session-capture --session-projection \
  --session-baseline --register-handoff --session-controls
./tools/dev --command python3 standalone/check_session_projection.py \
  --session-controls --output build/session-controls-linked-next
```

Add `--projection-probe` to build the diagnostic variant, then use a fresh output:

```sh
./tools/dev --command python3 standalone/test_session_projection_dos.py \
  --session-baseline --session-controls --output build/session-controls-DOS-next
./tools/dev --command python3 standalone/prove_directory_keys_source.py \
  --process-bank --session-capture --session-projection --session-baseline \
  --serial-bank --register-handoff --session-controls \
  --output build/session-controls-source-next
```

Register tests accept `--session-controls` to select this product. The ordinary
output is `build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls/TERMINAL.EXE`.

## Remaining integration

Sound and mouse preferences now project; additional native metadata, guarded
HOOK routing, returned-state validation/application and combined owner lifecycle
still require integration. These tests do not claim a physical mouse/modem test
or new live BBS coverage for this optional variant. The separate ENiGMA stream
fragmentation gap remains open.
