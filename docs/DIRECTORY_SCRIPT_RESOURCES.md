# Directory script resource preflight

The opt-in `--directory-scripts` application adds script resolution and a
whole-file fingerprint to the existing KEY/KBD/XLT transaction. It implies
`--directory-translation`, retains the LoC.6 splash, and uses disconnected
preview R / PROGRAM kind 6. It does not execute a script, compile source, adopt
the selection or dial.

```sh
./tools/dev --command python3 standalone/package_special_edition.py --build \
  --custom-irq --directory-scripts --output build/scripts-package
```

The directory's existing nine-byte script field passes the same strict name
validator as selection decoding. Blank fields stage no script. Bare names try
ASX in CWD, ASX in PCPLUS, ASP in CWD, then ASP in PCPLUS. Qualified names do
not gain an environment fallback. An unavailable or malformed PCPLUS variable
supplies no fallback, matching the current interpreter helper. An existing
compiled candidate with a bad header, a directory or an IO failure does not
silently choose a source instead.

All resource identities resolve before the first content open. The shared
reservation includes the selected script identity. The reader uses existing
checked near/far DOS adapters, non-inheritable handles and 256-byte reads. It
streams a 32-bit byte count and CRC32/IEEE over every byte, including the compiled
header. There is no 64 KiB file restriction; signed 32-bit file-position limits
match the interpreter. A compiled candidate needs a first byte at most 128.
That is the loader's header check, not complete bytecode validation. A source
candidate is explicitly kind SOURCE, including an empty file whose eventual
compiler must report any language error.

An open/read/header/close or release failure preserves the complete far bundle.
A close uncertainty retains its actual handle number and canonical claim; the
owner refuses EXEC, reset and retry. The diagnostic separately checks the cases
where the kernel handle remains open and where it has already closed. A test
child deliberately bypasses the refused product EXEC gate to prove that the
still-open script handle is not inherited.

The script extension adds only a canonical path and a 12-byte fingerprint to
the bundle, taking it from 1,948 to 2,024 bytes. The resource snapshot grows from
206 to 272 bytes. The exact actual-session snapshot/seals follow at frozen
6,002 through 6,700; page/proposal offsets and both history capacities remain.
No script body is held in that bundle. CRC32 detects changes, not authenticity;
it fingerprints the observed stream and does not lock an external writer or
prevent a later namespace replacement. Adoption/execution must retain and check
this identity/fingerprint before using the script.

The [receipt](validation/directory-script-resources.json) binds the exact application,
component, proofs and tests. The component uses real DOS IO with explicitly
identified fault adapters and a separate Python zlib CRC oracle. It covers
98,305-byte files, partial reads, every lookup level, qualified/absolute names,
bad/empty compiled headers, source and empty-source candidates, noninheritance,
claim conflicts, CWD drift, argument aliases and preservation of an earlier
bundle after a later failed selection. Authored scripts contain a file-write
marker; preflight must never create it.

Application tests run actual DOS8086 COM3/IRQ5, with a passive observer checking
quiesced DOS boundaries and non-inheritable opens. New script cases execute a
real ASPECT child that changes CWD before preview, then compare the canonical
path and complete fingerprint independently. Existing active configuration,
keymap, translation and logical selection fields remain unchanged. Kind 6 bypasses the child-only capture-close step in this variant. Independent
capture stays open; a capture of the selected script refuses before content
reads while preserving the capture handle and the entire prior bundle.

Source compilation before adoption, reserving compiler output, checking the
fingerprint at launch, publishing the selected entry/active resources and
canonical script identity, and dialing remain open. Stock ENiGMA evidence checks
server interaction and selected final screen markers, not a complete independent
character/attribute oracle. Full F01–F16, physical Boca/SPA2102 and card acceptance
remain open. No live bridge, BBS, network adapter or card is changed by these tests.
