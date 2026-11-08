# Experimental GET display RPC

The subsequent [GET status policy](ASPECT_GET_POLICY.md) adds optional
capability22 and checked STATUS_HIDDEN/STATUS_ROWS metadata. Capability21 and
the reviewed capability20 application remain separate profiles.

The optional `ASPECT_GET_DISPLAY` build publishes renderer capability21 in both
parent and child. The default reviewed capability20 payload is unchanged. This
is an interface checkpoint: GET opcode49 remains unavailable in the maintained
compilers/interpreter, and no installed files or package selectors are changed.

Requests21..26 correspond to the six [field controller](ASPECT_GET_DISPLAY.md)
operations: begin, configure, stage, present, info and close. The parent checks
PSP, DS, published descriptor, main child MCB, client magic/version/token and
unchanged callback identity on every attached request. A rejected request cannot
acknowledge ownership retirement. Field work requires a live serial handoff;
explicit error close remains available after serial return. The requests neither
acquire UART ownership nor invoke a child callback.

BREAK notice, KEY, PROGRAM begin, window service, confirmation and EMULATE refuse
while a field is owned. Actual BREAK ownership also excludes field admission.
Ordinary parent parser output remains possible; the field must be repainted by
its eventual serviced editor. Parent prepare/revoke retires stale private field
ownership without entering a retired child. Invalid foreign display contexts
are preserved during error retirement.

Explicit error-close and END responses use `E000|status` to acknowledge retirement
even when display cleanup fails. Plain errors, zero or malformed tags cannot
falsely release the child's owner. Info uses `F000|byte`. Child-side callback
and nested-request guards prevent a callback from re-entering an in-flight field
transaction. A failed post-request client validation quarantines the local owner
until a checked retry; it does not pretend cleanup succeeded.

## Evidence and limits

[The receipt](validation/aspect-get-rpc.json) records:

- 35 CPU replays of the actual full parent bridge, allocation validator, field,
  adapters, native cursor and parser, with modeled BIOS/DOS PSP/UART hardware.
  No child callback executes. Register/FLAGS preservation, IF/DF behavior,
  authentication mutations, owner conflicts and retirement are checked.
- 271 DOS8086/FPU-off child-client checks against controlled parent responses,
  including error tags, callbacks, nested calls and quarantine/retry.
- A clean 752-input public-source export reproducing both diagnostic binaries
  and complete reports without prior objects, originals or ancestor Git.
- 103 DOS field/video cases and805,134 checks, including255 nonzero CP437 bytes;
  the additional check covers BREAK ownership. Its nine-input source export
  reproduces the exact diagnostic and report.
- A complete experimental ASPECT interpreter link with capability21. This is
  compile/link evidence, separate from the independent bridge/client tests.

The parent replay permits only the existing four-instruction video-DS borrow in
BREAK's packed-cell reader; the new field requests permit no foreign-DS span
while IF is enabled. The native reader neither accesses stack nor calls a child
inside that borrow. This is not a blanket claim about all legacy routines.

The experimental parent requires480,944 allocated module bytes plus its256-byte
PSP; the reviewed parent requires479,408 plus PSP. DGROUP remains65,520 bytes,
with the existing63,000-byte history and redisplay snapshot capacities retained.
Whole parent/child runtime capacity and package admission remain unverified.

The subsequent [native checkpoint](ASPECT_GET_CHECKPOINT.md) separately proves
GET stack restoration. Its field/WHEN cleanup integration remains open.
Actual child EXE-to-parent GET execution, field buffer
and destination lifetimes, serviced receive/repaint composition, FLOAT.RTE,
both compiler grammars/opcode49, connected scripts and package/memory/physical
acceptance remain open. No live serial, BBS, SIP or physical machine was probed.

```sh
./tools/dev --command python standalone/check_get_display_bridge.py \
  --product build/my-capability21-parent --output build/my-bridge-check
./tools/dev --command python standalone/build_get_display_client.py \
  --output build/my-field-client
./tools/dev --command python standalone/prove_get_display_bridge.py \
  --bridge build/my-bridge-check --client build/my-field-client \
  --output build/my-field-source-proof
```

Build the parent with the reviewed terminal recipe's flags and
`--aspect-get-display`. The experimental process builder accepts
`get_display=True` only with its EMULATE/snapshot prerequisites. Packaging still
rejects this unreviewed capability; no connection candidate is promoted here.
