# ASPECT decimal conversion commands

The standalone interpreter now executes `ATOI`, `ATOL`, `ITOA` and `LTOA`
with the recovered scanner and CRT instructions. All 38 new authored compiled
fixtures pass in actual 8086 DOS. Fifteen independent compiler-validation
fixtures also pass, including nested operands and boolean control flow.
The composed suite now passes 410 cases and
6,090 assertions across 237 compiled fixtures. Of 215 dispatch slots, 54 are
wired and 161 still abort explicitly. This remains a partial interpreter.

The [frozen evidence](validation/aspect-conversions.json) binds current sources,
normal and optional original comparisons, compiler provenance and DOS results.
The diagnostic build now invokes the [maintained host compiler](ASPECT_COMPILER.md)
on each authored source, compares output with its frozen oracle and runs that
generated ASX. The original compiler is no longer required for this test build.

The fresh [source-only checkout rebuild](validation/application-components-source-build.json)
reproduces all 82 current DOS outputs byte for byte and runs the compiler
regressions with originals, analysis databases and prior build outputs absent.
`EXECUTE.EXE` SHA256 is
`0227ce9de6d70280bdee7d6d80f1af23923610d3ee97172de89ed7dee35c9a5b`.

Reproduce through the pinned Nix toolchain:

```sh
./tools/build test-aspect-compiler test-aspect-conversions test-aspect-conversion-services test-aspect-runtime
```

Optional read-only comparisons with the ignored original executable:

```sh
./tools/build test-aspect-conversions-compat test-aspect-conversion-services-compat test-aspect-runtime-compat
```

## Recovered behavior

| Command | Opcode | Accepted source form | Result |
| --- | --- | --- | --- |
| ATOI | 06 | `atoi string integer_destination` | Low 16 bits of decimal parse |
| ATOL | 07 | `atol string long_destination` | Full 32 bits of decimal parse |
| ITOA | 61 | `itoa integer string_destination` | Signed decimal string |
| LTOA | 6E | `ltoa long string_destination` | Signed decimal string |

The command/scanner module recovers 218 bytes in overlay17 ranges
EA4B..EAE1 and EAF4..EB38, with exclusive ends. The CRT module recovers
312 resident bytes across seven ranges: two parse thunks, the shared parser,
two formatting entries, the shared formatting body and `strcspn`.
These modules call the existing recovered operand, string scratch, integer
destination and far writeback code. Host libc conversion functions do not
replace the native instructions.

The command component passes 1,711 CPU scenarios and 8,282 actual DOS
assertions, visiting all 104 command/scanner instruction addresses. Optional
comparison verifies all 46 component code ranges, including the actual CRT,
rather than substituting a host parser behind native command handlers.
The CRT service diagnostic separately passes 3,709 direct CPU vectors plus
1,234 C selfcheck vectors, with 6,694 assertions in actual 8086 DOS.
Optional native replay reproduces the CPU results. Invalid radices are only
characterized with bounded CPU diagnostics; they are never run in DOS.

The scanner searches for the first decimal digit, or a minus immediately
followed by a decimal digit. Other leading characters are skipped. Thus
`cost: 42 dollars` becomes 42, `.75` becomes 75 and `x-.x--7z` becomes -7.
Once a candidate is found, parsing stops at the first nondecimal character:
`12.99` becomes 12. No candidate yields zero.

The parser accumulates modulo 2^32. ATOI consumes the low word rather than
reporting range errors: `65537` becomes 1. ATOL of `4294967295` retains
FFFFFFFF, and `4294967296` wraps to zero. Negative values use two's-complement
negation. These are recovered behaviors, not a new overflow policy.

ITOA and LTOA pass radix 10 to the native formatter and produce signed decimal,
including -32768 and -2147483648. The CRT formatter also has nondecimal paths,
but those paths are not a claim that ASPECT exposes a radix argument. It does
not check destination size or invalid radix. The composed command handlers use
the existing 81-byte owned string buffers and decimal output fits within them.

The scanner reads only bit04 of the original ctype table. Optional original
comparison verifies that exactly bytes 30..39 have this bit. The maintained
table reproduces that consumed predicate; it does not reproduce or claim the
other CRT classification flags. Candidate text `-.0123456789` is verified
separately against DS:776C. High CP437 bytes remain nondigits.

## Compiler evidence and limitations

The original compiler oracle accepts 38 of 42 authored scripts. Tests cover
zero, signs, integer/long limits, overflow, empty and nonnumeric strings,
prefixes/suffixes, CP437 high bytes, local variables, string parameters and
parse/format composition. Four wrong-order, missing-argument or wrong-type
attempts are rejected. All 37 outputs accepted by the earlier probe reproduce
unchanged in the final probe; the additional accepted case corrects a source
expression to a single signed long literal. Expected runtime values were fixed
in the authored probe before composed execution.

The exact source grammar is broader than these tests establish. Floating-point
conversion, formatting commands, other builtins, source compiler completeness,
recorder, terminal bindings and scheduling remain open. The scanner retains a
floating candidate flag, but recovering that branch does not implement ATOF.
There is no general arbitrary-input script runner. All F01–F16 whole-application
gates remain open.
