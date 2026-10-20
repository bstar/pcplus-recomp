# Owned DOS door compatibility

The fixture copies the installed ENiGMA v86 door modules, Doors menu/layout and
BIOS into an isolated checked keyboard-decoder candidate. It makes private,
writable copies of the installed Global War and Barren Realms Elite images.
The original images remain read-only inputs. BBS authentication uses synthetic
accounts; the game identity is `PCPlus Door Lab01`. Cloned images may contain
existing game state and remain private under ignored `build/`.

The reference probe characterizes actual game prompts. It does not substitute
for DOS-client acceptance. Global War reaches its menu, opens the paged
instructions and quits normally to Doors. Barren Realms reaches its realm-name
prompt, but the reference connection stalls after a burst name submission;
that is retained as a failure to investigate.

A reference retry sending the name 200ms per character reaches the name
confirmation. Ordinary burst submissions later stall again. The first DOS
attempt accepts the name and reaches gameplay, but its incorrect `Q` quit
recipe enters other menus and ends by disconnect. It fails normal-return
acceptance. These observations distinguish the input-timing investigation
from the test recipe's separate menu mistake.

The corrected DOS BRE route explicitly confirms the name, declines instructions,
acknowledges the title pause and uses `0` to quit. It returns normally through
Doors to Main. Both game routes pass 13 workflow checks. Passive audits reject
13 Global War and ten BRE damaged-capture cases. The
[record](../../docs/validation/enigma-v86-doors.json) binds those results, retained
failures and all 31 unchanged application products and 566 source files. This
does not resolve the reference burst-input stall or establish saved-realm
persistence after a new login.

The DOS driver runs the source-built terminal and a DOS-compiled ASPECT login
on modeled COM2/19200/8N1/HARD. Global War acceptance requires the instructions,
pager, game menu, normal worker stop, Doors return and Main return in order,
with the corresponding outgoing commands. Disconnect-triggered shutdown fails
acceptance even if the DOS program itself exits normally. A passive audit
individually removes required observations and injects error/disconnect events.

Prepare a fresh checked candidate with
`lab/bbs/patches/enigma-key-stream/check.py`, then:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_v86_fixture.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate --private-tmp
./tools/dev --command python3 lab/bbs/enigma_v86_dos.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs \
  --label UNIQUE --game gwar
./tools/dev --command python3 lab/bbs/check_enigma_v86.py --label UNIQUE
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py stop \
  --candidate build/bbs-lab/NEW/candidate
```

Never edit frozen inputs during a run or reset game images to erase failures.
The first setup attempt failed while recording the resolved dependency path
through a node_modules symlink, before server startup. A fresh candidate fixed
that bookkeeping. The first DOS run retained its game/menu captures but failed
in the report's menu-list processing; acceptance requires the corrected run.

This is a bounded interaction check, not a full game playthrough. Live board
deployment, physical RS-232/Wi-Fi modem timing and full PCPlus reconstruction
remain separate open work. No copied executable, image, BIOS, game transcript
or database belongs in this public repository.
