# ASPECT owned read window

The opt-in GET interpreter now uses the existing256-byte ASX read window as
its only read-ahead buffer. Its underlying stdio stream is set to `_IONBF`
before the first read. Previously stdio also allocated a heap buffer, leaving
insufficient near heap for a512-byte script-file buffer in the attached test.
The native window,8192-byte stack, six script slots,512-byte script buffers,
128 string globals and80-character values retain their capacities.

`ASPECT_FILE_OWNED_WINDOW` controls this change in `file_io.c`. The GET builder
enables it; the default reviewed interpreter does not. A failed `setvbuf` closes
the still-private stream and reports file IO failure. Successful opens publish
the handle normally. Refills continue to request data through the owned window;
tell/seek/EOF handling uses the same checked native prefix and logical offset.
This changes read-ahead allocation, not the ASX format or original opcode bytes.

## Diagnosing the previous failure

The earlier checkpoint incorrectly described runtime error7 as a heap error.
The source enum makes7 `ASPECT_RUN_OPERAND`; heap is8. Opcode65 is FPUTS, not
FOPEN. The original failing fixture attempted FPUTS after an unsuccessful FOPEN,
so its final error did not directly describe the first failure.

The new passive `--allocation-probe` reads symbol-bound child metadata at DOS
exit. On the old interpreter, backend open calls=0, native error=4 and runtime
error=7. The only non-state refusal before incrementing the backend open counter
is its512-byte `_nmalloc` request. After the change, backend open calls=1,
native error=0 and runtime error=0. The real file contains `BEFORE|LoC42`, the
stream is closed, and the script completes its serial exchange. The probe
reads product state; it does not invoke the allocator or modify the product.
Captured CRT heap boundaries are observational, not a general memory guarantee.

## Validation

[The receipt](validation/aspect-get-owned-window.json) binds source and artifacts:

- 113 host and218 DOS8086 file checks use the same72016-byte fixture. They cover
  real stdio, checked native reads, seeks, nested frames/returns and abort/longjmp.
- Six actual DOS parent/GET-child cases include FOPEN→GET→FPUTS→FCLOSE with
  exact file content, string/integer/long wire values, confirmed cancellation,
  float refusal and missing operands. Parent handles/history and return remain
  checked. The peer is a synthetic serial modem; no actual BBS is contacted.
- Seven full CLI DOS8086 cases retain128 strings,80-character values, mixed
  numeric/file ownership, healthy exit and typed errors.
- An isolated public-source rebuild reproduces the parent and child and replays
  the file, CLI and attached GET tests. Default interpreter bytes remain exact.

The attached pair uses the complete installed feature set plus capability22.
The separate heavier keymap parent still has an unresolved DOS EXEC8 startup
failure. Full variable/stream co-residency, ordinary8086 attached capacity,
repeated/EXECUTE GET, native WHEN actions, both GET compilers, other field modes,
FLOAT.RTE, package promotion and physical acceptance remain open. No selector,
installed files, hardware or private settings change with this checkpoint.

```sh
./tools/dev --command python standalone/check_aspect_file.py \
  --owned-window --output build/FRESH_FILE
./tools/dev --command python standalone/test_aspect_get_vm_dos.py \
  --parent-dir build/PARENT --child-dir build/GET_CHILD --output build/FRESH \
  --stream-probe --allocation-probe
```
