# ASPECT terminal integer operands

The opt-in `terminal_builtins=True` interpreter implements `$COL`, `$ROW`,
`$SCRNCOLS`, `$SCRNROWS`, `$TERMBOLD`, `$TERMDIM`, `$TERMNORM`, `$TERMREV` and
`$TERMULINE`. Both source compilers emit the original integer operand selectors.
The [native provenance](../reconstruction/aspect_terminal_builtins/provenance.json)
binds nine exact four-byte overlay16 getters to retained REA evidence and a
separate optional comparison with the original executable.

Every result is a raw 16-bit WORD. Cursor coordinates are zero based and logical;
a logical 132-column pane can return a column above79 while `$SCRNCOLS` remains
the physical80. `$SCRNROWS` reads physical display height through `ui_window_rows`,
including when the status bar reduces the logical terminal height. The five
attribute operands return configured words. `$TERMDIM` reads the preset word;
it does not compute a dim mask from the normal attribute. Integer-to-long
promotion retains the native signed integer interpretation.

Production reads use a matching parent built with `--aspect-terminal-query`.
This profile requires the complete compiler-lease renderer and publishes
capability24. Parent operation29 accepts a field index0..8 plus bit8 selecting
the high byte, returning exactly `F000|byte`. The child validates its lease
before and after both requests and publishes the word only after both succeed.
An error, malformed response, or changed lease leaves the destination unchanged.
The parent authenticates each request against the current child PSP, DS,
descriptor/version/token, callback and MCB ownership. Busy field, window,
confirmation, PROGRAM, snapshot and compiler-loan states reject the query;
published UART return rejects it too.

Neither byte request polls input, enters the parser, emits output, invokes a
child callback, or allocates memory. The child runs no scheduler between reads.
This provides a fresh word under the application's foreground ownership model;
it does not claim atomicity against arbitrary external TSR mutation. Ordinary
opcode scheduling and WHEN handling retain their existing behavior. A standalone
interpreter without the parent backend reports unsupported before assignment.
Diagnostic tests supply explicit words; production has no fabricated80×25
snapshot or cached fallback.

[Validation](validation/aspect-terminal-builtins.json) binds the native,
compiler, client, VM and application evidence:

- All589824 WORD getter cases,117 original dispatcher cases and exact native
  getter/dispatcher/resident-thunk bytes. Overlay loading is explicitly modeled
  in this CPU check.
- 90 original compiler probes,54 accepted and36 rejected, matching host and
  actual DOS output. The complete DOS8086 compiler suite passes3246 cases and
  1693 API checks.
- 435 actual DOS8086 client cases with2766 checks, including both-byte errors,
  malformed tags, all busy guards, validation precedence and destination
  preservation. Parent requests/client identity are controlled boundaries here.
- The linked-parent CPU check executes prepare/BEGIN, the cross-stack bridge,
  per-read client authentication and native getters:163 grouped cases,
  117 WORD scenarios/234 tagged responses and497 invalid payloads. Owner,
  returned-UART, authentication and between-byte revocation controls preserve
  registers/FLAGS, source words and video. Pure admission, setup retirement,
  DOS PSP lookup and the optional child UART-open boundary are modeled.
  Ten linked-child version probes admit24 to that backend and reject mismatches
  before entry; actual DOS geometry/EXEC acceptance is checked separately.
- 232 actual DOS VM runs with5218 checks: all nine words, signed promotion,
  globals/locals/parameters/string-register conversion, six held streams,
  EXECUTE, WHEN CALL, unsupported-backend preservation and repeated
  heap/JFT/INT0/FLAGS/ABI cleanup. Enabled and disabled1414-case base runtime
  suites pass35415 checks each.
- Two full-parent source/GET workflows with103 checks, including exact cursor
  21→26, physical80×25 dimensions and configured attributes before/after GET
  and across source EXECUTE. The nested Help/FILE/child workload passes63
  checks. A clean1071-source export reproduces the parent, interpreter,
  compiler and overlays and repeats both workflows without originals,
  previous objects or ancestor Git.
- Eight full-parent DOS8086 geometry cases pass344 checks at25/28/43/50 physical
  rows, each with shown/hidden status. Independent peer CPR checks prove logical
  bottom rows24/25,27/28,42/43,49/50 while `$SCRNROWS` retains physical height.
  Plain MESSAGE changes column21→23; the two25-row wide-pane cases read logical
  columns120→125→131 while `$SCRNCOLS` stays80. GET, exact host/DOS compiler
  output and the complete parent-return comparator remain checked.
- Capability24 packaging has39 admission/archive controls; the existing
  capability23 package retains its34 controls. This staging fixture is for
  contract validation. The later
  [connection checkpoint](ASPECT_TERMINAL_CONNECTION.md) supplies the complete
  committed package/archive and fresh BBS qualification; hardware stays open.

The interpreter is SHA256
`75f1c9327f40de559d3ad9b78231264b8a8758aa0a2358fe20b3b76635575155`.
Near code65204 leaves332 bytes. DGROUP40624, stack8192 and existing buffer/stream
limits are retained; the exact DOS minimum is126208 bytes and the page-rounded
minimum126352. Parent DGROUP remains65520 bytes. The matching source compiler
is `baf2b02b657c6e591b58735d599b58b8fae1433993cfa0f8d91f8a4c94324601`.

This profile is not installed or physically accepted. The earlier
[directory-protocol package](ASPECT_DIRECTORY_PROTO.md) retains its independent
qualification and identities; the later capability24 connection candidate has
its own package and lab receipts. Remaining ASPECT services, broader fault
composition, complete setup/emulation/protocol parity and physical acceptance
remain open. Host remains the final implementation stage.
