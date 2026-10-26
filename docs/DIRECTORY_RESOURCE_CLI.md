# Original CLI resource identities

The opt-in `--directory-resource-cli` application variant captures original
command-line provenance before the directory chooser, startup editor or selected
entry can affect active settings. This closes the distinction needed by
[KEY/KBD resource staging](DIRECTORY_RESOURCES.md): a directory-derived binding
must not become a permanent `/K` or `/T` override on the next selection.

This variant retains the LoC.6 UI/version. It does not yet connect staged
resources to the live directory adoption/UART owner, and is not deployed to the
card. The ordinary and LoC.6 application products remain byte-identical.

## Startup and request contract

After successful option parsing, main calls the actual far startup adapter and
checks its status before `terminal_select_directory`. The adapter saves all
original CLI mask bits and resolves explicit `/K` and `/T` to uppercase absolute
DOS83 names, at most63 bytes. Both resolutions must succeed before either active
selector changes. Canonicalization does not open/probe resources; subsequent
strict startup readers still decide whether files exist and have valid schemas.

The138-byte inspect-only snapshot has once-only DATA-cookie initialization.
Initialization never clears a bound or failed attempt. A second binding refuses
without changing original flags, paths or history. An invalid source span fails
before starting a bind; canonical/path failures record FAILED without publishing
partial identities. The actual adapter reports keyboard/action error9/10 for
the corresponding failed resource.

The pure near-cdecl request factory copies the selected114-byte record, supported
profile4/6, actual PSP and only the two original resource-mask bits into the
248-byte staging request. It gets paths from the bound snapshot, independently
of subsequently augmented active flags or selectors. It neither reads files nor
changes the active session. Invalid profile, PSP, spans or aliases preserve the
whole output. Stored binding syntax remains the strict staging API's decision.

Explicit CLI resources therefore retain their initially bound identities after
CWD changes. Directory-derived resources still use the selected entry's normal
CWD/environment search; missing explicit files cannot silently become directory
bindings. Canonical DOS names do not lock external writers or prevent drive
remapping/host aliases.

## Segment and memory boundary

The old near CODE splash followed `_TEXT` in the same CS. With this startup hook,
that shared segment would have only five bytes free. In this variant only, the
existing far entry and complete377-byte CS-relative splash occupy an independent
`FARCODE` segment. Actual DOS character/attribute captures compare the full
4,000-byte splash image exactly before/after, including magenta, logo, version,
edition and Sysop credit. No history, screen, stack or editor capacity is reduced.

| Measurement | Experimental variant |
| --- | ---: |
| Near data and8 KiB stack |64,656 bytes |
| Complete resident CS extent |65,154 bytes |
| Free resident CS |382 bytes |
| CONFIG_CODE |56,173 bytes |
| Separate splash |377 bytes |
| Minimum allocated module |406,416 bytes |
| Live/frozen history |63,000 bytes each |
| Physical full-screen buffers |12,000 bytes |

The checker now reports the complete resident-CS extent, including any other
code segments sharing that CS, alongside the previous `_TEXT`-only counters.
The new variant requires the splash to have its own CS and offset0. Startup
checks bind the actual far target/relocation, status branch, configuration-error
destination and following directory call; five damaged controls are rejected.

## Evidence and remaining integration

The [receipt](validation/directory-resource-cli.json) binds17 actual DOS8086
workflows/486 assertions through the real startup adapter, CLI snapshot, request
factory and strict resource staging. Independent expected bytes cover both and
mixed CLI resources, directory-derived flags, CWD drift, lowercase absolute
paths, profile6 and raw selected metadata. Operational/path failures preserve
both active selectors; rebinding refuses; malformed/missing resources preserve
the output bundle. All source files and42-byte hardware snapshots remain intact.

An isolated38-source export of committed source `c9bed2c` reproduces the
diagnostic and all17 objects, then repeats those DOS workflows. A separate
764-source export of that commit reproduces all ten package files, with Git and
originals unavailable. Application checks cover directory accounting,
startup edit/save and subsequent real DOS EXEC; packaged START performs nested
120-level ASPECT source compilation/replay, and SETUP preserves the exact splash.
Stock loopback ENiGMA is tested through the actual SynthModem proxy with20ms per
serial input byte and250ms key framing, including the actual directory preview
and resumed Home/Insert editing. These software tests exclude SIP/DSP, physical
serial timing, analog audio and full BBS rendering acceptance.

Build an isolated package using the pinned Nix toolchain:

```sh
./tools/dev --command make test-directory-resource-cli
./tools/dev --command python3 standalone/package_special_edition.py \
  --build --custom-irq --directory-resource-cli \
  --output build/special-resource-cli-UNIQUE
```

Next, acquire a stable proposal/resource lease across popup release and the
quiesced PROGRAM owner, stage remaining translation/script resources, retire old
selection accounting, then integrate the actual UART/profile/target commit and
dialing. `directory_resources_stage` is not yet called from the live UI. All full
F01–F16, broad BBS/transfer, physical and card acceptance remain open.
