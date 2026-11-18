# Clock string operands and procedure keyword binding

The opt-in `clock_builtins=True` runtime executes the original read-only string
operands `$DATE` (selector8), `$TIME0` (20) and `$TIME1` (21). Both maintained
compilers emit their original `6E selector` operands and reject attempts to use
them as writable destinations, declarations or procedure names.

These getters call the existing recovered DOS formatters directly. `$DATE`
preserves year-minus1900, so November17,2026 is `11/17/126`. `$TIME0` returns
12-hour text with adjacent AM/PM; `$TIME1` returns24-hour text. Neither getter
sets the clock, consumes another ASX operand or flushes a destination.

Both time operands return the **same mutable buffer**. Thus
`strcmp $time0 $time1` compares two pointers to the second formatted result and
reports equality. The reverse order has the same aliasing behavior. Explicit
assignment, parameter copying or `strcpy` preserves the copied text independently;
the DATE buffer is separate. Fresh independent strings or cached clock values
would change the recovered behavior.

[Provenance](../reconstruction/aspect_clock_builtins/provenance.json) links
retained REA evidence for the three overlay16 bodies: DAC2, DAFF and DB07.
Their20 bytes, original string-dispatch slots and resident stubs are compared
separately with the SHA-bound original. Normal builds never consume originals,
analysis images or REA databases. The existing resident36D4/498B date/time
helpers and formatter buffers are reused without new data allocations.

The original compiler probes also exposed an existing procedure-name gap.
Both maintained compilers now reject all558 identifier-shaped names in the
original18-table keyword catalog as procedure declarations. Eight ordinary
prefix controls remain accepted. The DOS guard uses a3971-byte packed string
block, without a558-pointer table. Builtin type/selector metadata in the DOS
compiler is now explicit, replacing positional type inference. Inventory,
expression and full-compiler source manifests include the new header and the
previously omitted emulation header dependencies where needed. This does not
claim complete variable-declaration keyword rules or complete language parity.

[Validation](validation/aspect-clock-builtins.json) binds:

- 477 getter CPU cases with original resident-CRT comparisons and modeled DOS
  dates/times, plus10 shared-buffer checks. Every getter issues one DOS query
  with the near DS=SS ABI.
- 63 original clock compiler probes:27 accepted,36 rejected, exact host/DOS
  bytes;566 procedure-name probes:558 rejected keywords and8 accepted controls.
- The complete3156-case DOS8086 compiler regression, with1693 API checks.
- Enabled and disabled1414-case runtime suites. Disabled clock operands stop
  before replacing an existing destination.
- 682 actual DOS clock runs over31 same-process rounds,16680 assertions and12
  direct API checks included in that total. DOS readings bracket each date/time
  result; the clock is never changed. Globals, locals, parameters, registers,
  WHEN callbacks, six held streams, nested EXECUTE, mixed command/builtin use,
  alias comparisons and copied strings retain heap/JFT/INT0/FLAGS/ABI state.
  Direct getter calls preserve pending destination, scratch-ring and comparison
  markers while reusing the expected date/time buffers.
- Two full-parent source/GET workflows with101 checks and all three clock
  reads before/after input and across source EXECUTE;63 nested-DOS/held-FILE/Help
  checks. A cold1067-source export reproduces the parent, interpreter, compiler
  and overlays and repeats those workflows without originals, prior objects or
  ancestor Git.

The full interpreter is SHA256
`7446e9b5dc135b83ce03643e2c4db791f827ab5a728961c9f735788fa678c459`.
Near code grows64 bytes to64772, leaving764 spare. DGROUP40608, stack8192,
all buffers and VM limits remain unchanged. Exact DOS minimum is125760 bytes;
the page-rounded125824-byte minimum is unchanged. The source compiler retains
its24576-byte stack and passes actual parent compilation with the keyword guard.

This profile has not been packaged, BBS-qualified, installed or physically
accepted. The [prepared directory-protocol package](ASPECT_DIRECTORY_PROTO.md)
keeps its separate byte identities and qualification. Remaining builtin and
command services, broader fault composition, full emulation/protocol/setup
parity and physical acceptance stay open. Host remains the final implementation
stage.
