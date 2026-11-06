# Chat Alt-F6 Redisplay integration

This records the API0105 integration checkpoint. The current profile is
[API0106 with display-change protection](CHAT_VIEW_GEOMETRY.md); its new build
identities and wider height coverage are documented there.

The opt-in `--chat-redisplay` profile now opens the existing serviced history
viewer from Chat and returns to the same session. Unfinished local input stays
intact. Incoming bytes continue through Chat's plain CP437 pane projection,
history and logging effects while the frozen viewer remains visible. Escape
returns to Chat; a later Escape ends Chat normally. Alt-H, Alt-X, carrier loss
and forced stop retire the viewer before retiring the module.

This is maintained integration against the [recovered entry/return contract](CHAT_REDISPLAY_ENTRY.md),
not a claim to have recovered all original D95C viewer behavior. The old internal
`CHAT_HELP` result identifies Alt-F6 Redisplay here; global Help and Alt-Z are
separate work.

## Storage and lifetime

Chat code stays in its existing12KiB frozen-storage window. The viewer's
63000-byte history snapshot is redirected to a DOS arena allocated only when
Alt-F6 is accepted. The arena's paragraph-aligned tail saves Chat's normal
terminal underlay, because the viewer uses the existing live/view frames.
Separate normalized pointers avoid crossing a64KiB far-array boundary. The
allocation is67008 bytes at80x25 and71008 bytes at80x50; no retained capacity is
reduced. Allocation refusal leaves Chat and its local input intact.

While the viewer owns the screen, Chat presentation cursor selection is
suspended. The existing top-level receive hook restores the live Chat frame
before each raw byte. Idle service commits Chat's history/log effects and lets
the viewer save that live frame and repaint its frozen view. On return, the
normal underlay and original snapshot-segment binding are restored, Chat's
presentation resumes, and the temporary arena is freed. Free failure retains
an explicit retry phase instead of forgetting ownership or unloading code.
Fault-injection acceptance for that path remains open.

The module owns suspension, DOS allocation/free, construction and bounded
frontend admission/scheduling. The parent retains guarded viewer bridges and
an immutable50-byte CODE descriptor. API0105 has a50-byte request and480-byte
caller-owned state. Its28-byte live binding includes the viewer descriptor.
The four-relocation module image is11140 bytes in the unchanged12288-byte
window, with no DGROUP, private stack, CRT or permanently allocated DOS block.

The resident parent is479344 bytes,64 fewer than the preceding479408-byte Chat
profile. DS=SS remains65504 bytes; resident CS remains65386 bytes. The8192-byte
parent stack, six ASPECT stream buffers,512-byte heap growth, history, frozen
snapshot, live/view frames,32-key FIFO and247-row index retain their capacities.
The nested-ASPECT/six-stream gate passes with the unchanged interpreter.

## Saved-screen pointer correction

The development frontend declared two arrays in one Watcom declaration, with
`CHAT_FAR` qualifying only the first. `redisplay_view` consequently decayed
through DS in the legacy runtime constructor. The new lease refused its
mismatched backup pointer before allocation, exposing that existing bug.
Separate far declarations fix the legacy constructor too. A real DOS API0104
control verifies exact backup-buffer identity, all2000 saved/restored cells and
arena lifetime. Its module remains byte-identical to the prior API0104 module.
The selected physical package does not change at this checkpoint.

## Verification and identities

[The checked receipt](validation/chat-redisplay.json) binds the following to the
same parent/module pair:

- Real DOS parent/module/viewer composition:75085 assertions across five
  sessions, including a complete63000-byte wrapped history comparison,
  unfinished local input, search, actual export, raw RX, real DOS allocation
  refusal/retry, Escape, Alt-H, Alt-X, carrier loss, forced stop, JFT and memory
  restoration. This caller invokes parent entries on the actual DS=SS/stack.
- Normal DOS8086 main, keyboard and synthetic UART: a passive observer sees an
  empty remote pane at viewer entry, later CP437 RX in the hidden live frame,
  retained local AB, and both panes visible after return. The line transmits
  once; Chat's incoming escape sequence is not treated as a terminal query.
- All ten direct TEXT keys, native echo CPU groups,40-key pressure with all
  cancellation keys, and XOFF/RX/queued cancellation before XON.
- 26 nested-ASPECT checks,25 Synchronet screen/editor/external-viewer checks,
  and16 Enigma carrier/reconnect/transfer checks with an independent exact
  65539-byte retry audit. The BBS cases keep Chat inactive.
- A5251-file fresh public-source export with no original binaries, analysis
  artifacts, prior objects or ancestor Git. It rebuilds identical binaries and
  repeats the DOS lease and normal-main Chat viewer tests.

Parent SHA256: `bb576021eaf39847007d57bbe3a22da285c2de2fe45f6219b72f2da9ba3fe193`.
Module SHA256: `db96a2fbd602235ad99aec3a4059004c9804ed7a1466984d0a12634c580991b9`.
ASPECT remains `cbdee1949f0ac6bba34f56ae9c594a17888ef9b5143ee5dca9cd76498737ccfd`.
The API0104 control parent is `432fc6944fda1683f8f18deaf1c4915cdd3b06224cbfe7b2120bff9fade01696`;
its module remains `83b77da00ded8f2e6df652d5058ae313dc673ef15d3865304aa755f590bc3eff`.

Earlier resident implementations failed the nested-ASPECT memory gate and
were superseded. The initial main-loop fixture omitted the harness's expected
banner/query markers: its Chat-specific observations passed, but its overall
result failed. The corrected fixture passes. Those failures and the pre-fix
pointer refusal remain identified in the receipt rather than becoming accepted
results.

## Reproduce

Run the public build profile inside the pinned Nix environment:

```sh
./tools/dev --command python standalone/build_chat_redisplay_profile.py --output build/chat-redisplay
./tools/dev --command python standalone/test_chat_redisplay_dos.py --terminal build/chat-redisplay/TERMINAL.EXE --output build/chat-redisplay-lease-check
./tools/dev --command python standalone/test_chat_redisplay_main_dos.py --terminal build/chat-redisplay/TERMINAL.EXE --output build/chat-redisplay-main-check
```

Keep the matched `TERMINAL.EXE` and `PCCHAT.OVL` together. Loader identity and
API checks intentionally refuse a mismatched module. This profile is not yet
the selected physical-card package.

## Remaining acceptance

The live Chat/viewer matrix currently covers80x25. Other supported row heights,
geometry changes while nested, DOS free failures, logging/printer faults,
sustained saturation and physical flow/carrier behavior need additional checks.
The Boca → SPA2102 → SynthModem → Enigma physical route and audio acceptance
remain separate from these software results. No card deployment, private
configuration/call-history update or production bridge/network change occurred.
Global Help/Alt-Z, broader Chat UI polish and the ASPECT/emulation/protocol/Host
inventory remain part of the active goal.
