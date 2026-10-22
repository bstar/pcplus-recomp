# PROGRAM after observed carrier loss

The current parent can send a proactive XOFF in modem command mode when a local
PROGRAM helper is launched after an observed carrier loss. This is a distinct
path from the already guarded PROGRAM return and ASPECT close paths. The
baseline still reconnects, but the isolated XOFF prefixes the next ATZ and the
virtual modem returns ERROR rather than OK before accepting the subsequent dial.

This is now reproduced, rather than inferred from source:

- Four linked cases in build/program-offline-flow/baseline-01 exercise actual
  parent connection polling and PROGRAM execution. SOFT/BOTH online controls
  send XOFF then XON; after observed high-to-low DCD the old build sends XOFF
  alone. DOS/BIOS/UART boundaries are modeled in these component cases.
- Two actual 8086 DOS cases in build/program-offline-modem-dos/baseline-03 use
  a real owned TCP socket close through DOSBox-X's virtual modem. The helper
  reads the parent state after launch: state0, status6, carrier-seen1, and
  UART XOFF-sent1. Its inherited UART has interrupts released. It then changes
  UART/video state, and the parent restores both, redials and handles ordinary
  manual input plus an ANSI query on the second connection.
- Independent raw verification checks both old-product cases: exact initial
  and second BBS streams, two carrier transitions, child samples, helper tail,
  complete hardware restoration and modem commands. The second initialization
  is exactly XOFF+ATZ, with ERROR. No product state or MSR result is injected.

The baseline parent is
6075bc182ae9821ae077e78a56a42741d81016cb82e79365556c36ee4782f62a.
The actual DOS fixture does not launch ASPECT or depend on an original program.
All contacts, commands and helper artifacts are source-owned synthetic data.

Earlier attempts are preserved: baseline-01 stopped before DOS because a private
symbol was not in the map. Baseline-02 reproduced the defective command but
failed its fixture expectation because full-duplex manual input does not echo
locally; the fixture consequently waited for the wrong cursor reply. Baseline-03
uses the actual full-duplex cursor position and independently verifies the
whole wire. Neither earlier attempt is accepted as a passing baseline suite.

## Pending correction and acceptance

Before issuing proactive XOFF, consult the existing far carrier-policy service.
For an enabled MODEM session whose parent observed carrier high, a currently
low DCD must retire old flow and proceed without introducing a new pause.
Online, DIRECT and untracked links retain their established policy. Normal
helper execution, error recovery, UART/vector/video restoration and command
construction must stay intact. Measure both normal and mouse code capacities;
the preceding mouse product has only 14 near-code bytes spare.

The parent source is intentionally unchanged while the current transmit-wait
audio test owns frozen admission inputs. Once that exact run is terminal,
apply the correction, require the linked and actual DOS cases to pass without
their baseline flags, compare unchanged BBS streams and clean ATZ/OK, then run
current process/PROGRAM, carrier/flow and BBS regressions and source rebuilds.
The prepared auditor requires old/new product identities and raw child samples.

The correction, local Script launch after loss, other helper/error paths,
initially-low/transient DCD, manual hangup/cancel, sustained flow pressure and
physical UART/modem acceptance remain open. This does not close a full F01–F16
application gate.
