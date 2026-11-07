# Checked Line/Port prefix persistence

The optional [live Alt-P candidate](LINE_PORT_LIVE.md) now composes these components
and passes the named application gates. The installed/default release is unchanged;
this document retains the separate component checkpoint and its limits.

`src/line_port/persist.c` now performs an actual checked save of the native
five-word line-settings prefix. The optional live candidate calls it through bank-local DOS boundaries.
The [staged popup transaction](LINE_PORT_SESSION.md) has separate component
coverage; broader application composition gates remain listed in the live report. Installed RBADE091 is unchanged.

The caller supplies an absolute DOS83 PRM identity, the ten bytes accepted when
the edit began, and the requested replacement prefix. The caller must hold the
canonical file claim. The storage function derives same-parent `PCPSTG.$$$` and
`PCPBAK.$$$` names using the existing checked path code. Existing recovery names,
read-only/missing targets, traversal/devices and invalid/overlapping arguments
are refused. It never creates a missing target or truncates an existing target.

The algorithm opens the original read-only and exclusively creates its stage.
It compares the accepted prefix, then streams exactly 1264 bytes, replacing only
the first ten and preserving every remaining byte. Short/oversized originals,
read errors, short writes and close errors prevent installation. Both source
and stage must close successfully before the original is moved to backup and
the stage installed. Failed installation attempts rollback; failed rollback
retains both recovery copies. Uncertain close prevents deletion/rename of a
potentially still-open stage. Cleanup errors retain their flags and artifacts.
Callers must inspect installed, stage, backup and close/rollback flags even if
the primary status names an earlier failure.

The storage function does not validate the semantic line values; the staged
serial plan supplies that validation. It does not bind the startup identity,
register the file claim, update the live-setup baseline, apply serial settings,
display recovery details or retire an uncertain file handle. Those remain
foreground integration requirements. File attributes/timestamps are not
preserved. FAT power loss and external concurrent namespace/data changes are
outside this transaction's guarantee.

## Accepted evidence

[The receipt](validation/line-port-persistence.json) binds source and output:

- **28 real DOSBox-X8086 checks** execute the actual persistence algorithm and
  DOS filesystem calls on authored files. Host-side readback compares all 1264
  final target bytes with the exact requested prefix patch and verifies short,
  oversized and read-only fixtures remain byte-identical. Success leaves no
  recovery names or accidentally created missing target.
- **37 checks at explicit filesystem boundaries** execute the same algorithm
  with authored faults: inspection/open/create/read failures, exclusive-create
  conflict, fragmented reads, failed/short writes, source/stage close errors,
  failed original move, failed installation with successful/failed rollback,
  cleanup failure, stale prefix, exact-size enforcement and existing recovery
  names. They inspect original/stage/backup contents and ownership flags.
  These injected errors are not observations of a failing physical disk.
- A ten-file isolated public-source export rebuilds both EXEs exactly and
  repeats all real/fault checks with an identical complete target output. It
  includes no original, private configuration, analysis database, previous
  object or Git metadata. The outer pinned Nix environment supplies tools.

```sh
./tools/dev --command python standalone/test_line_port_persist_dos.py \
  --output build/NEW-line-port-persist
./tools/dev --command python standalone/prove_line_port_persist_source.py \
  --receipt build/NEW-line-port-persist/result.json \
  --output build/NEW-line-port-persist-source
./tools/dev --command python standalone/record_line_port_persistence.py \
  --receipt build/NEW-line-port-persist/result.json \
  --proof build/NEW-line-port-persist-source/result.json
```

Both producers require fresh output directories.

## Live memory and integration constraints

The current exact parent `856a9c85` uses 65504 DGROUP bytes, leaving 32, and
65460 resident code bytes, leaving 76. These figures come from the actual
candidate's linked memory manifest, whose hash is bound in the receipt. The
native selector adapter adds 12 data bytes; simply adding the 28-byte popup owner
would already exceed the remaining near-data space. The front end therefore
needs far-bank state with bounded DS=SS stack snapshots when it calls the
verified near-pointer session/plan APIs. The diagnostic's 64KiB separation pad
must never be linked into the application.

The existing PROGRAM handoff is the route for actual serial commit. A distinct
internal operation must skip child EXEC and unnecessary acknowledgement while
preserving drain deadlines, flow release, IRQ/vector restoration, carrier gates,
custom COM/IRQ checks and DTR. New port/framing values must not publish before
all required validation and the save result are known. A successful saved prefix
followed by apply failure must remain visibly saved and must not be rewritten
implicitly on retry. Uncertain persistence must retain the file claim and
recovery information through retirement rather than silently reopening.

After wiring these owners, exercise direct/browser/reference Alt-P, connected
incoming data and terminal replies, modal restoration, Escape/Alt-S, no-op and
port reselect, busy/fault/refusal and carrier-loss paths in the exact application.
Package reproduction, Enigma/Synchronet regressions and physical modem testing
remain separate gates. No application or hardware parity gate is closed here.
