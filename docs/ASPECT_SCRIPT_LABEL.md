# Current script names in native STATUS

An accepted compiled-file open now publishes its uppercase DOS basename to the
parent and refreshes native STATUS, including after EXECUTE. The parent retains
a separate13-byte label plus a validity word. It does not change the invocation
filename, directory entry, saved configuration or child's filename storage.
Preparing or revoking a renderer lease clears validity. A failed label transfer
or STATUS preflight retains the previous label; an ordinary STATUS without a
published label uses the invocation filename as before.

This is a maintained application operation implementing the native D4D0 label
behavior recovered in [ASPECT_CHAIN_NATIVE.md](ASPECT_CHAIN_NATIVE.md). The
original loader copies the accepted basename to D464 then calls2FB8. The new
parent/child transport is not an original PCPlus protocol.

## Capability and ownership

ASIOv4 remains48 bytes. Its renderer capability is now **4**, and the ten-byte
client record also requires version4. Versions1–3 are rejected before UART
admission. Deploy the matched terminal and child from the DOS package.

Request6 takes the same duplex snapshot scalar as STATUS: FFFF uses the parent
setting,0..255 selects the child's temporary override. It admits only the
active child PSP/DS under the checked bridge and a live UART lease. No child
pointer is sent. During this synchronous request, callback7 pulls consecutive
label bytes0..12. The child requires an ordered, complete transfer through the
terminating NUL. Unsolicited, repeated, skipped, out-of-range and post-terminator
pulls fail; the normal error callback separately reports typed child failures.

The parent stages at most13 bytes on its own checked stack. It accepts1..8 stem
bytes and exact `.ASX`, rejects path separators, control characters and extra
dots, and checks callback errors before using each scalar. High CP437 bytes are
retained. It then updates the owned label and calls the existing native status
renderer. A drawing-preflight failure restores all13 old label bytes and its
validity word. The child's changed duplex is a drawing override; the parent
setting is not adopted. No raw UART byte is consumed to obtain a filename.

## Verification

```sh
./tools/build test-aspect-script-label-client test-aspect-script-label-parent
./tools/build test-aspect-chain-status-dos
```

The linked CPU tests cover37 child cases and29 parent cases. The parent test
executes the actual bridge, client MCB validation, bounded label parser,
rollback and native STATUS rendering. Admission-success, DOS62, child scalar
callback and MSR are explicit test boundaries. The child tests execute the
actual synchronous callback and stack lifetime with a declared parent endpoint.
They do not substitute for actual DOS application tests.

Two actual DOS terminal/child cases check a replacement's `NEXT.ASX` status row
in full and half duplex. BREAK1234 and WHENCASE survive replacement; returning
from the child preserves parent keyboard/query/history, IRQ/JFT and owner
checks. Half duplex is restored to full after the sampled PAUSE and before the
synthetic password. The test uses only local authored credentials.

The ordinary85-case linked STATUS suite, renderer client/parent admission,
BREAK inheritance and production DOS CLI regressions remain separate checks.
The five-case synthetic DOS callback fixture now handles version4 label pulls.
It uses fixed12000 DOSBox cycles and applies its callback stimulus once, so an
error message cannot overwrite the first callback observations.

An additional max-cycle run exposed an existing end-wait pacing limitation,
also reproduced with the pre-label e464f08 executable: bounded calibration can
return pacing5 at unconstrained emulator speed. Its error output began with A,
which retriggered the old fixture and obscured successful first callbacks. Both
failed observations and the diagnosis are retained in ignored local history.
The production calibration bounds have not been relaxed, and this checkpoint
does not claim unconstrained-cycle timing compatibility. Physical modem timing,
DOS ASP compilation, broader UI/services and all F01–F16 gates remain open.
