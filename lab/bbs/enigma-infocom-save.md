# DOS SAVE/RESTORE across worker sessions

The [recorded DOS run](../../docs/validation/enigma-infocom-save.json) passes
all11 checks; all11 corrupted or incomplete evidence cases reject. The retained
first attempt remains explicitly failed. No whole-application gate closes.

This isolated fixture copies the owned board's exact Z-Machine door, worker
and save-dialog source, plus its locally installed Zork I release. Story bytes,
saved games and transcripts stay in ignored `build/`. It copies no live user
database or saved games and changes no live code, configuration or service.

The checked keyboard-stream candidate supplies the base ENiGMA instance with
only synthetic accounts. An added `ZORK` command selects the copied door;
this route does not claim to reproduce the live custom library/menu. Its
configured save root is entirely inside the candidate, and the runner refuses
a nonempty save root. Use a fresh candidate and label for every attempt.

The actual DOS terminal sends:

`Main → ZORK → NORTH → SAVE locprobe → QUIT → Main → ZORK → RESTORE locprobe
→ LOOK → QUIT → Main`.

The first game saves at North of House. The second worker must start a fresh
game at West of House before RESTORE returns to North of House and LOOK
confirms the restored location. Both complete worker lifecycles, exact outgoing
commands, normal DOS exit/device restoration, unchanged source inputs and no
saved messages are required. A file-existence check alone cannot pass: the
saved Quetzal IFF extent, required memory/stack chunks and release/serial/checksum
identity must match the actual story. The saved path must belong to the
synthetic user's server-created per-account/per-story namespace.

Run from the repository through the pinned Nix environments. Replace `NEW`
and `NEW_LABEL` with fresh names:

```sh
./tools/bbs-dev --command python3 lab/bbs/patches/enigma-key-stream/check.py \
  --source build/bbs-lab/enigma/source --output build/bbs-lab/NEW
./tools/bbs-dev --command python3 lab/bbs/enigma_infocom_save_fixture.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate
./tools/dev --command python3 lab/bbs/enigma_infocom_save_dos.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs --label NEW_LABEL
./tools/dev --command python3 lab/bbs/check_enigma_infocom_save_audit.py \
  --candidate build/bbs-lab/NEW/candidate --label NEW_LABEL
./tools/dev --command python3 standalone/record_enigma_infocom_save.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs --label NEW_LABEL
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py stop \
  --candidate build/bbs-lab/NEW/candidate
```

The audit checker removes restored-room evidence, the save prompt, RESTORE,
one game entry, worker completion and menu return, then introduces a worker
error. It also rejects empty/truncated saves, an invalid IFF length and a
different story identity: eleven independently rejected corruptions.

The first attempt correctly saved and restored but failed its route assertion:
the test incorrectly expected SOUTH from North of House to reach West of House.
The game blocks that move. Its report, captures and exact original runner remain
retained under `infocom-save-dos-20261019-01`; the corrected recipe omits that
unnecessary move and runs in a fresh instance.

This is one story's save/restore workflow. Save overwrites, cancellation, bad
save files in the actual door, other stories/doors, live decoder installation,
full live-menu acceptance and physical RS-232 Wi-Fi modem operation remain open.
The [ENiGMA acceptance matrix](../../docs/ENIGMA_COMPATIBILITY.md) and full
application gates remain authoritative.
