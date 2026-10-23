# Current register build on owned BBSes

The optional ASIO v7 terminal and interpreter now have live script/editor
evidence on the existing local Synchronet and stock ENiGMA instances. This
extends [register handback](REGISTER_HANDBACK.md) beyond the synthetic peer. It
does not enable HOOK or establish complete BBS compatibility.

The terminal is
`build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers/TERMINAL.EXE`;
its interpreter is `build/aspect-register-parent/ASPECT.EXE`. The probes accept
explicit products, verify their manifests and complete declared source closure,
and run immutable copies. The ordinary terminal/interpreter products and the
running BBS services are not replaced or reconfigured.

## Observed behavior

All live cases run DOSBox-X in8086 mode, COM2 at19200 baud,8N1 and HARD flow
control. Valid mouse scales8/4 are explicit synthetic PRM inputs. The selected
directory launches ASPECT, which sends the synthetic account credentials once.
Actual keyboard input begins after login. The parent then resumes the editor;
drafts are aborted or left unsaved on disconnect. No message is submitted.

Synchronet passes with immediate modem forwarding. Its editor audit checks the
emitted Home/End/Insert/Delete/Tab/page/control keys and their expected visible
effects, together with draft abort, configuration/directory accounting and UART
register/vector restoration.

Stock ENiGMA passes with explicit30ms byte-transparent modem buffering. Repeated
immediate-forwarding trials include both a complete editor pass and a Home/Insert
failure, despite successful login, script return and exact expected key bytes
on the wire. Neither the passing trial nor buffering proves that arbitrary TCP
chunk boundaries work. The failed trial is retained as a failed editor result;
normal DOS exit does not override it.

The [receipt](validation/register-bbs.json) records each outcome, exact product
and source identities, raw capture hashes and unsaved-draft evidence. The
server-side [key-stream experiment](../lab/bbs/patches/enigma-key-stream/README.md)
is replayed separately against the same stock Client hash: forced partitions
reproduce84 key and9 editor differences. An isolated candidate has zero such
differences across122 checks. The framing oracle passes1858 checks, including
200 clock/deadline cases, and upstream regressions pass. A successful stock
counterexample test means the expected defect was reproduced. No candidate was
installed on the running BBS. Reused installed server modules are not a clean
dependency-reproduction proof.

## Reproduction

Use fresh labels; each run preserves its artifacts. Existing owned services are
required on loopback23231 and23233. The probes use only their synthetic lab
accounts, not the separately running LAN server or private credentials.

```sh
./tools/dev --command python3 lab/bbs/directory_script_dos_probe.py \
  --label register-sync-next \
  --terminal build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers/TERMINAL.EXE \
  --runner build/aspect-register-parent/ASPECT.EXE --mouse-scales 8 4 --cpu 8086
./tools/dev --command python3 lab/bbs/enigma_directory_script_probe.py \
  --label register-enigma-next --packet-delay-ms 0 \
  --terminal build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers/TERMINAL.EXE \
  --runner build/aspect-register-parent/ASPECT.EXE --mouse-scales 8 4 --cpu 8086
```

For the buffered comparison, explicitly select `--packet-delay-ms 30`. The
default modem model remains immediate. Source-based login probes can still
select `--source` for actual DOS compilation; this checkpoint uses precompiled
ASX and does not claim the source-compilation route was rerun.

The receipt generator checks all raw and semantic outcomes independently of the
probe's process exit, including unsuccessful immediate trials:

```sh
./tools/dev --command python3 standalone/record_register_bbs.py \
  --sync-label register-sync-01 --enigma-buffered-label register-enigma-buffer30-01 \
  --enigma-immediate-label register-enigma-immediate-01 \
  --enigma-immediate-label register-enigma-immediate-02 \
  --enigma-immediate-label register-enigma-immediate-03 \
  --decoder-replay build/bbs-lab/register-key-stream-replay-01 \
  --output docs/validation/register-bbs.json
```

## Remaining work

Stock ENiGMA's fragmented key handling remains an integration gap. The isolated
server candidate and buffered bridge are separate mitigations; this evidence
does not establish perfect behavior on the user's LAN server or a real modem.
These live cases do not inspect register-bank mutations, sustained flow pressure,
file transfers or reconnect within the same session. Those require composition
with the existing dedicated tests. Guarded HOOK routing, supported returned-PRM
application, additional native fields and full application/hardware gates remain
open.
