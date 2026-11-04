# Full-height status visibility and bounded status writes

Normal Ctrl-] and the existing reference/browser Toggle Status command now work
with coherent25/28/43/50-row layouts when both the large shared frames and
PROGRAM display owner are composed. Small-frame builds retain the25-row gate.
The existing offline-only policy remains: tracked connections refuse a change;
busy parser, transfer, child, recording and modal owners retain their prior
deferral/refusal behavior. Toggle Lines and startup preference application are
not enabled by this checkpoint.

## Full-height transaction

The maintained transaction now derives physical cells, effective logical rows,
status coordinates, scroll threshold and shadow bounds from the accepted height.
Canonical fields and BIOS must agree before loans or mutation. Its three existing
exclusive frame loans save all admitted physical cells, rather than only2,000.
Their larger capacities are already validated by the source-built memory checker.
No persistent buffer or near-data allocation was added.

Hiding clears and admits the former reserved last row into terminal addressing.
Showing contracts the logical area, follows default margins while retaining
representable custom margins, performs the real native scroll when needed and
clamps live/saved cursor rows. Captured RIS defaults follow both sizes. Failed
native rendering restores all captured video, canonical planes, line flags,
defaults and hardware cursor, including physical rows beyond25. Queued UART input
remains owned by the real receiver until foreground parsing resumes.

## Status string write boundary

Full8000-byte rollback checks found a pre-existing write the earlier4000-byte
tests missed: a legal native status format contains81 bytes, and the native
string writer places its last blank into the next physical row/page. On failure,
the old rollback restores only the admitted physical area, leaving that cell
changed. Merely enlarging the rollback buffer would leave normal draws crossing
their row boundary.

The maintained CONFIG bridge now copies at most the remaining physical columns
into a bounded near stack string before forwarding through the existing checked
near/far adapter. Invalid widths or a column outside the width return status3
before writing. The original81-byte formatter result, recovered drawing helpers
and native text writer remain intact. Visible bytes are retained; the invisible
overflow is no longer written. The copy uses a134-byte stack buffer and no static
data. The memory checker still validates the original resident adapter and the
forwarding call/relocation at its new CONFIG entry.

This is an explicit maintained write-boundary correction, not a claim that the
genuine original had the same clipping policy. Synthetic132-column addressing
checks exercise the adapter only and do not establish a supported BIOS mode.

## Evidence

The [receipt](validation/large-status-control.json) binds exact images, public
sources, raw captures, checkers and isolated rebuild proofs.

-111 linked inputs cover all heights and profiles4/6, normalized direct keys,
 reference-frame return, genuine size/CPR and RIS, default/custom scroll bounds,
 bottom-row live/saved cursors, complete frame/plane/history canaries, queued real
 UART input, hidden Pause/Auto Answer refusal and their visible-row admission.
 Pre-render and post-draw failure cases restore the complete snapshot. Online,
 busy-owner, bad BIOS/geometry and unrepresentable-margin requests refuse. Three
 additional cases within that count establish that the small-frame image refuses
 coherent28/43/50-row layouts before acquiring a frame loan.
-48 baseline/candidate CPU inputs execute the string bridge and real native
 writer with80/132 synthetic columns, two row positions, first/last/outside
 columns and empty/full-byte strings. The preceding accepted image deliberately
 demonstrates cross-row writes. The candidate clips or refuses them while
 retaining the callee-cleaned stack and native visible bytes. Full16KiB video
 canaries and register/IF/DF checks are retained.
-Current existing status transaction, normal-control, small-frame transaction
 and live-render regressions pass on the final images. Earlier scoped tests are
 not used as acceptance evidence for an image whose bridge later changed.
 The old live STATUS checker now honors explicit terminal/output arguments and
 checks a coherent hidden-row fixture; a separate case rejects its former
 inconsistent hidden flag/visible bounds. Its initially ignored-argument run
 against a default image is excluded from this checkpoint.
-Six actual DOS8086 application workflows cover the ordinary parent, all four
 startup-height diagnostics and the small-frame parent. Real BIOS Ctrl-] and
 Alt-Z selection produce `(physical-1) → physical → (physical-1)` size and CPR
 replies. An owned peer writes `EXPOSED` on the last logical row at each stage.
 A passive timer captures two full frames while that text occupies the newly
 exposed physical last row. The final8000-byte capture places the text on the
 returned last logical row and native status on the last physical row.
-Nine actual DOS8086 renderer cases retain the original81-byte formatter fixture
 while comparing its first80 visible characters, emphasis, eight key labels,
 alternate/message/hidden output and three typed formatter failures. All4004
 sampled bytes are checked, including four unchanged canary bytes after the
 physical row. The standalone DOS checks retain ABI/stack guards.
-Independent artifact verification passes the six application workflows,
 12 exposed-row frames,18 exact area reports and nine renderer cases. It rebuilds
 each passive observer, compares exact wire replies and used fixture bytes,
 verifies raw final body/status placement, hardware restoration and renderer
 canaries. Actual injected rollback failures remain CPU-model evidence.
-Six isolated source-only parent rebuilds reproduce exactly: five569-source
 composed images and one567-source small-frame image. Startup-height diagnostics
 remain rejected by application staging.

The ordinary internal candidate is SHA256
`baaff639d995f791ea8613e02544f2a14d316e281b96a57f9366086c52f72f1b`.
Near data/stack remains65,120 bytes and resident CS65,500 bytes (36 spare).
CONFIG grows59,537→59,728 bytes. Height diagnostics retain12 resident bytes spare.
The small-frame image uses65,088 near bytes and65,470 resident bytes. Further
resident additions still need banking. Original splash, UART/protocol engines,
typed modem readiness and private configuration were not changed.

## Reproduction and remaining work

Use the pinned `./tools/dev --command` environment and receipt flags to build fresh
parents. Run `standalone/check_large_status_live.py --terminal ORDINARY
--small-terminal SMALL --output build/NEW`, the existing status/control tests and
`standalone/check_status_string_bounds.py` against the preceding accepted baseline
and the new ordinary parent. Rebuild and run the standalone status renderer before
checking its canaries. Use `standalone/prove_terminal_variant.py` for isolation.

```sh
./tools/dev --command python standalone/test_status_control_dos.py \
  --terminal build/NEW/50/TERMINAL.EXE --rows 50 --label new-status-50
```

Use fresh output directories and repeat at other heights and both ordinary and
small-frame parents. The independent checker accepts those six reports and the
standalone renderer report. The receipt gives exact accepted paths and hashes.

Normal Toggle Lines/startup selectors, live setup/HOOK adoption, tracked-online
resize and bridge NAWS coordination remain open. The serial tests use an
untracked loopback fixture and do not establish live BBS resizing. Owned Enigma/
Synchronet, physical Cirrus/mouse/Boca/SPA2102 and full application parity remain
separate acceptance gates. No physical DOS files/card, selected package, private
settings/call history, installed bridge/BBS/service or networking changed.
The full goal remains active.
