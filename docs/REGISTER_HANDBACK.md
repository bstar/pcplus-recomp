# Experimental ASPECT register handback

The optional register build retains the native ten integer words and ten
81-byte string slots when an external ASPECT child returns. This is a maintained
ASIO extension, not the original PCPlus helper protocol. It prepares storage for
the pending guarded HOOK integration; directory KEY kind2 remains disabled.

## Ownership and initialization

ASIO version7 adds four words to the version6 descriptor: exchange offset,
segment, byte count and invocation token. All four participate in the existing
input guard. The descriptor is58 bytes and may reside outside parent DS.
`parent_ds` still addresses the ring, translation table and directory record.
Old builds continue to admit only versions1–6.

The terminal owns1,734 initialized bytes in HOOK_CODE: phase/token/epoch/seal,
descriptor, an838-byte exchange and the830-byte accepted bank. It adds no near
DGROUP storage. The exchange contains magic, token, returned and seal words,
followed by20 integer bytes and810 string bytes. Parent APIs require the actual
application DS=SS, IF set and DF clear. The seal detects accidental damage; it
provides neither authentication nor isolation from another DOS program.

Preparation copies the accepted bank, clears the integer words and the first
byte of each string slot, and preserves the remaining string bytes. This follows
the recovered per-invocation initialization described in
[HOOK exchange](HOOK_EXCHANGE.md). The child restores the preserved tails after
its ordinary runtime reset. Its integer and string banks have separate linked
addresses; publication gathers them explicitly.

The child validates the exchange against the parent's allocation and known
descriptor/ring/table/record/render spans before UART acquisition. It attaches
only after acquisition succeeds. After its IRQ is released, it publishes bounded
strings and integer bytes, the seal, then the register returned flag. Ordinary
ASIO status/count/flow and returned follow.

Parent extraction checks immutable descriptor fields, token, returned flags,
ring count, carrier policy and bounded/sealed register payload. Extraction moves
the owner to a distinct validated phase. Commit requires that phase and rechecks
the payload; preparation alone cannot authorize commit. The existing terminal
handback checks still run before commit. Failure/discard preserves the accepted
bank. A failed child that did not initialize its interpreter may omit register
publication; a successful child may not. A malformed helper or failed EXEC does
not become a successful register return.

## Build and validation

Use the pinned Nix toolchain:

```sh
./tools/dev --command python3 standalone/build_terminal.py \
  --external-render --mouse --notice-sound --notice-input --aspect-keys \
  --directory-keys --process-bank --session-capture --session-projection \
  --session-baseline --register-handoff
./tools/dev --command python3 standalone/build_aspect_process.py \
  --notice-bank --notice-sound --notice-input --notice-help --help-resource \
  --serial-bank --register-handoff
./tools/dev --command python3 standalone/check_register_handoff.py \
  --output build/register-handoff-linked-new
./tools/dev --command python3 standalone/test_directory_key_bindings_dos.py \
  --process-bank --session-projection --register-handoff \
  --label register-script-new --case script --port 2
```

Each test output/label must be fresh. The linked checker runs the actual parent
and child far APIs, verifies calling conventions, and prohibits interrupts and
port access. It covers all bank bytes, invocation reset, damaged descriptor and
payload rejection, commit ordering, missing publication, invalid CPU context,
child admission and unterminated strings. It does not model DOS EXEC or replace
product routines. The DOS smoke test uses the actual terminal, ASPECT child,
UART/renderer and a synthetic serial peer; it does not inspect every returned
bank byte.

The current checkpoint passes923 linked input cases and separate COM1/COM2 DOS
script smoke sessions. Both older terminal and ASPECT products match their
previous executable hashes exactly. The new ABI declarations are feature-gated:
exposing otherwise unused types changed Watcom's static symbol order, so merely
disabling calls was insufficient to preserve the older executable.

The [receipt](validation/register-handback.json) binds current source hashes,
linked binaries/maps/manifests, DOS fixture/capture hashes and the older product
comparison. Recreate it from completed captures using:

```sh
./tools/dev --command python3 standalone/record_register_handoff.py \
  --linked build/register-handoff-linked-03 \
  --dos-label register-script-03 --dos-label register-script-com1-01 \
  --output docs/validation/register-handback.json
```

## Remaining acceptance

This checkpoint does not establish full register/HOOK acceptance. Still required:

- Real DOS sequences that write/read every integer and string bank through
  ASPECT and inspect accepted state across multiple invocations, errors and retry.
- End-to-end failed/malformed helper tests, including publication failure
  followed by clean UART continuation. The linked admission tests already cover
  allocation edges, each known overlap span and segment wrapping.
- An empty-source-tree reproduction and combined parent/child proof for this
  optional build, plus current Synchronet/ENiGMA interaction coverage.
- Guarded HOOK routing, remaining native PRM fields, returned-settings staging
  and application, and composition with the exit/trap owners.
- Physical Boca/SPA2102/SynthModem and complete application acceptance.

The workstation tests do not establish physical modem compatibility, hardware
handshake/audio, or a14.4 kbps connection.
