# Experimental Chat foreground core

`--chat-frontend` wires the loaded Chat session into original Alt-O entry,
keyboard dispatch, top-level receive admission, idle service and screen-owner
retirement. It requires the adapter/presentation/storage/loader options and the
banked keyboard. It is an experimental development build, not a selected release
or full original Chat acceptance.

The core currently selects buffered sending. It uses the accepted parent duplex
and newline settings and snapshots the accepted input translation table at
entry. Immediate sending is component-tested but has no foreground setting yet.
Original Chat Help6D00 and Alt-number direct TEXT are explicitly refused with
internal diagnostic7F01; they do not accidentally execute a different general
KEY action. The Alt-Z Chat item remains unavailable. Those continuations and
configuration/UI work remain part of the goal.

## Ownership and lifetime

Entry resolves `PCCHAT.OVL` beside the launching executable using the validated
DOS environment trailer, independently of the current directory. It refuses
pending private typeahead and uses the existing common storage-acquire guards.
Module identity verification, DOS4B03 loading and all pane/session storage stay
in the established loader/module contract. Failure releases the acquired lease.

The18-byte handle is near; a nonzero initialization cookie explicitly clears it
before use, without assuming DOS zeroes BSS. The11-byte filename and2-byte cookie
are also near. Session/context/request/translation storage uses frozen-workspace
offsets12288/13000/13200/14000, outside the8192-byte module window. The existing
view frame backs up the physical screen. There is no new heap or frame.

A keyboard peek can hold a pending key before the actual BIOS read while prior
effects remain outstanding. Escape also waits for queued output; Alt-X/Alt-H can
retire unfinished Chat and resume ordinary dispatch. Entry preserves the existing
manual-init handler and auto-download flush ordering. A received byte is not
dequeued while the prior RX effects remain pending or presentation geometry is
invalid. The raw top-level byte reaches Chat after modem/control recognition
and before ordinary monitor/controller/transfer/ANSI input. Chat performs its
translation, pane rendering and real history/log effects instead of invoking
the terminal parser. UART flow, queued sending and the ordinary foreground loop
continue running.

Idle work uses the existing bounded session scheduler and real parent sink.
Native status polling already defers to the screen owner. Stop aborts/restores,
unloads and then explicitly releases storage. A busy or changed-geometry refusal
keeps the owner; a notice does not draw over that retained lease. Restoring the
admitted geometry allows retirement. Broad notice/trap/error/mouse interactions
and all physical timing still require further acceptance.

## Actual DOS evidence

The overlay-parent composition invokes actual parent C/assembly and loaded
module instructions on the parent DS=SS and declared stack. Three entries at
one module location cover pending-key hold, TX refusal, RX progress across two
idle turns while TX refuses, native queue/history effects, Escape, emergency
exit handoff and changed-page quarantine/recovery. Help/TEXT refusal preserves
the local buffer. Every saved cell is restored; PSP/JFT/free-memory checks pass.
This fixture does not perform a BIOS keyboard dequeue or UART delivery itself.

The separate normal-main test does use real BIOS keys and the DOS UART with a
synthetic Hayes peer. After acknowledging the original splash, it enters Chat,
types a buffered line and submits it over the UART. That line triggers incoming
text plus a CPR request. Chat does not parse/reply to that request. Escape then
restores the underlay; ordinary typed keys trigger text plus another CPR, which
the normal parser answers. Exactly two CPR replies, including startup's reply,
and the final video demonstrate ownership and return; this is not inferred from
normal process exit alone. Hardware and imported settings are restored.

A targeted negative test found a real order bug in the first frontend image:
a held auto-download prefix expired after Chat opened, painting into the Chat
screen and disappearing from its restored underlay. The fix moves Chat dispatch
after the existing manual-init handler and input flush. With identical PRM and
key sequence, the restored first row changes from `FIRST BYTE SAFE BACK` to
`FIRST BYTE SAFE*BACK`. Only application source `transport.asm` differs across
that pair; memory dimensions and flags are identical. All643 baseline source
files are retained under ignored storage for the failed regression.

Earlier normal-main attempts omitted the splash acknowledgement. A passive
observer showed that Alt-O had been consumed before the terminal reader was
active. Those captures are invocation failures, separate from the product order
bug; the corrected ordinary tests use no passive observer.

Parent `5875536a` uses479408 minimum module bytes/29978 retained paragraphs
including PSP, near65504 and resident CS65528. The frontend C contribution is
839 code bytes plus31 data/BSS bytes; register bridges contribute240 far-code
bytes. Alignment makes the total increase1168 minimum bytes and16 near bytes
over the preceding sink build. Existing capacities/stacks and compiler profile
remain unchanged. Six buffered ASPECT streams across three DOS children and all
54 linked storage cases still pass. Disabling the frontend reproduces parent
`c1b3faf8` byte for byte.

The corrected image also passes ordinary stock Synchronet editor/external-viewer
return in its existing386/UMB helper profile, and Enigma's8086 carrier-loss,
same-process redial, two ASPECT logins, partial-file cleanup and exact65539-byte
retry with the established150-second test wait. An independent raw-wire audit
checks CRCs, completion/control exchanges and session boundaries. These runs
exercise normal BBS paths with Chat inactive; the synthetic test above is the
connected Chat workflow. No SIP/audio/analog acceptance follows from either.

A647-file clean public export reproduces parent/module/header and direct host/
result exactly, and independently repeats both normal-main workflows. Original
executables, private settings, prior objects and ancestor Git are absent.
Clock-sensitive full main captures are not claimed byte-identical. The
[checkpoint receipt](validation/chat-foreground-core.json) binds these results
and the corrected image's BBS regression evidence.

```sh
./tools/dev --command python standalone/test_chat_frontend_dos.py \
  --terminal build/PARENT/TERMINAL.EXE --output build/NEW-direct-core
./tools/dev --command python standalone/test_chat_main_dos.py \
  --terminal build/PARENT/TERMINAL.EXE --output build/NEW-main-core
./tools/dev --command python standalone/test_chat_main_dos.py \
  --terminal build/PARENT/TERMINAL.EXE --output build/NEW-prefix-core \
  --pending-prefix
```

Finish original Help/direct TEXT, Alt-Z entry, send-mode settings and further
notice/trap/disconnect/error/geometry/mouse coverage; repeat final memory,
BBS/package and physical gates. Ordinary BBS regressions are not proof of
interactive Chat inside every BBS workflow. The earlier unattributed redial
miss remains open. No selected package, physical DOS PC or production
SynthModem/Enigma configuration changes.
