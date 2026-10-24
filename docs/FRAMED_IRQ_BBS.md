# Immediate ENiGMA editor on the current IRQ build

The current DOS8086 IRQ build now passes the Home/Insert editor workflow with
immediate modem forwarding against a separate ENiGMA instance containing the
existing incremental key decoder. A fresh stock control still fails both
effects. The ordinary board, user's LAN board, application binaries, staged
Special Edition package and card were not changed. The temporary server has
been stopped.

The [receipt](validation/framed-irq-bbs.json) records:

| Instance | COM2 IRQ | Helper return | Buffering | Outcome |
| --- | --- | --- | --- | --- |
| Stock loopback23233 |7| Accept |0ms| Source login/helpers pass; Home/Insert fail |
| Isolated framed23234 |7| Accept |0ms| Source login, helpers and all editor checks pass |
| Isolated framed23234 |5| Reject/retry |0ms| Retained bank, retry and all editor checks pass |

The first two runs use identical terminal/interpreter/compiler executables,
ASP/ASX, KEY, helper, compact observer, PRM, keyboard profile, full key schedule
and serial settings. Server/endpoint selection is explicit. The editor source
itself remains identical to stock. Candidate code changes are limited to the
input decoder; separate configuration and database snapshots provide isolation.
Every expected key is
present on both wires. This directly composes the existing server fix with the
current source-built parent, v7 return and guarded helpers.

All scripts compile in DOS, submit the synthetic credentials once, and resume
the parent. Raw helper snapshots verify returned bank adoption/rejection,
retry and the selected IRQ's masked vector baseline. The final hardware samples
match the original UART/PIC/vectors. No draft was saved. The third helper fails
deliberately before subsequent editor use; its returned register frame is not
separately captured.

A fresh decoder export/check passes1858 framing checks,122 actual candidate
Client/editor checks and upstream regressions. Stock deterministic replay again
demonstrates84 fragmented-key and9 editor differences; candidate differences
are zero. Its installed dependencies are reused from the owned lab, rather than
reproduced in a fresh dependency build. Four read-only evidence corruptions
reject a stock root disguised as a candidate, hidden buffering, an unmasked
IRQ7 and altered decoder source, with all original files unchanged.

## Isolation and limitations

The fixture exports a new checked source tree, snapshots only the synthetic
locadmin/loclab databases and copies the synthetic file base. Its writable db,
logs, drop, file-base and temporary paths belong to the new tree. It listens
only on127.0.0.1:23234; the existing services remain on23231/23233. The receipt
requires the experiment to be stopped and23234 available before publication.

The decoder holds incomplete escape/UTF-8 input with a bounded100ms first-byte
deadline. Delayed fragments beyond that policy can still split. These local
editor checks do not establish arbitrary latency, shared/physical IRQs,
transfers/reconnect, the custom LAN menus or complete original application
parity. The [client patch](../lab/bbs/patches/enigma-key-stream/README.md) remains
a separate server-side integration artifact. A DOS terminal cannot enforce
remote TCP receive boundaries. The measured unmodified-stock buffering
comparison remains documented in [IRQ BBS checks](IRQ_BBS.md).

## Reproduction

Use a fresh output directory and labels through the pinned Nix tools:

```sh
./tools/bbs-dev --command python3 lab/bbs/patches/enigma-key-stream/check.py \
  --source build/bbs-lab/enigma/source --output build/bbs-lab/framed-irq-next
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py setup \
  --candidate build/bbs-lab/framed-irq-next/candidate
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/framed-irq-next/candidate --private-tmp
./tools/dev --command python3 lab/bbs/enigma_directory_script_probe.py \
  --candidate build/bbs-lab/framed-irq-next/candidate --label framed-irq-next \
  --irq 7 --packet-delay-ms 0 --compact-observer --source --hook-session accept \
  --cpu 8086 --mouse-scales 8 4 \
  --terminal build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply-lookup-guarded-traps-custom-irq/TERMINAL.EXE \
  --runner build/aspect-register-parent-custom-irq/ASPECT.EXE
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py stop \
  --candidate build/bbs-lab/framed-irq-next/candidate
```

The default probe still selects stock23233. The optional `--candidate` validates
the running owned instance, records its explicit log/endpoint/source hashes,
and checks that stock sources remain unchanged. Receipt verification does not
require that a completed experiment remain running.
