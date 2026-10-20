# Controlled DOS-door error persistence

The earlier input bridge reports a queue error before its isolated worker sends
the final image. The actual parent then completes the menu and writes its old
SAB. When `stopped` later transfers the changed image, the once-only finish
callback has already run. The guest's completed file write is lost on disk.

The real DOS probe creates and closes `C:\ERRCHK.TXT`, reports readiness over
COM1, then receives one deliberately oversized input chunk. The baseline parent
returns before the child sends its changed image. A fresh guest boot from disk
cannot read the new marker. This is an observed counterexample, not a modeled
worker or simulated file write.

This separate stage changes two owned modules and adds `image_flush.js`:

* Controlled serial-input errors call shutdown with the error. The worker sends
  it in `stopped`, so the existing isolated IPC path transfers the image first.
* The parent records that error and waits for the image flush before completing
  the menu and releasing the door slot. Listener cleanup and completion remain
  once-only.
* Writes use a same-directory exclusive temporary file, preserve permissions,
  sync file contents, atomically rename and sync the directory. A failure before
  commit preserves the prior complete image. An error after rename explicitly
  records that the image was committed.
* A failed flush is reported to the caller; the next flush can retry the retained
  SAB instead of inheriting a permanently rejected queue promise.

Stage into a stopped fixture that already has the input bridge:

```sh
./tools/bbs-dev --command python3 lab/bbs/patches/enigma-v86-shutdown/stage.py \
  --candidate build/bbs-lab/NEW/candidate
./tools/bbs-dev --command node lab/bbs/patches/enigma-v86-shutdown/check_image_flush.js
```

The component suite uses real temporary files and explicit syscall fault models
for open, chmod, partial write, sync, close, rename and cleanup errors. It tests
symlink-target publication, permission preservation and retry after rejection.
Fifteen checks pass. It does not simulate a hardware power cut.

The VM probe uses the actual owned door, isolated child/worker, v86, FreeDOS and
filesystem. Config, logger and the BBS client are declared stand-ins. The fixed
case requires cold guest readback of the new file. The partial-write case
injects ENOSPC after writing part of the temporary image, verifies the old image
is byte-for-byte intact, checks the logged failure, explicitly retries the
retained state and requires cold guest readback afterward. This tests the real
flush API; it is not an acceptance claim for every subsequent BBS retry route.

Raw images, serial output and runtime artifacts remain under ignored `build/`.
The stage does not patch the running board. Abrupt process crashes before image
transfer, concurrent guest writes, real power loss, physical modems and full
application reconstruction remain outside these controlled-error results.
