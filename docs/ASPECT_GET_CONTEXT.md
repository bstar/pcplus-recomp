# GET context before operand parsing

The subsequent [command checkpoint](ASPECT_GET_COMMAND.md) adds foreground
confirmation ownership and actual final native abort/longjmp. Application
interpreter linkage and its cleanup guards remain open.

The optional `ASPECT_GET_CONTEXT` path now runs preparation and finish hooks
inside the native GET checkpoint. Preparation acquires an invisible parent field
and WHEN keyboard lease, captures current position/attribute/columns/logical rows/
viewport origin through existing capability21 INFO, then lets the recovered owner
read its operands. Configuration and presentation occur only when the owner calls
the field service. No new renderer capability or speculative geometry is needed.

The scalar aliases now address that context, the existing WHEN keyboard-disabled
state and the script-file mode scratch pointer. The native field service verifies
its requested position against the anchor before configuring it. Width0 never
calls that service: the finish hook explicitly retires its invisible anchor.
Operand-read aborts retain the anchor for matching-generation recovery before the
VM can discard abandoned frames. There are no retained destination/source pointers
in this ownership record; its independently linked far extent is now206 bytes.

Wrap is not derived from geometry. Each invocation requires an explicit checked
policy supplied before native entry. Invalid values disarm preparation, an
unarmed call refuses before any operand is read, and policy changes are rejected
while a native/field owner is active. The application still needs its real parent
policy binding. This API does not establish a guessed default.

## Shared scratch evidence

GET's original `4B06` read appears at overlay17/F2E3 in retained REA Evidence
`ev_048bc51f758f5883ec4e7e2b12ad78e9c95900e86c91ff4814b41bed0c726c36`.
Fresh REA of the exact overlay18 analysis image confirms FOPEN's EBCE owner
pushes the same pointer at EBF5, EBFE and EC06 before copy/lowercase/open. Its
complete dossier is `ev_16275dddb0f55061dc619264956d47f2c6c165ff95ad574e34c844196fe9c05b`;
analysis-image SHA256 is
`6cea4652377db36867cf1a663e8e0d7bbf0c296e3cb5c86dd67b6e442bb7a194`.
Both recoveries derive from original PCPlus SHA256 `6401ccfd…`. The ignored
local Evidence bundle retains the complete records; no proprietary binary or
analysis export enters public Git.

The new alias uses the maintained backend's existing
`runtime_script_file_mode_pointer`, whose81-byte static buffer already has a
script-file lifecycle. GET context does not clear it. That preserves a shared
role and retained-text behavior instead of creating an independent GET scratch.
The diagnostic supplies and seeds this owner, then poisons the old diagnostic
pointer to prove native GET uses the new symbol. An actual FOPEN→GET sequence
against the owned DOS backend, original startup allocation/reset behavior and
cross-script lifetime equivalence remain unverified.

Initial main-image reference searches found no direct initialized reference and
did not prove pointer allocation/lifetime. An overlay16 query was the wrong target,
and an overlay17 query resolved a different procedure. These are excluded from
the FOPEN claim; the matched overlay18 digest and exact EBCE dossier support it.
Synthetic analysis images were inspected only; none were executed.

## Acceptance and limits

[The receipt](validation/aspect-get-context.json) records actual DOS8086/FPU-off
context execution through the recovered owner, typed readers, integer CRT,
native field ABI and serviced editor/WHEN/client:

- 137 frozen cases match the original observations.
- One original25-row case clips to five characters using the captured24-row
  parent view. Its edited result and cursor remain correct; its field width is
  an explicit context change.
- Four reserved-view cases refuse without consuming keys or changing the
  destination. Row24 rejects before operands; a row23 wrap-enabled overrun
  rejects after operand parsing, with matching ownership cleanup.
- Extra probes cover invalid/unarmed policy, rejection of live policy changes,
  the poisoned old scratch alias and an origin52 edit. The latter reads physical
  position and verifies the original owner adds52 in its final adoption call.
- A36-source isolated rebuild reproduces the exact executable and full report
  without originals, private data, prior objects or ancestor Git.
- The non-context serviced owner still passes137 matches plus5 protected-view
  refusals. The independent editor/heap suite still passes759 checks with its
  exact20-source reproduction. Default and checkpoint-only diagnostics remain
  byte-identical to their preceding reviewed binaries.

The parent display, BIOS keys, serial, native WHEN actions, final cursor operation
and confirmation/final abort boundaries remain modeled. The native operand FILE
is the existing synthetic buffered stream. Float conversion remains opaque.
The real script-file backend is not linked into this diagnostic. This does not
verify a complete interpreter, live parent parser, child handoff, real UART/BBS,
application capacity/package or physical machine.

Still required are full-interpreter linkage and budget checks, caller policy and
actual FOPEN/scratch lifecycle integration, foreground confirmation cleanup and
final native abort propagation, real parent parser/receive tests, FLOAT.RTE,
both compiler grammars/opcode49, raw console support, connected scripts and
physical acceptance. Application GET remains disabled; the selected payload and
installed files are unchanged. No FTP/card/modem/SIP/BBS state was touched.

```sh
./tools/dev --command python standalone/build_aspect_get_owner.py \
  --checkpoint --serviced --context --output build/my-get-context
./tools/dev --command python standalone/prove_aspect_get_owner.py \
  --build build/my-get-context --output build/my-get-context-source
```
