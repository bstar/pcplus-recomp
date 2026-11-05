# Gateway file transaction

The optional `--gateway-files` parent composes the bounded direct-COMSPEC
resolver with the retained private-handle lease and actual sink-owner queries.
It flushes capture without stopping it or changing HOLD, protects currently
open descriptors, executes the selected interpreter, and restores the lease on
both success and failure. The transaction has six initialized bytes in FILE_CODE
and adds no near data or resident code.
The supported composed configuration includes the call-log bank, as recorded in
the receipt's build arguments; the broker depends on that file owner.

This is the application file boundary. Alt-F4 is still unbound: foreground
admission, display/mouse/trap return and serial ownership are not integrated by
this option. PROGRAM's existing stop-capture/close-printer policy is unchanged.

## Contract

`gateway_files_run()` uses far cdecl, DS=SS and IF1/DF0. Its result pointer must
be the parent's existing `terminal_program_result`; it cannot point into sink
snapshots, flags or caller-selected data. The context adapter additionally
checks the real parent DGROUP and current DOS PSP before any file action.

Admission refuses another lease/transaction, queued or closing printer output,
uncertain/failed open sink ownership, capture reservation activity and an active
or unresolved call-log file transaction. Call-log readiness is a pure owner
query; no log data is discarded or flushed by this transaction. Capture/snapshot/
monitor/history/PRN descriptors are collected without ownership transfer. Capture
flush runs before JFT masking; its normal failure/cleanup policy remains active.
The future foreground scheduler must drain printer work before this boundary.

The resolver runs while the selected JFT entries are masked. Restoration runs
even when COMSPEC is missing/invalid, a candidate fails EXEC or a child exits
nonzero. Nonzero child exit remains a successful EXEC. Parent file positions
and open owner state are preserved, and shell CWD persists until application
exit restores the startup directory.

Uncertain JFT restoration or damaged transaction cookie/active/recovery state
returns `GATEWAY_FILES_RECOVERY` (8). The owner latches recovery and refuses later
launches before file IO. `gateway_files_owned()` exposes an active lease or
recovery condition. The foreground caller must quarantine before resuming any
owner IO, including cleanup that assumes valid descriptors. These checks are
lifetime/integrity guards, not protection against arbitrary DOS memory writes
or an explicit child open by filename.

## Validation

The receipt is [gateway-files.json](validation/gateway-files.json).

- 40 linked CPU cases run the actual broker, owner adapters, resolver, JFT
  lease and recovery latch. Filesystem and raw EXEC endpoints are modeled.
  They cover five simultaneous owners, enabled/held capture, repeated calls,
  failed/missing/rejected interpreters, queued/uncertain owners, foreign result
  pointers, DS/IF/DF/current-PSP admission, failed flush before masking, changed
  JFT metadata and corrupted lease/transaction state. Repeated calls after
  recovery perform no further file IO or EXEC.
- Ten actual DOS8086 workflows, with FPU disabled, pass 184 external checks.
  Both enabled and held capture run a synthetic empty-tail interpreter, a child
  changing CWD, missing and BAT interpreters, and real COMMAND.COM MD/CD/EXIT.
  Four real application files remain open with unchanged descriptors and end
  exactly AB. The synthetic child gets invalid-handle errors when writing or
  closing descriptor slots 5..19 and safely reuses slot 5 for its own Y file.
  Capture buffer/flags, complete descriptor close, retained floor, shell and
  final startup CWD, final hardware/vector snapshots and binary identity are
  checked independently.
- The preceding 56 private-handle/owner-query cases, 33 Gateway lookup cases,
  and ordinary HOOK's 28 cases plus 14 boundary cases pass with this parent.
- Fresh Git-free source trees reproduce the normal parent from 586 public
  inputs and both diagnostics from 588 inputs each. Disabling this option
  reproduces a327e2a1 exactly; ordinary ASPECT reproduces 23caac93. No original
  executable is an application build input.

Normal parent: `build/gateway-files-integrity-20261104/TERMINAL.EXE`, SHA256
`a3fb5c2bf51b66e1118dbf57ff0b4f53f8fa0c854258538615fd1ff217a21af3`.
Near data/stack is 65,488 bytes (48 spare), resident code 65,332 bytes,
FILE_CODE 5,854 bytes and retained parent floor 28,770 paragraphs including PSP.

`--gateway-files-probe normal|hold` invokes a diagnostic before UART startup,
opens the four application file owners, executes the broker, continues writing,
closes them and records a fixed 116-byte report. The probe's generic near-call
adapter is diagnostic-only and is absent from the normal parent. These images
are not deployment candidates or evidence of active UART compatibility.

## Next integration

The optional [live UART owner](GATEWAY_UART.md) now implements and tests the
kind9 IF0 return path and live RX/flow policy. Its diagnostic uses this file
transaction with an acquired UART across real DOS EXEC. Foreground/display and
physical/BBS acceptance remain open.

Add the distinct Gateway foreground action with revalidation at launch, printer
drain, no return-key prompt, and appropriate failure/quarantine handling. Reuse
the verified display and mouse owners while preserving shell CWD. Integrate the
tested live UART owner and kind9 IF0 return boundary into that normal scheduler;
their diagnostic invocation does not establish the full foreground lifecycle.

Sustained RX/flow, DCD, FIFO state, transient DTR behavior, reconnects, transfers,
BBS interaction and physical Boca/SPA2102/SynthModem acceptance remain required.
No deployment, physical machine, network, boot, ATA or service setting changed.
