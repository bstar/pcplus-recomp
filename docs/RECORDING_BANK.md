# Recorder code-bank integration

The [bank validation record](validation/recording-bank.json) binds the recorder
core and publisher to the terminal's distinct CONFIG_CODE segment. The DOS
backend remains resident; its nine far-cdecl callbacks use near DS=SS arguments.
Fourteen public recorder/publisher functions, three compiled adapter far calls,
their relocations and all nine callback segments/relocations are checked in
the serialized terminal. This links the libraries; foreground recording is
still unfinished.

Processed-text capture now executes in CONFIG_CODE through eight declared
near-cdecl public adapters. Their counts include the three-word path/ticks begin
and two-word ticks poll. Calls within the implementation use bank-local names;
five explicit services enter the resident checked file owner. Buffer, clock,
cookie and diagnostic state retain their existing near layout and behavior.
The recorder also uses a typed compiler-register strlen service alongside the
existing C-library bridges. The build respects explicit bank membership before
its generic ASPECT-directory segment assignment.

The actual DOS publisher test can build both ordinary and banked variants.
Both run the same16 publication, shared-owner, recovery, compiler and UART
replay cases. Every banked process records distinct publisher/core and resident
callback code segments at runtime. Status words, ASP source, compiled ASX,
retained recovery files and observed wire bytes match the ordinary variant.
One initial generated diagnostic bridge failed NASM because a macro alias was
not undefined before a new definition; the failed cohort is retained. The
accepted banked campaign uses the corrected adapter declaration.

The current source-only terminal is
`ea0fa0ad72cd9a2d7d79a13cbe4b33b0960001410740c56095051cad269c290e`.

| Evidence | Scope |
| --- | --- |
|16 ordinary and16 banked DOS publisher cases |Real DOS file operations, deliberately injected read-only handle and target races, maintained DOS compiler and exact UART replay on owned synthetic media. |
|11 actual terminal DOS capture scenarios |Default/explicit paths, cancel, append across DOS1A, pause/resume, CR/LF, periodic and shutdown flush, buffer boundaries, read-only refusal and XMODEM coexistence. |
|24 linked capture inputs |Actual logger, file owner and PROGRAM paths with modeled kernel/hardware boundaries. |
|27 linked history inputs |Canonical exclusions, append, cancellation and file/child fault models. |
|78 linked ZMODEM workflows |Existing framing, storage, recovery and transfer ownership against the rebuilt terminal; modeled boundaries. |
|518 ABI corruption checks |Declared entry frames, callback targets/segments, far-call relocations, initialized reservation state and bank extents reject damaged evidence. |
| Three linked far-code cases |All controller entry paths, resident printer services, DS=SS, stack restoration and real UART ISR/IRET execution with modeled hardware; six damaged images/layouts reject. |

There are150 checked bridge pairs, including94 configuration pairs. The normal
terminal leaves506 resident-code bytes and272 near-data bytes free. Moving
capture recovered570 resident-code bytes; the publisher backend and new bridges
consume some of that space. The publisher/core add352 near-data bytes, including
their constants and callback table. The326-byte recorder owner has **not** been
allocated in the terminal. Storage work is required before adding its UI state;
the current library linkage does not establish usable foreground recording.
The mouse variant also rebuilds and passes the static bank/memory audit, leaving
356 resident-code bytes and224 near-data bytes. This is build evidence; its
runtime behavior is outside this checkpoint's terminal campaign.

The later [stable owner checkpoint](RECORDING_OWNER.md) resolves the near-data
allocation and adds initialized state and assembly lifecycle calls. Next add Record
start/stop/cancel/recovery controls and foreground taps. Record only successfully
emitted user/binding bytes and intended received prompts; guard transfers,
scripts, child programs, setup, port changes and exit/error paths. Then run
actual foreground recording, DOS compilation/replay and affected BBS workflows
using those resulting binaries. Older BBS/audio records retain their historical
binary scope. Physical modem testing and all full F01–F16 gates remain open.
