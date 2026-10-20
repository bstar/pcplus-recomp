# DOS door error completion and disk persistence

The actual parent/isolated-worker path can lose a completed guest file write
on controlled input failure. DOS creates and closes a marker file before a
deliberate oversized input. The baseline parent returns to its menu and saves
its old image; the child transfers the changed image afterward. A new DOS boot
cannot read the marker. The retained baseline verifies this ordering and loss.

The [shutdown candidate](patches/enigma-v86-shutdown/README.md) carries the input
error with `stopped`, transfers the image first, awaits atomic disk publication
and then completes the menu/releases the slot. A failed publication remains
retryable. The fixed real DOS probe reads the marker from a fresh disk load.
With modeled ENOSPC after a partial temporary-image write, the prior complete
image remains unchanged; the failure is logged, the temporary is removed and
an explicit retry publishes the retained state for cold guest readback.

The baseline audit rejects ten damaged cases. Fixed and partial-write audits
reject 11 and 13. Both fixed probes also pass against the composed instance,
with the same audit counts. Fifteen real-file/component checks include explicit
syscall fault models. Nine owned v86 registry/isolated-IPC regressions pass.
Config, logger and the BBS client in the file probe are declared stand-ins;
v86, FreeDOS, file writes, IPC transfer and cold reads are real.

```sh
./tools/bbs-dev --command node lab/bbs/enigma_v86_shutdown_probe.js \
  --candidate build/bbs-lab/NEW/candidate \
  --image /home/bstar/projects/black-flag-bbs/local/doors/images/bre.img \
  --label UNIQUE --expect fixed
./tools/bbs-dev --command python3 lab/bbs/check_enigma_v86_shutdown.py \
  --label UNIQUE
```

Add `--flush-fault partial` for the explicitly modeled write failure. Use
`--expect baseline` only with the earlier input-bridge worker to reproduce data
loss. The image is copied to the unique output folder before boot; original
images are read-only inputs. Never reuse output labels or publish raw images.

The [combined validation record](../../docs/validation/enigma-combined.json)
binds these results to the seven actual DOS routes and two-peer reference
upload workflow. All 31 DOS products and 566 application source files are
unchanged. This does not establish every BBS retry route, abrupt process-crash
recovery, power-loss recovery, concurrent guest writes or physical modem
behavior. The live board is unchanged and full reconstruction gates remain open.
