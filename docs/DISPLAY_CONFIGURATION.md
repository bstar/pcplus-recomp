# Saved display fields and native operand behavior

The line-selector investigation now connects the original memory-image PRM to
its consumers. The whole-image reader/writer starts at DS1B84 and spans1264
bytes; these fields are therefore inside the saved image:

| PRM offset | Original DS | Meaning and evidence |
| --- | --- | --- |
| 01C2 |1D46 | Status hidden WORD; recovered46BA normalizes zero/nonzero. |
| 01C8 |1D4C | Saved display selector; startup overlay3 passes it to2EAA. |
| 01CA |1D4E | Preferred row WORD; passed by startup and Ctrl-minus to2EAA. |
| 04EC |2070 | Preferred BIOS video-mode WORD, consumed by selectors3/4. |

The lossless Python codec now names all four fields. It retains every16-bit
value and every opaque neighbor; it does not validate a PRM's version, silently
normalize saved data or write an installed file. The optional [startup capture](DISPLAY_PREFERENCES_STARTUP.md) now publishes
these raw words after successful import, separately from live hardware geometry.

## Recovered SET/FETCH handlers

The93 new native bytes consist of overlay19 EDD1..EE22 (82 bytes) and parent16
DDEE..DDF8 (11 bytes). Flat assembly matches loader-derived original file ranges
exactly; relocatable OMF assembly also builds. These are ASPECT SET/FETCH field
handlers, not setup-screen or text-configuration routines.

EDD1 tests E38E query mode. Zero calls DDEE, whose wrapper requests integer
bounds0..127 from DD68, then stores AX into2070. Nonzero passes the raw2070
WORD to DE3A, the typed integer destination writer. No BIOS mode change occurs
inside this handler. The full bounded parser is outside this focused recovery;
the wrapper's bound arguments execute against an explicit modeled boundary.

EDE7's zero-query branch calls the general integer reader DC48 and recognizes
28,43,50. Other values call error1 through4EFB. If that service returns with
E378 nonzero, the handler substitutes43; if it returns with E378 zero, it stores
the original word. If the error unwinds, storage never occurs. The tests keep
those cases distinct: a returning error model is not evidence that ordinary
ASPECT source accepts invalid rows. Nonzero query mode returns the raw saved
word through DE3A without validation or a BIOS change.

Ctrl-minus still uses2070's unsigned zero/nonzero state to select two or four
selectors. The downstream display service instead requires signed2070>0 and
font capability for3/4; otherwise it falls back to selector1. The saved selector
is not a proof of accepted physical geometry. See [display recovery](DISPLAY_MODES_RECOVERY.md).

## Evidence and verification

[Provenance](../reconstruction/display_config/provenance.json) binds original
SHA256, loader-derived original ranges, flat digests and REA Evidence IDs.
`ev_10e4272da2361a912c9abd8f23a9111a00e3f6f7666b090f35b9d9f1b22bce62`
reads the82 handler bytes and
`ev_8e5daa5453f123bb822d29973def72c5fe96980178413505448165b23969ddf0`
reads the video operand wrapper. The synthetic overlay image includes parent16
at its loader-derived address; it was analyzed statically and never executed.
Independent comparisons use genuine original overlay bytes, not that synthetic
image. Ignored REA bundles retain the complete records.

Each [source-only and original-comparison suite](validation/display-configuration.json)
executes131328 inputs: all65536 row words under both returning-error flags,
all128 video operand values,88 raw-word query combinations and40 error-unwind
cases. The actual recovered handlers and bound wrapper execute; integer readers,
destination storage and error services are explicit boundaries. DS=SS,
BP/SI/DI, stack balance and guards are checked on normal return. Error-unwind
cases stop at the service boundary without claiming normal cleanup. The nine
lossless-codec tests also pass, including56 display field/word combinations
with exact untouched-neighbor comparisons.

```sh
./tools/build test-display-config
# Optional: requires the ignored original executable.
./tools/build test-display-config-compat
```

## Next integration gates

The optional startup capture now stages these fields with the current
configuration; applying them must distinguish saved selector from accepted BIOS state. The [physical selector service](DISPLAY_SELECTOR_SERVICE.md) now handles
configured-mode decisions and verified fallback; selector cycling and the
canonical transaction still need application integration. Combine those with the existing
[offline BIOS/canonical transaction](ROW_GEOMETRY_TRANSACTION.md), larger modal
screen loans, guarded commands and explicit online bridge coordination before
advertising either line/status command. No key availability, application image,
package, active pointer, private PRM, installed bridge or physical machine changes
in this recovery. Thirteen unavailable reference commands and full hardware/BBS
acceptance remain open.
