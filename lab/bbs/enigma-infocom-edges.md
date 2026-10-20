# DOS save-dialog edge workflows

The owned worker exits on a non-IFF save. The
[staged save-read candidate](patches/enigma-save-read/README.md) rejects the
malformed restore and returns control to the game. The original failure and
candidate startup correction remain in the
[validation record](../../docs/validation/enigma-infocom-edges.json).

Three actual DOS sessions share one isolated synthetic account and private
save namespace. Each uses a DOS-compiled ASPECT login, source-built terminal
and the exact owned door with the explicit candidate:

1. Cancel SAVE, reject `../x`, cancel the reprompt, attempt a missing restore,
   LOOK and quit. No save file may be created.
2. Save at North of House, restart, overwrite that named save at West of House,
   then quit. A second worker starts, moves north, restores and confirms West.
   Two different valid Quetzal snapshots must occupy the same owned save path.
3. Move north and attempt a generated malformed save. The rejection must leave
   the game playable at North. A subsequent valid restore and LOOK must confirm
   West; the valid save and malformed fixture must remain unchanged.

The routes pass 13, 14 and 14 checks. Their passive audits reject 9, 10 and 9
damaged evidence variants. Actual worker methods and files additionally pass 49
component checks, including bounded/immutable reads and the upstream write
path. All 31 application products retain their prior identities. No source
build or physical-modem compatibility is inferred from the server tests.

After preparing a fresh checked save fixture and staging the candidate, start
it once, then run these modes in order with different labels. Cancel and
overwrite require empty save data; corrupt requires the valid save left by
overwrite. Existing save data is never cleared to satisfy a rerun.

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate --private-tmp
./tools/dev --command python3 lab/bbs/enigma_infocom_edges_dos.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs \
  --mode cancel --label UNIQUE_CANCEL
./tools/dev --command python3 lab/bbs/enigma_infocom_edges_dos.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs \
  --mode overwrite --label UNIQUE_OVERWRITE
./tools/dev --command python3 lab/bbs/enigma_infocom_edges_dos.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs \
  --mode corrupt --label UNIQUE_CORRUPT
```

Audit each retained label with `lab/bbs/check_enigma_infocom_edges.py`. Stop
only this owned server with `enigma_key_stream_fixture.py stop --candidate ...`.
Stories, saves, transcripts, runtime databases and generated malformed data
stay under ignored `build/`. Do not edit frozen runner or candidate inputs
during a DOS run.

This covers one story/release and the direct isolated ZORK route. Live custom
library navigation, deployment, physical RS-232 behavior, concurrent save
writers, other doors and full application reconstruction remain open.
