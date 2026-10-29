# Foreground directory resource preflight

The opt-in `--directory-resource-owner` build connects the Alt-D selection
preview to the existing PROGRAM serial handoff. Press **R** while disconnected
to check and stage the selected entry's KEY/KBD resources. The notice reports
success or failure, then restores the terminal. This is a resource preflight;
it does not apply the selection or dial. It retains the LoC.6 splash/version
and has not been installed on the card.

Build with the pinned toolchain:

```sh
./tools/dev --command python3 standalone/package_special_edition.py --build \
  --custom-irq --directory-resource-owner --output build/resource-owner-package
```

## Ownership and publication

The directory page occupies the first 2,788 bytes of the inactive frozen
history allocation. Its proposed selection occupies the next 1,190 bytes;
the complete KEY/KBD bundle uses the following 1,624 bytes. The R handler
admits PROGRAM kind 6 before releasing the preview and all ancestor popups.
Pending/active PROGRAM admission keeps other frozen-history consumers out.
This also works when Alt-D was entered through the reference or browser.

The foreground worker requires the admitted PROGRAM owner, closed popups,
disconnected session, inactive parser and drained transmit queue. PROGRAM
pauses the mouse, lowers RTS, masks the UART IRQ, disables IER and restores
the pre-PCPlus vector before resource DOS calls. The actual-session proposal
and accepted in-memory PRM are checked again before reads. Their 16-bit seals
detect accidental damage; they do not establish security, external freshness
or a transactional generation identity.

Original CLI resource identities take precedence through the existing request
factory. Missing directory bindings reset to validated network defaults and
disabled actions. Invalid resources leave the entire output bundle unchanged.
Readers use non-inheritable handles and shared file reservations. An uncertain
close/release keeps the independent resource claim held and blocks DOS EXEC,
even after the temporary frozen-buffer lease is released. No active target,
serial settings, keymap, actions, paths, translation or accounting are published.

## Conventional memory and child return

This variant needs 409,872 module bytes with both 63,000-byte history allocations
retained. Near DATA/stack uses 64,976 bytes; resident CS has 208 bytes free.
The complete frozen allocation and its 494-byte row index are placed last.
An eligible PROGRAM child may temporarily relinquish exactly 63,504 bytes.
The live history ring, display buffers and all other code/data stay resident.
An active viewer, snapshot, popup or resource worker prevents that loan.

The small DOS mouse-state block uses last-fit allocation so it cannot split
the contiguous loan from the remaining conventional arena. The original DOS
allocation strategy is restored immediately, including allocation failure.
Uncertain restoration retains its identity, refuses further allocation/EXEC,
and gets one cleanup attempt during shutdown. This uses DOS 3+ Int 21h/58h;
the [Microsoft MS-DOS Encyclopedia](https://msarchive.pcjs.org/mspl13/msdos/encyclopedia/section5/)
documents get/set strategy and first/best/last-fit values.

After a child returns, parent DS/SS/SP are restored and the UART is quieted
before trap restoration can enable interrupts. The full parent allocation is
then reacquired on success and error paths. Reacquisition failure preserves
the first DOS error, requests controlled exit and refuses another EXEC. It
does not continue using memory that DOS may have assigned to another owner.

## Validation and limits

The machine-readable [receipt](validation/directory-resource-owner.json) binds
the candidate and its evidence. Exporting only committed sources from
`6e3509e` into an empty tree with no ancestor Git metadata rebuilds all ten
package files byte for byte from 768 source inputs. The three ordinary, LoC.6
and CLI-only control binaries remain exact. Seven actual DOS 8086 workflows check valid
resources, each malformed format, defaults, both nested popup entry paths and
a deliberately damaged queued proposal. Passive observers verify every
resource DOS call has DS=SS and the quiesced UART/vector/owner state. The fault
case explicitly injects one bit at the mouse handoff; it is separate from the
passive cases. Active settings and original files stay unchanged.

Linked-instruction checks cover 14 memory-loan/failure cases, 24 mouse allocation
and cleanup cases, and eight damaged ABI/relocation controls. These model DOS
boundaries and UART registers; they are not physical hardware tests. Actual
packaged START compiles a nested ASPECT source, runs it and reopens the frozen
viewer afterward. SETUP, strategy restoration, private-file preservation and
the existing directory/snapshot checks have separate evidence.

The initial package exhausted memory during nested compilation; moving the
mouse block high and lending inactive frozen storage corrected the observed
fragmentation. The first online owner check exposed an overwritten refusal
notice; its text now has a dedicated row. Failed artifacts remain under ignored
build storage and are not counted as successful validation.

Selected-entry adoption, translation/script staging, retiring old-selection
accounting, transactional UART/profile/resource publication and dialing remain
unfinished. The full F01–F16 plan, real modem/SPA2102 acceptance and card
deployment remain open. Software ENiGMA evidence cannot establish perfect
rendering of every screen or analog/file-transfer compatibility.
