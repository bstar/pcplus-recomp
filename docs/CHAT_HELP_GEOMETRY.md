# Chat Help admission and external screen changes

The opt-in Chat Help frontend now checks the existing module presentation before
queuing context3 through PROGRAM. Previously Alt-Z bypassed ordinary module-key
validation: even with an invalid BIOS screen mode, Help was queued. PROGRAM's
later display refusal could then take the generic notice/Chat-stop path and
discard unfinished input. The new guard consumes the local Help key without
queuing PROGRAM or stopping Chat when the presentation is invalid.

This is a source-maintained compatibility fix, not newly recovered original
machine code. It reuses API0106's existing presentation operation; the module,
helper, authored Help resource and ordinary Chat fault/retirement policy do not
change. [The acceptance receipt](validation/chat-help-geometry.json) binds the
new product to the actual DOS checks and frozen old-parent negative.

## Reproduction and evidence

```sh
./tools/dev --command make test-chat-help-geometry
```

Twelve DOS8086 component sessions cover25/28/43/50 initial rows, each with an
external height change, active-page change or actual BIOS mode13 transition.
The fixture loads the exact source parent as a DOS overlay and invokes its
actual far entries with its own DS=SS and stack. It supplies canonical initial
layout fields; it does not patch product instructions or ready/ownership flags.

All206028 checks pass. Invalid Help admission leaves the guarded video bytes,
unfinished `AB`, Chat ownership, loaded-module integrity and largest free DOS
block unchanged. The graphics case guards all64000 visible pixels; the page
case guards both text pages. Once valid geometry is restored, Help queues and
normal Chat retirement restores the preserved original underlay exactly.
This component queues valid Help but does not execute its DOS child.

The identical mode13 probe against the preceding6fd8aafc parent fails exactly
one of34018 checks: Help was queued despite the invalid presentation. Its
source snapshot is retained and checked independently of today's frontend.
All other guards pass. The new parent passes this same probe.

Separate current-product tests pass24 normal/repeat/resource-failure/SOFT-flow
main-loop cases and eight native-wait/full-FIFO Help sessions across all four
heights. A5323-file clean source export reproduces all four products and repeats
six ordinary/reference/Chat/busy sessions. Six ASPECT streams, recovery and
three nested children pass25 checks.

The current parent also passes authenticated stock Enigma editor → Chat → Help
→ Chat → editor return through the actual SynthModem Telnet proxy. All4000
editor and Chat frame bytes, cursors and ON-LINE status return exactly, local
input stays local and ordinary editing resumes without a saved post. Independent
final replay matches1920 cells/attributes and CPR9,8; eight copied-evidence
controls reject. Synchronet editor/external-viewer checks pass. Enigma's longer
carrier-loss/redial test and independent65539-byte retry audit also pass.

## Product identity and limits

The opt-in parent is
`fab5ac9e046627b3f59050619acf4508b3703a3b4f04455bcb9bdb8104be6dd0`.
Minimum allocation including PSP is479408 bytes,16 more than its predecessor.
DS=SS remains65504 bytes, resident CS65452 and the stack8192. Companions remain
PCCHAT6845e2c8, PCHELPf163169f and authored resource45c6cdba; the profile without
Chat Help reproduces parent471d5856 unchanged.

The geometry tests establish the admission boundary, not whole-main continuation
under an external screen change. A BIOS mode reset can erase live Chat pixels;
this change does not reconstruct those pixels. Ordinary geometry-fault policy,
allocation/lifetime faults and other original features remain open. The BBS
editor is idle while the local Help child runs; no remote payload is deliberately
scheduled inside that child. The Hayes/nullmodem model holds CTS ready.

No physical deployment or selected-package change occurs at this checkpoint.
Boca/SPA2102 SIP/audio and real flow timing still require hardware acceptance.
Earlier [connected editor](CHAT_HELP_BBS.md), [busy input](CHAT_HELP_BUSY.md) and
[recovery](CHAT_HELP_RECOVERY.md) receipts retain their original product identity;
the new receipt records these current-parent reruns separately.
