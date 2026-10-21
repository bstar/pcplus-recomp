# Online exit uses hangup

Alt-X previously called the maintained connection cancellation operation with
AX=0 even when state6 was online. Cancellation sends MI_ABORT_CHARACTER, which
is Escape in the lab profile, then drops/restores DTR. The BBS receives that
Escape as application input and starts its editor menu while the terminal is
exiting. Alt-X during state9 also cancelled an already-running configured hangup.
These are maintained controller defects, not claims about the original PCPlus UI.

The corrected controller selects configured hangup for an online Alt-X, just
as Alt-H does. An empty hangup string uses the existing configured DTR operation
without sending a dial-abort character. Alt-X during an active hangup marks exit
pending and leaves its sender/deadline intact. A hangup timeout proceeds to the
configured DTR cleanup without falling through the dial-abort sender. Dialing
cancellation and its configured abort character remain unchanged.

Successful online exit now reports hangup status5 rather than cancellation4.
Hangup timeout retains status3. DTR behavior still follows the profile; no Boca
command, modem capability or physical control-line result is assumed.

## Linked regression

The [component receipt](../../docs/validation/online-exit.json) retains the
failing old-product counterexample and five passing fixed-product cases with
20 checks: configured online hangup, empty online hangup, dialing abort,
in-progress hangup and CTS recovery after the hangup deadline. Tests execute the
actual linked keyboard/connection/sender/UART instructions. Only BIOS clocks,
keys and port hardware are modeled. The CTS case recovers after the configured
three-second deadline and verifies that no late Escape leaks onto the data line.

The existing eight connection groups/46 inputs and four far-ABI groups pass.
The [five actual DOS connection cases](../../docs/validation/online-exit-dos.json)
also pass: connect/banner preservation, busy/timeout aborts, configured hangup
and explicit redial, with normal exit, hardware snapshots and profile checks.
Both old/new maps have DGROUP extentFD40h (64832 bytes), retaining DS=SS. The
modem code grows and moves subsequent physical segments; the far bridge,
relocations, nested PRINT/MODEM transition and UART ISR/IRET checks cover that
layout. The default build remains source-only. The new regression is included
in test-terminal; its default output uses a fresh timestamp directory.

The existing stalled Alt-X test now allows the configured hangup deadline plus
DTR wait for online/in-progress-hangup cases. Dial cancellation retains its
shorter40-poll bound. This is the intended policy change, not a global timeout
or CTS relaxation. Physical modem and complete application acceptance remain open.

```sh
./tools/build terminal
./tools/dev --command python3 standalone/check_online_exit.py
./tools/dev --command python3 standalone/check_connection.py
./tools/dev --command python3 standalone/check_modem_far_live.py
./tools/dev --command python3 standalone/test_connection_dos.py
```

## Socket-close and actual audio evidence

The [controlled emulator receipt](../../docs/validation/dosbox-socket-close.json)
uses the pinned DOSBox-X2026.07.02, real DOS UART reads and strace from the pinned
Nix modem shell. A drained256-byte payload closes with EOF; an immediate normal
exit after one UART/TCP byte from65536 bytes leaves network data unread and the
peer observes ECONNRESET. The normal DOS witness is checked in both cases.
Earlier marker and delayed-exit attempts are retained: a delay let DOSBox read
all network bytes even though the DOS program consumed only one UART byte.
Network socket consumption is therefore distinct from application consumption.

The [pre-fix audio diagnosis](../../docs/validation/synthmodem-exit-diagnosis.json)
records actual editor06 with common-clock serial-input/BBS-relay events and
owned-emulator syscall tracing. It has no reset and all47983 submitted bytes are
reconstructed as exact socket reads. It still fails the two complete-downstream
checks for the same616-byte suffix. The final input is Escape, about1011ms
before close; all missing suffix bytes were observed at the BBS relay about297ms
after that input and714ms before close. They belong to the editor Escape-menu
reply. These are observed relay timings, not internal server-generation clocks.

This explains why eliminating the reset alone cannot establish full delivery.
It also supports removing the unintended exit Escape. The syscall-traced call
has different scheduling and does not retroactively prove why editor05 reset.
The untraced fixed-product editor07 repeat is the next actual DOS/audio gate.
Neither the reset nor complete-downstream checks are waived, and the previous
intermittent guest-decoded insertions remain unresolved.
