# EMULATE parent memory funding

The experimental parent now passes the capacity tests that failed when its
profile owner was added. It saves208 bytes from that initial candidate without
reducing buffers, streams, numeric storage or stacks. This accepts the parent
component for continued integration; the child RPC and VM opcode remain unbound.
The installed connection-test package is unchanged.

[The validation record](validation/aspect-emulate-funding.json) binds the source,
positive results, ordinary control and historical negative checkpoint. Current
parent `b6392d36` is source built. The tested normal interpreter remains `b4f0aecc`.

| Parent | Minimum including PSP |
| --- | ---: |
| Ordinary control `689bdce9` | 479,680 bytes |
| Initial owner `c5e5ba00`, capacity failed | 479,936 bytes |
| Funded owner `b6392d36`, specified capacity passes | 479,728 bytes |

The48-byte increase over the ordinary control remains. These are launch minima,
not universal peak requirements or a guarantee of room for future RPC/VM code.
Near data/stacks remain65,504 bytes; resident code remains65,460 bytes, eight more
than the control. The other retained capacities and existing heap policies stay
unchanged.

## Equivalent smaller operations

The profile owner holds its target and prior setup status in saved SI/DI rather
than an additional BP frame. It combines nonzero-owner tests with the same
state10 outcome. It clears DF for the called services and restores caller FLAGS.
The existing quarantine, import-before-commit rule, fatal-reset behavior and
all owner checks remain.

Only the optional profile selects the compact script handoff helpers:

- Device checks combine the first two name bytes and compare only uppercase
  ASCII-letter forms. Port suffix digits remain raw. Clearing ASCII bit5 in
  alphabetic comparisons leaves rejected nonletters and high bytes rejected.
- Character admission applies that letter comparison alongside unchanged raw
  digits, underscore and hyphen checks. Component lengths, drive/root handling,
  dots, terminators and namespace resolution retain their existing path.
- Hex words use a four-iteration loop with the same leading zeros, uppercase
  digits, four writes and returned pointer.
- Buffer admission specializes the fixed64-byte executable and96-byte tail
  contract. It retains null rejection, inclusive end65536 and half-open
  disjointness, using ordered16-bit differences after bounds checks instead of
  generic32-bit extent arithmetic. The actual buffer sizes are unchanged.

These are maintained-code adaptations. The ordinary source branches retain the
control's exact executable bytes. Compiler-flag experiments did not provide the
required saving and are not selected by the accepted build.

## Verification and reproduction

All306 linked profile-owner cases pass, including the previous294 cases and12
additional ABI cases across default/explicit maps, both profiles, IF settings
and a caller-set DF. Kernel/BIOS/UART boundaries and initial script-owner state
are modeled; product admission, staging, reset and keymap functions execute.
This does not establish an actual child lease or a DOS profile-switch workflow.

Source-branch comparisons run under DOS8086 with identical compiler flags:

| Operation | Coverage |
| --- | --- |
| Device classification | 113,580 authored leaf/stem cases |
| Character admission | All256 byte inputs |
| Four-digit words | All65,536 unsigned16 values, pointer and adjacent-byte checks |
| Buffer extents/separation | 2,686,976 cases covering every offset at fixed null/end/wrap and relative overlap/touch boundaries |

The buffer matrix does not enumerate all2^32 pairs or dereference arbitrary
pointers. These component comparisons do not substitute for complete path or
DOS namespace validation. Capacity runs separately exercise actual script launch
and handoff through the parent and normal interpreter.

Real DOS capacity passes27 held-stream checks on8086,26 stream-around-child
checks on8086, and27 held-stream checks on386. Each executes three real DOS
children, six streams and local DATE/TIME queries, with missing-file recovery
and view restoration checks. No original application/compiler participates.

A clean5,449-public-file export rebuilds the parent and normal interpreter
exactly, repeats all306 linked cases and all three DOS comparison suites, then
passes the8086 held-stream capacity suite. It contains no originals, private
configuration, prior objects or Git ancestry. The separate root386 and8086
stream-around-child profiles are not repeated by that cold proof.

```sh
./tools/dev --command python standalone/check_aspect_emulate_parent.py \
  --product build/emulate-parent-fixed-buffers-20261107 \
  --output build/my-funded-emulate-checks
./tools/dev --command python standalone/prove_aspect_emulate_parent_source.py \
  --parent build/emulate-parent-fixed-buffers-20261107 \
  --test build/emulate-parent-funded-abi-checks-20261107 \
  --runner build/aspect-alarm-unwind-funded-20261106/ASPECT.EXE \
  --output build/my-funded-emulate-cold
```

Next connect the versioned child request and VM opcode to this owner. Verify the
bridge's bounded stack and MCB/lease validation, WHEN/modal ownership, script
error cleanup, actual DOS profile changes and fatal-reset faults. Measure receive
service during keyboard imports/clears and retest memory after adding the bridge.
Current Enigma/Synchronet, package and physical acceptance are required for the
integrated product. The remaining named emulations and F01–F16 inventory remain
open. Neither this component nor the newer source compiler has been deployed.
