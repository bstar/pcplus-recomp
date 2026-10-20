# Explicit transfer temporary owners

This isolated ENiGMA experiment supersedes the earlier tracked-session upload
patch. It changes three core modules and adds `transfer_temp_owner.js`; it does
not install changes on the running board or change the DOS application.

The original shared `temptmp` upload session can retire another upload's data.
The earlier per-upload session fixes that scope, but its dependency handles only
successful deletion promises. `../enigma-upload-temp/reproduce-rejection.js`
demonstrates the resulting unhandled EACCES rejection: free-time accounting is
released, but the receive completion callback never runs. The deletion rejection
is modeled and the partial file is real. Earlier successful captures remain
valid within their recorded scope.

The new helper issues private upload or file-list owners. Callers cannot grant
deletion authority by supplying an arbitrary directory or forged prototype.
Cleanup coalesces callers, completes asynchronously on callback errors or
synchronous throws, and retains failed owners for retry. Starting another
transfer retries failed retirement without removing active peers. Exit cleanup
attempts the remaining owners even when one removal fails. Directories use
`mkdtemp`; file lists live inside their own directory and close through
`writeFile` before protocol execution.

The upload module passes its owner through protocol selection and details.
Receive failure preserves the original protocol error and releases free time
before cleanup. Cleanup failure is logged and cannot block menu return. Each
transfer tracks only its own file-list owners. Synchronous protocol-spawn throws
retain the upstream throw contract after initiating cleanup; this is not a
complete replacement for upstream exception/error UI handling.

Stage only into a fresh, stopped, successfully checked upload fixture:

```sh
./tools/bbs-dev --command python3 lab/bbs/patches/enigma-transfer-owner/stage.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs
./tools/bbs-dev --command node lab/bbs/patches/enigma-transfer-owner/check.js \
  build/bbs-lab/NEW/candidate build/bbs-lab/transfer-owner-unit/NEW
```

The stage records original and staged core hashes, authored helper provenance
and exact patch inputs. The component suite uses actual module methods and
private filesystem data with explicit provider fault models. It also covers
file-list write failures, independent owners, callback completion and exit
continuation. It does not establish simultaneous BBS sessions.

The later [two-session network test](../../enigma-concurrent-upload.md) verifies
active-upload preservation across another client's cancellation and successful
details cleanup using two actual reference-peer connections. Concurrent DOS
clients, file-list protocols and combined deletion-error concurrency remain
separate acceptance work.

See [DOS/network acceptance](../../enigma-transfer-owner.md) for the separate
normal and deletion-error workflows. Physical modem acceptance, upload carrier
loss, original source dates and full application reconstruction remain open.
