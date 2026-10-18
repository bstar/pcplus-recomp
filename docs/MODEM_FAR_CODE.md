# Static modem code segment

The maintained modem connection controller and paced sender now share an
independent `MODEM_CODE` segment and `MODEM_GROUP`. The resident `_TEXT`, modem
code and dedicated `PRINT_CODE` controller have distinct CS values. DATA and
STACK retain the existing near-pointer ABI, DS=SS and current state layouts.
No original executable or overlay image is a build input.

Compared with the serviced-BREAK checkpoint `30585e2` / `c0a9cbaa`, resident
code falls from63,490 to62,306 bytes:1,184 bytes freed and3,230 bytes remaining
below64KiB. The modem segment contains1,467 bytes, including far thunks and
module alignment. The added bridge code/padding increases the loaded module
from93,786 to94,074 bytes; this relocates capacity rather than reducing total
memory use. Shared DATA/STACK stays52,384 bytes. Further code/data migration and
full startup/UI reconstruction remain open.

## Entry and callback contracts

`src/terminal/modem_abi.inc` declares eight public register/no-argument entries:
connection prepare/start/poll/receive/cancel/exit and sender start/poll. Existing
resident names remain near-call entry thunks. Each CALL FAR enters a modem
wrapper, which near-calls the implementation and RETFs to the resident wrapper.
Internal modem-to-sender calls stay near inside the shared modem CS.

Ten namespaced callbacks reach resident register services: clock, call
accounting, matcher reset, notices, nonblocking UART write/RX clear and
BREAK/macro/PROGRAM cancellation. Separate callback names prevent a far module
from accidentally near-calling another module's thunk or defining duplicate
symbols for a shared resident service.

Four additional services have explicit caller-cleaned word arguments:

| Resident target | Words copied | Result/behavior retained |
| --- | --- | --- |
| `modem_expand_bounded` | 4 | Source/destination near offsets and capacities; AX/CF validation result |
| `modem_response_classify` | 3 | Response/current baud/autobaud; AX/DX/BX and CF |
| `uart_set_baud_divisor` | 2 | Low/high rate words; actual divisor and original volatile-register behavior |
| `modem_responses_feed_bounded` | 1 | Byte word, matcher cursor changes and AX/CF |

The far implementation pushes its ordinary argument words and CALLs a near
far-service thunk. The resident adapter saves BP and copies the words from
BP+8 onward into a new ordinary near-call frame. After the actual target
returns, `LEA SP,[BP]`, POP BP and RETF release only the copies and preserve
returned FLAGS and registers. The original caller still owns/cleans its slots.
The UART setter uses DS:BX stack access; DS=SS remains essential.

The macro accepts only declared1..4-word, BP-preserving, plain-RET targets.
It does not provide variadic calls, callee-cleaned RET-N forwarding, generic
callbacks/function pointers or a general-purpose compiler far-C ABI. Stack
arguments are copied by value; these targets do not write back into the
original argument slots.

## Build and retention guards

The existing ordered CODE/FARCODE/DATA/BSS/STACK link and explicit groups prevent
AUTO grouping from merging the modem CS with resident or printer code. The
builder checks all44 bridge pairs:22 printer and22 modem pairs. It validates
actual CALL FAR encodings and MZ segment relocations, near target displacements,
RETF/RET paths and the exact declared argument-copy/LEA cleanup frames. All
executable segments must fit64KiB, be serialized in the MZ, avoid each other,
DATA and far UI/storage, and lie within retained parent memory.

The actual DOS PROGRAM child now records56 bytes /28 words, with status63 when
all checks pass. Along with the existing native-storage, snapshot and UI-frame
checks, it records modem CS/extent and sums every relocated modem code byte
before and after allocating/filling a disjoint16KiB DOS block. Both modem and
printer code sums must survive; the parent then resumes operation and restores
sampled UART/PIC/IRQ state.

## Verification

```sh
./tools/build terminal test-terminal
```

`check_modem_far_live.py` compares the actual far-service path with each actual
resident target for successful/error expansion,390 classification inputs,
five response-byte boundaries and nine baud settings. It checks returned
registers/FLAGS, original argument slots and stack balance. The baud setter's
volatile BX retains part of its actual stack address, so only that irrelevant
value is excluded from direct/bridged equality. Existing independent connection
tests verify the command/response policy and actual divisor behavior.

Other linked cases visit all eight public entries, dial/connect/autobaud/hangup,
and nest PRINT → resident transport → MODEM calls. A modeled maskable UART
interrupt executes the real recovered ISR and IRET back into interrupted modem
code; the byte is retained or printed exactly once and execution returns to
resident CS. Nine deliberately malformed modem images/maps must be rejected,
including argument offsets, wrong returns/targets, missing relocation and
missing/oversized segment declarations. Existing printer rejection tests remain.

The full terminal regression, actual DOS allocation child and independent
source-only rebuild are bound to the selected executable in
[the modem segmentation report](validation/terminal-modem-far-code.json).
The current [BBS checkpoint](../lab/bbs/modern-compatibility.md) repeats actual
editors on the same7a0ea9d3 runtime: Synchronet passes; ENiGMA immediate Home/Insert
failures persist while explicit30ms buffering passes the paired checks. Its
first ENiGMA harness preflight failure remains separately recorded. These checks
are static real-mode segmentation evidence; dynamic overlays, complete original
application startup and physical UART/modem behavior remain separate work.
