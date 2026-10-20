# Upload cleanup failure and recovery

Use two fresh isolated copies of the owned ENiGMA server, each with the existing
keyboard decoder candidate and the [explicit transfer-owner patch](patches/enigma-transfer-owner/README.md).
Neither copy shares writable runtime data with the live board.

The normal workflow cancels after valid data and a peer ACK, checks that no
partial was installed or retained, opens an NFO, retries the binary/empty batch,
accepts both detail forms and opens the NFO again. It requires 21 checks and
22 rejected evidence corruptions.

The second workflow uses `fault-once.js` as an isolated Node preload. It denies
exactly one upload-directory `fs.rm` callback with EACCES. Actual DOS input,
protocol bytes, filesystem data and menu execution remain real. The first NFO
must remain interactive despite this modeled deletion error. The intermediate
snapshot must retain only the denied owner's partial, with no installed file or
catalog entry. Starting the retry retires that failed owner. Final stored files
and metadata must match, dates must be current and private temporary data must
be gone. This route requires 24 checks and 26 rejected evidence corruptions.

A separate actual DOS download regression uses the same staged core: receive
ZIP A, explicitly skip its existing DOS alias, then receive ZIP B, with NFO
input after all three transactions. It checks exact data, unchanged existing
file identity, finish snapshots, visible Save/Skip/Save labels and hardware
restoration. Thirteen checks and seven rejected capture corruptions bind this
route; component tests separately exercise the file-list argument branch.

Start and test one fixture at a time; both use the same fixed loopback port.
For the normal copy omit `--cleanup-fault-once` and `--cleanup-error`:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate --private-tmp --cleanup-fault-once
./tools/dev --command python3 lab/bbs/enigma_upload_dos.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_LABEL \
  --cancel-first --upload-bytes 65539 --cleanup-error
./tools/dev --command python3 lab/bbs/check_enigma_upload_audit.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_LABEL
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py stop \
  --candidate build/bbs-lab/NEW/candidate
```

Never edit the runner, checker, observer or fixture inputs during a DOS run.
Preserve failed outputs and use new labels/candidates rather than clearing data
to satisfy acceptance. The sanitized [validation record](../../docs/validation/enigma-transfer-owner.json)
binds both routes, the retained earlier promise-rejection failure, component
checks, upstream regressions and unchanged application products. Raw accounts,
server logs and protocol captures stay in ignored `build/`.

The live decoder and upload fixes are not deployed. Concurrent BBS sessions,
physical RS-232 modem behavior, upload carrier loss, source-date preservation
and full F01–F16 reconstruction remain open.
