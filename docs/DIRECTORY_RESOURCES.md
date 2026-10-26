# Directory KEY/KBD resource staging

Live selection needs to distinguish original `/K` and `/T` overrides from files
chosen for the previous directory entry. Startup currently augments
`terminal_option_mask` with the latter, so reusing that mask would incorrectly
pin the old board's resources. `directory_resources_stage` instead requires an
explicit original CLI mask and previously bound absolute CLI paths. The later
[CLI integration](DIRECTORY_RESOURCE_CLI.md) captures that provenance in an
opt-in application variant; the unchanged LoC.6 build still lacks that capture.

The new component reads and validates both resources into a proposed bundle
before publishing any of it. A missing or blank directory binding resets the
corresponding defaults; it cannot inherit the old BBS's selected bytes. This is
a prerequisite for selection adoption, not a new terminal release. LoC.6 still
offers directory preview without live adoption.

## Lookup and ownership

The request retains the selected raw114-byte record, profile4/6, original CLI
mask, PSP and two previously bound CLI paths. Both stored names are validated
even when overridden. Directory KEY and META basenames select `.KEY` actions
and `.KBD` keyboard tables, respectively.

Directory lookup checks the current directory, then the bounded `PCPLUS`
environment directory. A named missing META retries `PCPLUS.KBD` through the
same search. Blank META does not request that fallback. Missing explicit CLI
files, malformed resources and operational lookup errors fail; they do not
silently select another resource. Defaults are the caller-supplied validated
948-byte keyboard and ten disabled(kind3) action records.

Every present resource gets an uppercase, absolute DOS83 identity, at most63
bytes, before content IO. Attribute inspection uses no file handles and accepts
read-only files. Both identities enter the shared registry before the first
read. Capture, snapshot, monitor, history, fixed recording claims and a different
dynamic reservation can refuse before any content handle opens. The readers
then use those same absolute spellings, including after CWD changes.

The opt-in `KEY_RESOURCE_PRIVATE_READS` builds both strict readers with DOS3+
`O_NOINHERIT`. Existing builds retain their previous behavior and exact bytes.
Close uncertainty keeps both claims, refuses reinitialization/further staging
and makes the pure EXEC admission predicate refuse. A failed release likewise
retains ownership. There is no force-reset or retry-close path. The future
application owner must wire this predicate into its actual EXEC gate.

Only complete reads, schema validation, successful closes and a successful
claim release allow the entire1,624-byte far bundle to be published. Failed calls
preserve an existing bundle. The inspect-only owner snapshot is142 near bytes;
the request is248. No extra persistent keyboard/action buffer is introduced.
The bundle's publication is not interrupt-atomic; the caller must own a stable
output lease and the UART quiescence boundary.

## Verification

The [receipt](validation/directory-resources.json) records36 actual DOS8086
workflows and1,757 assertions, with independently constructed exact bundle bytes:

- Local/environment lookup, named META fallback, explicit CLI profile6, blank
 and missing defaults, and read-only resources preserve raw after-NUL bytes.
- Invalid defaults, binding syntax, relative CLI paths, profile, near/far spans
 and physical far aliases fail without mutating caller data.
- Malformed KBD slots, missing profile blocks, invalid KEY kinds, suffixes,
 metadata/canonical/open errors, directories and long canonical paths preserve
 the output. A failed second selection preserves the previously staged bundle.
- Conflicts cover all four binary sinks, both fixed recording resource names
 and an existing dynamic owner, with no content opens on refusal.
- Injected close failures cover both physically closed and still-open handles.
 A real DOS child cannot read the latter handle while its parent can still read
 it. This deliberately bypasses the diagnostic's refused admission predicate
 to verify DOS noninheritance separately; it is not a product launch path.
- A successful second selection with blank bindings replaces previous imported
 bytes with defaults. All source resource files, CWD decoys and the42-byte
 hardware snapshot remain unchanged.

An isolated35-source export of committed source `0c35362`, without Git or
original files, reproduces the diagnostic and all15 objects, then repeats those
36 DOS workflows. Ordinary and
LoC.6 current-source terminal builds remain byte-identical to their accepted
products. These source changes do not alter the card or running services.

Run with the pinned Nix toolchain:

```sh
./tools/dev --command make test-directory-resources
./tools/dev --command python3 standalone/prove_directory_resources.py \
  --output build/directory-resources-proof-UNIQUE
```

Remaining integration includes original CLI identity binding, accepted PRM
freshness, a lease spanning popup release and the PROGRAM owner, translation
and script resources, old-selection accounting, actual UART/profile adoption
and dialing. Same-process DOS names are not external-writer locks, host inode
identities or protection against drive remapping. Broader application, BBS,
transfer and physical acceptance remain open.
