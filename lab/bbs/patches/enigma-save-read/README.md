# Validate save reads before VM restore

The owned Z-Machine worker terminates when the upstream parser receives a
non-IFF save. The retained actual-worker probe reproduces `Not an IFF file`
after exercising cancellation, invalid names, missing saves and overwrite.
This candidate rejects malformed restore input before handing bytes to the VM.
It changes the dialog and worker and adds one authored `save_read.js` helper.
The live board remains unchanged.

The helper checks the exact IFF extent, IFZS container, required unique chunks,
story release/serial/checksum, program-counter bounds, compressed-memory runs,
dynamic-memory size and complete stack-frame extents within the VM's actual
configured capacity. Its 128KiB read bound matches this installed VM's restore
buffer. Only regular files are read; symlinks are rejected. Descriptors close
on success and read failure. The dialog receives an immutable validated byte
snapshot, so replacing or overwriting the file afterward cannot change that
restore read. The existing write backend continues to replace a named save.

Structural validation does not prove that every game variable in a valid
container is meaningful. Concurrent writers and write publication are separate
work. This experiment does not claim arbitrary damaged-state recovery or a
full story playthrough.

Stage into a fresh stopped [isolated save fixture](../../enigma-infocom-save.md):

```sh
./tools/bbs-dev --command python3 lab/bbs/patches/enigma-save-read/stage.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs
./tools/bbs-dev --command node lab/bbs/enigma_infocom_edge_worker.js \
  build/bbs-lab/NEW/candidate build/bbs-lab/NEW_WORKER_RESULT
./tools/bbs-dev --command node lab/bbs/patches/enigma-save-read/check.js \
  build/bbs-lab/NEW/candidate build/bbs-lab/NEW_WORKER_RESULT \
  build/bbs-lab/NEW_COMPONENT_RESULT
```

The worker probe uses the actual owned interpreter and local story. The 49
component checks use real saves, filesystem data and dialog methods; two
read-provider error boundaries are explicitly modeled. Both are distinct from
the [actual DOS workflow](../../enigma-infocom-edges.md).

The first staged candidate accessed VM options before initialization and failed
at startup. The corrected worker passes a deferred stack-limit getter; its
actual worker and DOS acceptance use the initialized capacity. That failed
candidate remains retained alongside the original parser failure.
