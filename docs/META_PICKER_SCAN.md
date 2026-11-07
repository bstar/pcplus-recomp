# DOS enumeration for the Meta Keys picker

The serviced picker can now collect a real DOS directory incrementally, using
its own find context. It preserves the caller's DTA, default drive and per-drive
working directories. It remains a separately tested component; the interactive
parent and installed application have not changed.

## DOS and ownership boundary

`meta_picker_scan.c/.h` supplies near-cdecl, DS=SS begin/step/cancel operations
with 130 bytes of explicit caller-owned far state. The picker retains its own
20-byte far state and 9,009-byte far name table. Begin validates and freezes an
explicit absolute ASCII DOS83 `*.KEY` pattern without doing IO. Case/slashes
are normalized; relative paths, devices, dot components and other wildcard
forms are refused. The 53-byte parent bound matches checked KEY replacement.
This is lexical validation, not canonical resource identity or file admission.

Each step performs at most one DOS FindFirst/FindNext, or at most 64 sorting
comparisons. The find continuation is copied between far state and a temporary
near DOS buffer. There is no shared global find context. Interleaved DOS searches
can therefore use another context between picker steps.

`meta_scan_fs.c/.h` saves INT21/AH2F's current DTA before each Watcom find call
and restores it with AH1A before returning, on success and error. Watcom's
near-data find routines otherwise leave the DTA pointing at their supplied find
buffer; restoring it also prevents a pointer to the adapter's temporary stack
buffer from escaping. No directory change, file-content access or open DOS file
handle is involved.

Readonly/archive entries are eligible. Hidden/system/directory/volume entries
are excluded; the returned name must be a terminated DOS83 KEY filename. ASCII
stem characters are checked and high CP437 bytes retained. The picker receives
the stem with its case preserved. DOS error 18 means normal end of enumeration;
other errors latch FAILED and retain the native error. Malformed results also
fail. Enumeration failure or cancellation leaves the partial list unsealed and
unselectable through the picker API. Cancellation during sorting similarly
keeps it inactive.
The owner must discard/reset the partial state.

Collection stops at 1,001 accepted names and records `limit_reached`. This means
the scan stopped at its cap, not that an extra file was observed. The diagnostic
supplies 1,002 matching files to exercise that outcome. There is no external
lock or snapshot of the directory; concurrent changes remain possible.

## Verification

```sh
./tools/dev --command python standalone/build_meta_scan.py \
  --output build/NEW-meta-scan
./tools/dev --command python standalone/prove_meta_scan_source.py \
  --build build/NEW-meta-scan --output build/NEW-meta-scan-source
```

The source-built DOS8086 test passes 137,372 assertions over owned scratch files.
Many assertions check the DTA sentinel bytes after every step; this count is not
a count of independent scenarios. The test verifies real enumeration, ordinary
files and readonly entries, exclusion of a KEY-named directory, ignored TXT
files, empty and missing directories, case/slash normalization and the capacity
outcome. It interleaves another real FindFirst/Next search, alternates the caller's
DTA buffers and checks their pointer and all 128 sentinel bytes. The default
D:\KEEP and C:'s separate C:\ALT directory are unchanged.

Six explicit test modes wrap real DOS calls: first/next errors, incorrect
extension, unterminated name, an ineligible attribute and an invalid stem. The
attribute case exercises filtering; the others prove partial-list failure.
Cancellation in both collection and sorting, terminal-state refusal, invalid
patterns/segments and external count mutation are checked. No fault is presented
as a real hardware failure. All 1,009 fixture files retain their exact bytes.

The far table lies outside DGROUP and DS=SS is checked at runtime. Object
inspection verifies zero data/constant bytes in the scanner and its DOS adapter;
new scanner-owned literals do not consume the parent's nearly full DGROUP.
The shared path-validation helper and application integration still need their
own memory admission. This is not a parent capacity result.

An isolated 16-file export reproduces the executable and all results without
original executables, private files, prior objects or ancestor Git. The outer
pinned Nix environment supplies tools. The
[receipt](validation/meta-picker-scan.json) binds the accepted source and product.
These tests use maintained source and actual DOS operations, not an original
binary comparison.

## Remaining work

The application owner must supply resource search (current directory and PCPLUS
fallback), canonical identity/claims, file/EXEC admission and modal/frame lifetime.
It must coordinate selection with checked load, original missing-file default
creation, baseline reconciliation, recovery/quarantine and live adoption. The
scanner is not a substitute for those policies. Full UI/cursor restoration,
foreground/UART scheduling, application memory/capacity and BBS/physical acceptance
remain open. Installed RCE81708 is unchanged; no full-parity gate is closed.
