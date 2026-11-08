# ASPECT CONNECTED operand

The maintained host and DOS compilers now accept the original read-only integer
`CONNECTED` operand. The runtime returns the modem-status DCD bit: **128** for
carrier high, **0** for low. This lets scripts use the original comparison rules,
including `if connected` and `if connected == 128`. It does not change the parent
terminal's connection state machine or its status bar.

## Original evidence

The private PCPlus executable is identified by SHA-256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
REA's overlay16 integer dispatcher at D988 selects table DS:4CB6. Slot29 points
through resident CC3F to overlay16 DA36, which jumps to AA5C. That routine reads
the port from DS:8FFE, executes `IN AL,DX`, masks AX with0080 and returns.
These are static observations; the original runtime was not executed for this
checkpoint.

Retained REA evidence:

- Dispatcher: `ev_9bac80d7375f8ce6a3ead676649b1f17961387f1afd1c0d8d73b15b17e525098`.
- Slot29 getter: `ev_27a78779152828e62ad96e8a577487c6609fe8d0a90ddbf3b7ca8774822622d4`.
- UART getter: `ev_4b8ba5f521315cae11bf646b2df2c5682fec78685053c0e657b4c56b762fa136`.

Full records stay in ignored `analysis/aspect-integer-builtins-20261108.rea.json`
and `analysis/aspect-connected-uart-20261108.rea.json`. Synthetic analysis images
were not executed and are not build inputs.

The original ASPECT1.01 compiler, SHA-256
`5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a`,
compiled22 authored grammar cases under DOS. Eleven succeed, eleven fail. Both
maintained compilers match acceptance and every successful output byte, including
operand `6F 1D`, case folding, arithmetic, integer-to-long promotion and Boolean
conditions. Assignments to CONNECTED, declarations using its name, function-call
syntax and string misuse are refused. A standalone `connected` line is accepted
but emits no operation, matching the original compiler's observed behavior.
The frozen authored vectors are public; original executable inputs stay private.

## Implementation and checks

The new integer routing is maintained code and calls the existing recovered UART
getter. It does not poll the transport, dequeue input or schedule WHEN actions.
The existing WHEN carrier service retains its separate polling behavior. An
unavailable serial owner raises unsupported error3 and unwinds before assignment;
it cannot publish a false disconnected value or treat the backend's FFFF refusal
as a positive connection. The opcode table still has107 supported slots: this is
an operand implementation, not an additional opcode.

The [validation record](validation/aspect-connected.json) binds:

- The final2,430-case DOS compiler regression, including all22 original grammar
  cases. The earlier2,431-case run included a subsequently replaced test source.
- The1,130-case DOS8086 runtime suite,27,161 checks and zero failures. Six new ASX
  cases cover raw values, long/string conversion, conditions, bare-line behavior
  and unavailable-owner refusal with the prior destination preserved.
- Seven direct API checks with one queued byte: two carrier reads keep it queued,
  a deliberate read consumes it, then the modeled carrier falls. The first
  multi-command test was excluded because the native dispatcher drains input
  between commands, which does not isolate the getter's effects.
- Actual UART machine-code execution against declared CPU/IO models: all256 MSR
  values on COM1–4, exactly one port read per getter, unchanged queued data and
  no IO after close. This adds1,028 inputs to the1,136-input serial regression.
- Five actual DOS8086 production-runner cases with an independent TCP peer:
  N/S/H/B flow and real nested DOS compilation with the serial owner retained.
  Exact traffic, unread `TRAIL` return, vectors, PIC, MCR and ASIO guards pass.
  The DOSBox nullmodem holds DCD high; it does not prove physical carrier loss.

The source-only compiler is
`build/connected-compiler-final-20261108/ASPCOMP.EXE`, SHA-256
`902d39d2c4be34da9db2b63217f970d203cd07cf995476aef8d2d561c28a78d9`.
The standalone runner is `build/connected-runner-20261108/ASPECT.EXE`, SHA-256
`a2a20a0411d1155dd46877ded30be8020895d5b250b7706aca8aa2f1b73f8353`.
The [recorder](../standalone/record_aspect_connected.py) checks current source
manifests, the frozen oracle, actual DOS compiler files and runtime receipts.
Builds and tests use the pinned Nix environment through `./tools/dev --command`.

## Remaining work

The full-child integration follow-up below now passes selected parent-session
checks but fails capacity admission. Resolve that failure before producing a
separately identified package. The
prepared [Chat-mode hardware-test package](CHAT_MODE_PACKAGE.md), deployment
selection and installed machine remain unchanged. Physical modem/SIP/BBS tests,
other missing builtin operands and full ASPECT feature parity remain open.

## Full-child follow-up: capacity gate remains open

The [full-parent receipt](validation/aspect-connected-parent.json) binds the
unchanged Chat-mode parent to new full child
`96ea98c9537f3d54b20d02fd8a5f5ec93849f2b01e0485b1a0b867ad199671ab`
and GET-enabled compiler. Resident near code is63023 bytes, DGROUP43712 and
stack8192. The exact DOS minimum including PSP is136528 bytes,48 more than the
preceding child; no stream, object, field or stack capacity was reduced.

Eight full-parent checks pass under386/UMB diagnostic placement: startup and
EXECUTE source compilation, plus string/integer/long input, cancellation, float
refusal and malformed operands. The string case retains a real open FILE.
Authored guards check raw CONNECTED128 and long129 before and after successful
fields and in source chains. These use the owned synthetic serial peer, not an
analog modem or observed electrical DCD transitions.

The first source run under8086 with the diagnostic observer in conventional
memory fails before ASPECT loads: the observed131200-byte largest free block
is smaller than the136528-byte child minimum. Moving that observer to UMB in
the existing386 fixture permits both source cases to finish. This is a test
layout distinction, not a change to physical machine configuration.

The heavier unobserved8086 workload fails. It holds six512-byte file buffers,
runs three real graphics DOS children with WAIT, switches VT220/ANSI, and checks
six-slot/missing-file recovery. A paired386/UMB trace compares the same parent
and byte-identical authored scripts against the previous child in an isolated
export of committed source base a234c8a. **Both children fail this workload.** This
is an existing capacity gap; earlier successful package/connection checks did
not establish this combined workload for the compiler-bridge child.

Both traces observe real DOS AH4A memory-growth refusals, error8 and maximum8607
paragraphs. The previous child's failed requests are8620,8628,8620,8620; the new
child requests8623,8631,8623,8623, exactly three paragraphs more. Both show child
exits7,0,0,7; the first/final scripts fail on FPUTS with a null file slot, native
error4. This corroborates a memory shortage before writing, rather than proving
a UART or carrier bug. A separately built128-byte heap-growth variant also fails
the unobserved8086 workload; changing allocation granularity alone is insufficient.

The new child is **not eligible for package promotion**. Next work is to reduce
resident memory or safely recover available memory while preserving all six
buffers, stacks, native VM limits and parent-service behavior, then repeat this
exact workload and the source/GET checks. Broader BBS/package tests must use the
eventual accepted child bytes. The prepared package, deployment selection,
installed machine and private files remain unchanged.
