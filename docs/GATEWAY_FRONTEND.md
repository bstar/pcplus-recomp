# DOS Gateway foreground integration

`--gateway` enables Alt-F4 and the DOS Gateway command/reference-menu action in
the normal application. It requires the composed display and mouse owners and
implies the live UART, private-file, JFT and empty-tail COMSPEC prerequisites.
This is a maintained integration of the recovered Gateway contract, not a claim
that every original UI or DOS behavior has been recovered.

The command interpreter receives an empty tail. `EXIT` returns directly to the
terminal without PROGRAM's return-key prompt. The retained IRQ owner keeps
receive and flow service active during DOS execution. Capture/HOLD and private
file descriptors use the separate preservation transaction rather than PROGRAM's
close/detach policy. A successful directory change remains current during the
application; orderly application exit restores its startup directory.

## Foreground ownership

Requests refuse incompatible parser, transfer, recording, viewer, menu, file,
modem-transition and display ownership. BIOS mode3, 80 columns and page0 are
required. Launch revalidates those owners after queued TX and printer output
drain. A 36-BIOS-tick deadline is renewed only by actual TX/printer progress;
repeated Alt-F4 requests do not reset it. Midnight wrap is handled. Waiting
preserves ordinary BIOS typeahead for COMMAND.COM; cancellation remains local.

The frontend retires existing notices, saves the full display, pauses the mouse,
then brackets the file transaction with the live UART lease. Raw EXEC retains
its IF0 repair and trap boundaries. Return restores the display and mouse,
then polls the existing connection state machine. Modem DCD qualification
therefore remains in the connection owner rather than publishing status from
an interrupt handler. A recovered line cannot undo an actual child hangup.

Failed interpreter lookup/EXEC returns to a usable terminal. Unrecoverable
serial, overflow, display and mouse faults stop through the existing shutdown
policy. Uncertain file ownership takes a separate quarantine branch that skips
stream/accounting cleanup. The existing final lifetime guard can retain the
parent instead of freeing uncertain ownership; this is deliberate fault
containment, not ordinary successful exit.

The new initialized state is20 bytes in retained FILE_CODE, with no additional
DGROUP state. The memory validator checks its sentinel, retained extent,
non-overlap with other owners, banked entry points and both shutdown quarantine
calls. Full static-parent retention reduces the memory available to DOS children.
A child that modifies arbitrary parent memory is not isolated.

## Validation

The receipt is [gateway-frontend.json](validation/gateway-frontend.json).

Linked CPU tests execute the actual foreground, C/ASM/file/UART/process/display
and mouse code against declared kernel/BIOS/hardware boundaries. They cover
25/28/43/50-row graphics-child returns, repeated same-process Gateway use,
admission guards, TX/printer deadlines, cancellation, typeahead, failed
lookup/resize/EXEC and fault containment. The file-quarantine test executes
actual application shutdown and checks that stream cleanup is skipped and the
final lifetime guard retains the parent. Corruption recovery is modeled; no
live DOS-kernel corruption test is claimed.

Three actual DOSBox-X workflows use an8086 with FPU disabled: direct Alt-F4,
the reference menu, and a real COMMAND.COM session. The latter runs a batch
that creates a directory, changes directories and invokes a child. During the
child, a serial peer sends3200 bytes and observes XOFF/XON. After return it
verifies the parser responds without a return key. An independent INT10/VGA
observer compares the full80x25 frame, cursor/shape and mode. These workflows
also verify startup-directory and hardware/vector restoration on final exit.
The child may change to graphics mode. Other physical row heights are covered
by the linked model, not this actual DOSBox matrix.

A fresh Git-free tree reproduces the executable from591 declared public source
inputs. Disabling only the frontend reproduces the preceding UART-only parent
exactly. UART54, file-owner40, private-handle56 and interpreter-lookup33 component
cases pass against the composed frontend image.

The later [stock-editor Gateway tests](GATEWAY_EDITOR_BBS.md) also pass actual
Enigma and Synchronet editor returns, full-frame/cursor restoration and all 1,920
logical cells per peer. They use the same executable with a synthetic graphics
child and explicitly staged proxy settings.

The later [composition checks](GATEWAY_COMPOSITION.md) pass five actual Gateway
capture/HOLD/PRN workflows, normal-parent ANSI/VT220 loss/redial, and independently
audited stock Enigma cancellation/cleanup/exact binary retry on this executable.
The latter two groups regress the enabled image without opening Gateway during
those operations.

## Remaining acceptance

Beyond those selected editor returns, the normal frontend still needs full
online Enigma/Synchronet interactions and further capture/HOLD/printer owner
combinations, sustained real-peer traffic, wider transfer/cancellation and
carrier-loss/reconnect coverage through the complete route.
Microsoft DOS6.22 and physical Boca/SPA2102/SynthModem acceptance remain open.
These tests do not prove physical flow-control timing or perfect BBS rendering.
No physical files, deployment selector, networking, boot configuration, adapter
or services were changed for this checkpoint.
