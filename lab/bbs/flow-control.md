# Serial flow and editor control keys

The current source-built DOS terminal passes all12 audited stock Synchronet
FSEditor checks with **HARD** on COM2/19200/8N1. A matched **SOFT** run passes
the other11 checks but cannot abort with Ctrl-Q. Both runs use the same binary,
complete keyboard input, harness sources and synthetic PRM except its flow words.
The recipe clears the synthetic body line before measuring editor behavior.
Server/user state is not reset between the sequential runs.

| Flow selected in DOS and modem model | Ctrl-Q bytes from DOS | Ctrl-Q bytes to BBS | Editor abort |
| --- | --- | --- | --- |
| SOFT | 1 | 0 | Fails |
| HARD | 1 | 1 | Passes |

The raw serial capture contains Ctrl-Q (`0x11`) in both cases. With software
flow selected, the modem model records that byte as XON and consumes it at the
serial boundary. With HARD selected, it reaches Synchronet and the editor
reports `Aborted.` after editor entry. This local case calls for matching
hardware-flow settings when testing the physical modem. The DOSBox fixture
holds CTS ready; cable signals, real CTS stalls and firmware behavior remain
unverified. The earlier SOFT COM1/38400 observation remains in report history;
it differed from its HARD comparison in both port and rate and was not a
controlled flow comparison.

The [matched report](../../docs/validation/bbs-synchronet-software-flow.json)
contains both successful DOS harness runs, the failed SOFT editor audit, the
passing HARD audit, byte counts, XON event and retained artifact hashes. It
does not turn the software-flow failure into a compatibility pass. The
[current BBS checkpoint](modern-compatibility.md) selects HARD for Synchronet
and separately preserves the ENiGMA immediate/buffered comparison.

Reproduce on the owned loopback Synchronet server, using new labels:

```sh
./tools/dev --command python3 lab/bbs/synchronet_editor_dos_probe.py \
  --flow SOFT --label editor-soft-comparison
./tools/dev --command python3 lab/bbs/synchronet_editor_dos_probe.py \
  --flow HARD --label editor-hard-comparison
./tools/dev --command python3 lab/bbs/record_synchronet_flow.py \
  --soft editor-soft-comparison --hard editor-hard-comparison
```

The SOFT probe deliberately exits nonzero when its abort audit fails. Run the
HARD control afterward as a separate command. Neither recipe submits an editor
save command. HARD remains the runner's default; NONE is accepted for additional
diagnostics but has no actual editor result in this comparison.
