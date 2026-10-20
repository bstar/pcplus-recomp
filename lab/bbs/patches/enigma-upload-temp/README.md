# Per-upload temporary ownership experiment

The owned ENiGMA upload code uses one tracked `temptmp` session named `upload`
for every upload. Its normal cleanup therefore covers other uploads too. On a
receiver failure, the upload pipeline is not re-entered, so its partial file
remains until a later successful upload or process cleanup.

The separate DOS cancellation test reproduces the retained partial while
proving that the client can open an NFO, retry successfully and open the NFO
again. `check.js` additionally runs the actual upload methods with two real
temporary directories and reproduces shared cleanup deleting both owners.

`upload-temp.patch` gives each upload a unique tracked session, passes that
owner through protocol selection and returns it to the details pipeline. A
failed receive cleans that owner before returning its original error. Normal
details cleanup retires only that owner. A bare caller-supplied directory or an
untyped object is not cleanup authority. Upload billing release remains on its
existing path, including the synchronous-throw behavior.

`stage.py` refuses a running fixture, checks the original core files against
the owned board's fingerprints, and applies the patch only inside an isolated
candidate under `build/`. It records original and staged hashes separately and
freezes all selected upload-core inputs. It never changes the running board.

Prepare a fresh checked upload fixture, then use the pinned BBS environment:

```sh
./tools/bbs-dev --command node lab/bbs/patches/enigma-upload-temp/check.js \
  build/bbs-lab/NEW/candidate build/bbs-lab/upload-temp-unit/BASELINE
./tools/bbs-dev --command python3 lab/bbs/patches/enigma-upload-temp/stage.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs
./tools/bbs-dev --command node lab/bbs/patches/enigma-upload-temp/check.js \
  build/bbs-lab/NEW/candidate build/bbs-lab/upload-temp-unit/FIXED --fixed
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate --private-tmp
```

The fixed component test covers independent owners, repeated cleanup,
failure/success ordering, original error identity, free-time release, owner
forwarding and preservation of foreign directories. The matching upstream
checks must load `test/setup.js`; omitting that bootstrap leaves the logger
undefined in an unrelated ViewController test.

```sh
./tools/bbs-dev --command bash -c 'cd build/bbs-lab/NEW/candidate && node node_modules/mocha/bin/mocha.js test/{transfer_time_budget,client_end,view_controller_action_keys,mltev,fse_focus}.test.js --require ./test/setup.js --timeout 5000 --exit'
```

This is a staged experiment on the pinned owned revision. It does not prove
two simultaneous BBS connections, cleanup under filesystem errors, synchronous
protocol-spawn failure, upload carrier loss or physical modem behavior. It
does not change unrelated protocol-list temporary tracking. The keyboard
decoder experiment remains separate, and both live deployments remain open.
