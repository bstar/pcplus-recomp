# ASPECT external execution in the actual VM

The separately built experimental interpreter now connects the exact DOS/RUN/
SHELL frontends to the composed PROGRAM controller. Real ASPECT numbered streams,
the buffered ASX reader, native call frames and subsequent DOS source compilation
survive actual child execution. This is an 108-slot experimental build; the normal
105-slot interpreter remains byte-identical and still rejects these three slots.
No whole-application gate closes.

The [ledger](validation/aspect-process.json) binds 56 actual 8086 DOS cases:
COM1/COM2 crossed with N/S/H/B flow and seven workflows. All 1,712 DOS assertions
pass, together with independent per-command status/flag and exact wire audits.
An actual unprotected launch of the same child demonstrates inherited-handle
access with its specific exit 98; guarded launches reject that access and execute
the rest of the real child. No process, keyboard or file service is replaced by
a successful recorder.

Fourteen separate linked policy cases model PROGRAM/file/renderer outcomes to
check result classification and cleanup ordering. They are not DOS execution
evidence. The retained pre-fix binary accepted internal ownership failures as
ordinary child results; the corrected bridge aborts with invalid-state after
retiring the scopes. Argument, EXEC and allocation failures retain native
comparison semantics. Unknown or contradictory owner results also reject.

## VM and file ownership

`src/aspect/external_runtime.c` enters an explicit runtime scope. An attached
parent renderer rejects before any flush or ownership mutation. The raw/local
path retains the current ASX owner, complete native read window, logical and
physical positions, then brackets the six actual numbered streams.
`script_file_runtime.c` flushes pending output and records their CRT owners,
native prefixes, buffered bytes, logical positions, mode/error/EOF state, slot
pointers and lifetime counters. These are the interpreter's actual streams,
not ordinary-C substitutes for ASPECT files.

`src/process/process_handles.c` temporarily hides only their selected DOS JFT
entries, including the current ASX descriptor. Parent SFT references and CRT
buffers remain owned. The original mappings return before any parent file I/O,
on process failure as well as success. DOS constructs a child without these
private handles; the child can open its own files at the same handle numbers
without changing a parent's buffered stream. This is lifetime isolation, not
memory security against a DOS program that deliberately alters parent memory.
The DOS child-table cloning behavior is visible in the primary
[FreeDOS process implementation](https://github.com/FDOS/kernel/blob/master/kernel/task.c).
Execution evidence here uses DOSBox's internal DOS, not FreeDOS or physical DOS.

After PROGRAM returns, the binding restores the JFT, checks the ASX window and
both positions, checks the six stream owners/buffers, and retires the VM scope.
Process failure remains the native raw FFFF comparison and execution can continue.
Ownership/display/serial failures become typed runtime errors after cleanup.
SHELL retains its original comparison behavior; absent COMSPEC is handled safely
as a raw invalid-name result rather than dereferencing a null pointer.

The variant shares the existing byte-verified string/error helpers. Its path
state provides a full WORD DOS-error field before exporting the process aliases,
so native error writes cannot overwrite the adjacent DOS-version byte. The
default build retains its existing layout and exact executable hash.

## Actual DOS workflows

- The full route checks every result and flag for COM, EXE, batch, PATH,
  command-processor, missing-target, WAIT and NOCLEAR calls. An owned COMSPEC
  wrapper enters the real `Z:\COMMAND.COM`, supplies EXIT through BIOS input,
  observes nested EXEC return and writes a completion marker.
- Five input streams retain prefetched data/positions; a sixth output stream
  becomes visible to the child before parent close. The ASX file stays open
  privately. Local integer/string values and global values survive RUN.
- EXECUTE compiles the missing `NEXT.ASP` under DOS, with output matching the
  host compiler exactly. Numeric/settings/environment state, six open streams
  and an active enumeration continue. Global strings correctly begin a new
  per-file lifetime; they are not incorrectly claimed to survive EXECUTE.
- A forced environment fallback runs with live local values. The large case
  borrows 8,365 arena bytes while the actual local frame begins at offset 6,944;
  the frame is inside the overwritten region and its values restore correctly.
- Allocation failure returns raw FFFF and resumes the next instruction. A real
  foreign-DS divide child returns 12 while the interpreter continues normally.
  Subsequent script divide/budget errors clean up; a second invocation in the
  same interpreter process reopens all six streams and receives later serial
  input successfully.
- Queued 00/1A/80/FF input, child baud/vector/PIC changes, restored UART input,
  exact S/H/B/N data/flow output and final baseline restoration are exercised.
  The complete parent JFT is compared before and after each invocation.

Nineteen linked CPU cases separately check selected-only restoration, nested
admission, closed/duplicate/out-of-range handles, far-table bounds, foreign-slot
detection and 20/40/255-entry tables. Only the default 20-entry case has actual DOS
execution evidence; the larger tables use explicitly modeled PSP metadata.

A fresh tree with only declared source inputs reproduces 23 DOS products exactly,
including the experimental interpreter, normal interpreter and DOS compiler.
The normal 1,111-case/26,686-assertion runtime and 108-input serial regressions pass.
The normal interpreter remains `aef146fd…21e559f5`.

```sh
./tools/build test-aspect-process
./tools/build test-aspect-process-source
```

The first failed DOS recipe used a nine-character DOS shell basename; the
corrected 8.3 name reaches the real command processor. A second recipe incorrectly
expected global strings across EXECUTE. Both captures remain retained; neither
is accepted as compatibility evidence. Partial compile/recipe attempts also
remain local and are not counted as DOS sessions.

## Remaining production integration

The normal dispatch table remains 105 slots. Before publication, bind the actual
ASIOv4 renderer and selected directory/translation leases, plus the applicable
macro keyboard, mouse/window and error-notice services. The existing terminal's
admitted renderer is mode3/80x25/page0; the broader original views remain in scope.
Nonlocal parent faults *during* external ownership need separate cleanup proof;
the error tests here deliberately occur after child return. Other DOS kernels,
physical Wi-Fi modem timing and complete live BBS workflows remain open.
