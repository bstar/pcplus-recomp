# Combined ENiGMA compatibility candidate

`enigma_combined_fixture.py` composes the keyboard stream, transfer owners,
validated save reads, v86 UART input bridge and controlled-error image flush.
It stages actual owned search/index/NFO/upload menus, the two DOS door routes
and the direct ZORK save probe. Authentication and catalogs are synthetic;
game/story copies remain private. The live board and original images are not
modified.

The [validation record](../../docs/validation/enigma-combined.json) accepts all
seven DOS routes: 101 checks and 80 damaged-evidence rejections. Its cumulative
audit rejects 12 additional corruptions. Controlled image-error and partial-write
probes pass on the same staged core. Separate component checks pass 15 atomic
image cases, 39 transfer-owner cases, 49 save-read cases and nine owned v86
registry/IPC regressions; the actual Z-Machine worker survives corrupt restore.

The search fixture creates the stopped base once. The DOS and Infocom staging
functions explicitly validate and reuse that base; their ordinary standalone
mode still requires a fresh setup. Each stage refuses duplicate preparation.
After staging, the composer records the union of final runtime inputs and
rebinds each test fixture's shared menu/config/module hashes to that final
configuration. Original source hashes remain separate and are verified.

Prepare a fresh keyboard-stream checked source export, then:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_combined_fixture.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate --private-tmp
./tools/bbs-dev --command python3 lab/bbs/enigma_combined_run.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs --prefix UNIQUE
```

The suite runs existing actual DOS routes and their passive audits sequentially
against one server: repeated receive/skip/receive with NFO return; upload
cancel/NFO/retry/NFO; save cancellation and invalid/missing paths; cross-worker
overwrite/restore; malformed restore followed by valid restore; BRE name/menu/
quit; and Global War instructions/pager/quit. The overwrite result deliberately
feeds the corrupt-restore route. No save or upload data is reset between tests.
The generated archive payload matches the established small-archive timing
recipe; the first larger prepared fixture is retained separately.

The runner freezes runtime inputs and existing producer/checker source hashes,
records every command and result, and stops at the first failure. Existing
failed labels must not be reused. Only executed, accepted individual routes
count toward cumulative acceptance; a prepared fixture or normal process exit
does not establish compatibility. Stop only this owned server afterward with
`enigma_key_stream_fixture.py stop --candidate ...`.

After the DOS suite, the preserved instance is stopped for second synthetic-user
enrollment with `enigma_concurrent_upload.py --setup`, then restarted with the
same configuration and data. `enigma_combined_concurrent.py` reuses the two-peer
reference route while keeping a complete baseline of earlier uploaded files.
Its snapshot delta concerns only the new CONCA/CONCB files; full installed lists
and prior file identity/content/catalog remain recorded and checked. The run
passes 22 checks, the protocol audit rejects 19 corruptions, and the additional
preservation audit rejects eight. These are reference peers, not concurrent DOS
clients. No earlier upload, save or game data is reset.

The first reference attempt's empty-directory assumption and a later attempt's
queued Main achievement are retained as failures. The adapter waits for the
actual visible Main command prompt before submitting F and acknowledges queued
achievement notices. Its CLI preflight correction occurred before connection.
Use unique labels and audit the successful run with
`check_enigma_combined_concurrent.py`. `record_enigma_combined.py` records the
accepted suite and optional reference run after verifying source/image/product
identities; it refuses missing or failed acceptance artifacts.

This fixture does not reproduce the complete live board configuration, full
catalog or user database. Its direct story probe is separate from live custom
library navigation. Component/worker evidence and modeled syscall failures
remain distinct from actual DOS workflows. Physical RS-232/Wi-Fi modem timing,
power-loss recovery, concurrent guest writes and complete PCPlus reconstruction
remain open regardless of these route results.
