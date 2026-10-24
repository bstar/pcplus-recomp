# Optional IRQ build on stock BBSes

The [composed IRQ build](PARENT_CUSTOM_IRQ.md) now has stock Synchronet and
ENiGMA evidence on COM2/19200/8N1/HARD with explicit IRQ5/7. All five workflows
use DOSBox-X8086, compile their login ASP in DOS, return through ASIOv7 and run
three guarded helpers before typing an unsaved editor draft. The card and
staged Special Edition package remain unchanged.

The [receipt](validation/irq-bbs.json) records four passing workflows and one
retained editor failure. It does not declare complete compatibility:

| BBS | IRQ | First helper return | Modem buffering | Outcome |
| --- | --- | --- | --- | --- |
| Synchronet |5| Accepted |0ms| Login, helper adoption and editor pass |
| Synchronet |7| Rejected |0ms| Login, retained bank, retry and editor pass |
| Stock ENiGMA |7| Accepted |30ms| Login, helper adoption and editor pass |
| Stock ENiGMA |5| Rejected |30ms| Login, retained bank, retry and editor pass |
| Stock ENiGMA |7| Accepted |0ms| Login/helpers pass; Home and Insert editor effects fail |

Every workflow checks current immutable product copies, exact DOS-compiled ASX,
one credential submission by the script, authentication, active IRQ configuration,
full UART/PIC/master-vector restoration, helper snapshots and actual emitted key
bytes. Helpers capture all four supported IRQ vectors; the independent receipt
checks the selected IRQ's masked state and previous-vector ownership. Rejected
returns preserve the accepted frame before a successful retry. The third helper
deliberately fails, and subsequent editor interaction proves continued use of
the parent; there is no post-third register snapshot claim. No message was saved
and no running server source/configuration was changed.

## Compact passive observer

The earlier large observer retained a4000-byte screen-copy buffer and requested
upper memory. Two first attempts in this8086 emulator profile placed it at
segment0814 instead. Neither produced LOGON.ASX or authenticated. Their generic
DOS/transport reports were green, so they are explicitly retained as failed
pilots rather than source-login or editor passes. The captured placement did
not meet the requested high-memory condition.

`--compact-observer` removes the resident screen copy and its transient output
buffer. The generated COM is358 bytes instead of8392, while the same pattern
scan, timer, signature, error/return-prompt flags and segment reporting remain.
Its eight-byte result replaces the4008-byte screen-copy record only when this
option is explicit. The full observer and `--observer-high` remain available;
the two options are mutually exclusive. Compact mode supplies no observer
console image. Main video, wire, server logs, compiler output and helper raw
captures are still independently checked.

All five compact workflows produced the exact expected compiled script and
authenticated. Five read-only corruption experiments reject a wrong IRQ5 vector,
an unmasked IRQ5, a changed accepted register bank, a changed compiled ASX and
wrong reported physical IRQ, leaving pass flags and original files intact.

## ENiGMA boundary

The immediate case sends every expected key byte, authenticates and restores
ownership, but the stock editor does not perform Home insertion or Insert
overwrite. Buffering30ms passes this measured run; it cannot guarantee how a
remote TCP server partitions input. IRQ changes do not fix the server decoder.

The receipt reuses the existing deterministic Client/editor replay only after
checking current server revision/client hashes, package/Nix pins, test inputs
and frozen logs. That historical replay retains84 fragmented-key and9 editor
differences for stock, and zero for its isolated candidate across122 checks.
It is not a fresh replay, a deployed patch or proof of arbitrary latency
handling. The [key-stream candidate](../lab/bbs/patches/enigma-key-stream/README.md)
and the user's LAN board remain separate integration targets.

The [current framed-server comparison](FRAMED_IRQ_BBS.md) now passes immediate
source login, helpers and editor interaction on IRQ5/7 against a separate
checked instance. Its stock control still fails Home/Insert. The temporary
server is stopped and no live board has received that patch.

## Reproduction

Existing owned loopback fixtures must listen on23231/23233. Use the pinned Nix
environment and fresh labels. For example:

```sh
./tools/dev --command python3 lab/bbs/directory_script_dos_probe.py \
  --label irq-sync-next --irq 5 --compact-observer --source \
  --hook-session accept --cpu 8086 --mouse-scales 8 4 \
  --terminal build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply-lookup-guarded-traps-custom-irq/TERMINAL.EXE \
  --runner build/aspect-register-parent-custom-irq/ASPECT.EXE
./tools/dev --command python3 lab/bbs/enigma_directory_script_probe.py \
  --label irq-enigma-next --irq 7 --packet-delay-ms 30 --compact-observer \
  --source --hook-session accept --cpu 8086 --mouse-scales 8 4 \
  --terminal build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply-lookup-guarded-traps-custom-irq/TERMINAL.EXE \
  --runner build/aspect-register-parent-custom-irq/ASPECT.EXE
```

Choose `--hook-session reject` for failed-return retention and retry. The
ENiGMA immediate comparison explicitly uses `--packet-delay-ms 0`; its expected
editor failure must be recorded rather than overridden by normal DOS exit.
Sustained pressure, transfers/reconnect on this exact product, branded packaging,
actual Boca/adapter behavior and full native application parity remain open.
