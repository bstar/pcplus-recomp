# EXECUTE in the source-built DOS interpreter

Opcode CB now runs the recovered 24-byte E709 command and actual resident999
restart in the diagnostic and production executables. It closes the old script
and starts a compiled target in the same interpreter invocation. It never
returns to the old procedure. EXECUTE is the original keyword; CHAIN is not an
additional accepted source keyword.

The loader stages the latest native E104 scratch filename before resetting
per-file state. Numeric and system banks, near builtin strings, settings,
FIND/SWITCH state, WAITFOR result and UART ownership remain invocation-owned.
Old far global strings are released and the new file allocates fresh empty
strings. Frames/depth/local-record owner words, operand lookahead/staging,
WHEN registration/progress pointers and pending near string destination reset.
Maintained C service guards also retire so no event points into a closed file.
The existing receive gate increments across replacement; the new compiled
main prologue decrements it. It is not overwritten with1. A framed procedure's
own prologue already cancels its caller's D0 increment; replacing a script from
inside that procedure therefore need not retain an extra gate contribution.

The initial production and diagnostic entry now uses native interactive owner0.
Previously it used owner1 but assigned gate1, a combination differing from the
native owner1 gate2. Owner0 plus native increment preserves the ordinary main's
old gate0 behavior. Remote-owner invocation and original remote scheduling
remain unfinished requirements.

## Checked loader boundaries

`script_path.c` follows the retained D4D0 filename algorithm: ASCII uppercasing,
leaf after the last backslash/colon,1..8 stem characters, exact ASP/ASX suffix,
and default ASX. It stages output transactionally, allows input/output aliasing,
and rejects more than80 input characters or an extension append exceeding its
82-byte storage. The original append can overflow that storage; this rejection
is an intentional maintained guard. Forward slash is not treated as a separator;
other DOS pathname rejection remains the file system's job.

The current file locator tries the compiled name then the existing bounded
PCPLUS environment fallback. Before reading the header it rejects a character
device through the maintained CRT's `isatty(fileno())` interface; EXECUTE CON
therefore cannot wait for console input. This uses the current CRT rather than
recreating the original CRT's private descriptor flag table. Empty EXECUTE
terminates normally after releasing the old file. Invalid names stop with
operand/native102; missing compiled files report OPEN; bad headers report HEADER.
Partial new-string allocation unwinds and releases each live block once.

**DOS source compilation is still required and unimplemented.** Explicit ASP
stops as unsupported; missing ASX does not yet find/compile an ASP fallback.
The original invokes ASPCOMP.EXE and has different missing-source/error UI.
The authored Python compiler supplies source-built ASX on the host, not a DOS
compiler dependency. Neither the original compiler nor original executable is
an application build input. Parent STATUS still shows the invocation's initial
script label rather than a replacement target; the native D464 label refresh
requires a subsequent owned parent/child operation. These are open plan items.

## End-of-script receive

The formerly unsupported final shutdown bridge now wraps recovered61-byte
4BFF end-wait. An attached live terminal renderer uses its50-unit delay,
translated/displayed receive loop,15-unit empty-queue delay and non-consuming
key check. It disables ordinary WHEN matching and forces DISPLAY when data
is present. It does not execute between999 replacements.

The native loop has no deadline. The maintained owner shares the invocation's
instruction budget across drain reads, services transport/ESC, and retires the
drain before entering native code so a nonlocal error cannot reenter it. A
canceled/failed script skips draining. Child keyboard admission currently uses
BIOS, not every original buffered-key queue. Raw ASIO sessions and the explicit
diagnostic transport preserve unread bytes and skip terminal draining. Those
platform policies are intentional and are not an exact native CLI end-drain
claim. The component proof separately executes the actual end-wait and receive
instructions with declared platform callbacks.

## Verification

Use the pinned Nix environment:

```sh
./tools/build test-aspect-chain-native test-aspect-end-wait-native
./tools/build test-aspect-chain-compiler test-aspect-script-path
./tools/build test-aspect-chain-runtime test-aspect-chain-serial-dos
```

- Native chain/reset/final owners:208 CPU cases,248 exact new bytes; actual
  scratch/strcpy/dispatcher composition, retained-state and gate-wrap cases.
- Native end-wait:221 CPU cases,61 exact new bytes plus83 existing receive bytes.
- Original compiler oracle:35 accepted EXECUTE specimens,41 rejections, their
  corresponding variants and7 novel maintained-compiler cases. CHAIN rejected.
- Checked path resolver:35 host-C cases,141 checks including unchanged output
  on failure and input/output aliasing. These are retained-algorithm policy
  cases, not execution of the original filename loader.
- Actual DOS diagnostic:16 cases,287 checks through real files/far allocations.
  Covers literal/far/local filename operands, settings/numeric persistence,
  empty new globals, three-file replacement, abandoned local frames and WHEN
  references, empty/missing/device/bad-header/name/source targets, truncated
  operand, partial allocation and cumulative self-chain budget. Serial input
  continuity uses an explicitly declared diagnostic queue.
- Actual production DOS child with independent TCP peer:two cases. A chained
  target retains changed BREAK1234, consumes queued END, transmits the expected
  wire bytes and returns exact raw TRAIL to ASIOv1. A missing target also
  restores IRQ/PIC/MCR/guards. No renderer or physical modem claim.

Current reports live under `build/aspect-{chain-native,end-wait-native,
chain-compiler,script-path,chain-runtime,chain-serial-dos}/checks.json`.
The public aggregate binds them separately from the original-free rebuild and
broader regression evidence. This checkpoint supports72 opcode slots; the
remaining143 and all whole-application F01–F16 gates remain open.
