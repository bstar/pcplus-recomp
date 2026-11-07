# Meta editor production service bindings

The Meta bank now uses the parent's actual service conventions, and the optional
`--meta-services` parent build links its new adapters successfully. Both bank
workflows and a complete parent source rebuild pass. The matched loader, Alt-M,
modal ownership and live action adoption remain unimplemented; this parent build
does not expose the editor and has not been installed.

## Binding and memory results

The bank reuses seven existing far callbacks: six near-memory/string CRT services
and canonical path resolution. It marshals the latter's two cdecl near pointers
into the parent's AX/DX register ABI. Renamed CRT calls preserve ES explicitly.
Four authored far-memory routines live in the bank, avoiding new resident CRT
wrappers; they preserve the generic Watcom ABI, including the fifth stack count
and `RET 2` for copy/compare. All routines retain DS=SS on return.

The installed Line/Port parent does **not** enable the optional directory service
exports visible in the repository source. An audit of its exact MZ caught that
incorrect assumption. `meta_bank_resident.asm` therefore adds independent Meta
adapters for existing path validation and strict KEY reading (20 bytes each),
plus the attributes register bridge (4 bytes). `meta_bank_resource.asm` adds a
20-byte adapter to the existing PCPLUS environment resolver in CONFIG_CODE.
The resident KEY reader uses this selected parent's ordinary build flags; the
in-bank comparison/staging backend keeps its private deny-write opens.
The bank binding is `meta_bank_runtime.asm`; the earlier generic diagnostic
binding remains available as a control.

The actual full parent links **44 additional resident code bytes** and **32
CONFIG_CODE bytes including alignment**, adding **64 bytes** to minimum retained
memory. The resulting minimum is 479,088 bytes. Resident code has 512 bytes spare;
CONFIG_CODE has 2,305 spare; DGROUP still has 16 spare. Receive/history, stack,
snapshot and far-storage capacities are unchanged. These facts replace the
previous assumption that the selected parent had no resident code space.

The product bank's calculated aligned payload is 21,619 bytes, with zero DGROUP
additions and unchanged 12,870-byte caller state. Diagnostics include extra test
code and use three separate code segments with a deliberate 64KiB gap from
resident code. Their larger bank sizes are not the product payload limit.
The proposed snapshot layout remains only a capacity calculation, not an arena
lifetime or loader acceptance gate.

## Evidence

- Each production-binding workflow passes 35,332 copy/fill/compare/string checks
  against independently compiled resident Watcom CRT routines. Tests cover
  guarded spans, zero lengths, four offsets, lengths through 255, unsigned byte
  ordering and CP437 values. These are byte/assertion counts, not user scenarios.
- Each also passes 166 kernel/ABI/DTA checks and 3,069 editor workflow assertions.
  The injected session adds 981 fatal-owner assertions.
- An isolated 56-file source export reproduces both bank diagnostics exactly and
  repeats their checks without originals, private data, old objects or Git.
- Seven existing deployed-parent callbacks and four new adapters have exact
  near-call/RETF instruction checks; 22 invalid variants are rejected. The four
  new adapters are checked again in the actual full parent (eight more invalid
  variants). No corrupted image is executed.
- A 707-file public source export reproduces the complete opt-in parent and its
  matched PCLINE.OVL exactly, then passes four actual DOS synthetic-peer cases:
  save, serviced traffic, read-only refusal and port-busy recovery.
- With `--meta-services` disabled, the parent remains exactly SHA-256
  `ff6bb369a8b3693cefc357fec901ae576139cafe8915f8e60818ddcdde2e5399`.
  The preceding generic bank diagnostic is also byte-identical.

The full parent build exposed a stale compiler-size source digest for the
`KEY_EDITOR_FS` test-only conditional added in 73d58b0. Its reviewed digest was
refreshed after confirming the optimized reader is still 611 code bytes with no
data and the disabled parent EXE remains identical. The deployed manifest's older
reader/profile sources are verified against matching public Git blobs, rather
than represented as current source.

See [the receipt](validation/meta-parent-services.json). Use fresh labels:

```sh
./tools/dev --command python3 standalone/build_meta_editor_bank.py --direct --parent-services --output build/meta-parent-direct-LABEL
./tools/dev --command python3 standalone/build_meta_editor_bank.py --parent-services --output build/meta-parent-fault-LABEL
./tools/dev --command python3 standalone/prove_meta_editor_bank_source.py --direct build/meta-parent-direct-LABEL --fault build/meta-parent-fault-LABEL --output build/meta-parent-source-LABEL
```

`build_terminal.py --meta-services` enables only the parent adapters; it is not a
Meta editor launcher or a deployable feature-parity package. Existing package
recipes/selectors remain unchanged. Next is the matched transient loader with
exclusive arena ownership, followed by menu/direct Alt-M, admitted internal file
work and checked live-table adoption. HELD/FATAL claims require keeping bank code
and state alive until DOS exit. Connected Enigma/Synchronet and physical modem
acceptance remain separate gates; installed RCE81708 is unchanged.
