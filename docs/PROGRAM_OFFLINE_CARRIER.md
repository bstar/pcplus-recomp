# PROGRAM after observed carrier loss

The preceding parent sends a proactive XOFF in modem command mode when a local
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

## Corrected component

Before issuing proactive XOFF, the parent now consults the existing far carrier-policy service.
For an enabled MODEM session whose parent observed carrier high, a currently
low DCD retires old flow and proceeds without introducing a new pause.
Online, DIRECT and untracked links retain their established policy. Normal
helper execution, error recovery, UART/vector/video restoration and command
construction stay intact. Normal/mouse products build with 154/6 near-code
bytes spare and unchanged 112/64 near-data bytes spare. Further resident code
placement is required before substantial mouse growth.

The source remained unchanged until the transmit-wait audio run finished and
its independent waveform/serial audits and outcome record passed. That audio
receipt retains its preceding parent identity; it does not accept the new parent.

The [independent correction audit](validation/program-offline-carrier.json)
accepts four linked inputs and the two actual DOS SOFT/BOTH comparisons. The
new child samples are state0/status6/carrier-seen1/XOFF-sent0, second ATZ gets
OK instead of ERROR, and both complete BBS streams stay identical to baseline.
All 60 existing linked PROGRAM inputs and42 carrier-policy cases pass; a fresh declared-source tree
reproduces 26 application/component products without originals.
Both existing modem-reconnect DOS cases also pass with the new parent.
All 13 actual DOS attached PROGRAM cases pass on the new external-render
parent; raw results are build/aspect-parent-process/offline-program-01/result.json.

## Local Script and current-parent regressions

The [source-bound local Script audit](validation/script-offline-carrier-source.json)
adds two actual DOS File/A workflows after observed MODEM loss. A passive
direct-EXEC snapshot records state0/status6/carrier-seen1/XOFF-sent0. The real
ASPECT child writes its local marker and returns0, with JFT/file-owner and UART
restoration. Redial then gets clean ATZ/OK, and both complete BBS streams and
manual ANSI queries match. The saved compiler regenerates GO.ASX exactly from
GO.ASP before the independent raw audit accepts the captures.

The first fixture incorrectly sent an acknowledgement space after adopted-render
return, where no prompt owns that key. It reached command mode and prefixed ATZ.
That failed run is preserved under script-offline-modem-dos/offline-program-01;
no product fix was made for it. The second run removes only that fixture key.
The third additionally binds the compiler source and bytecode regeneration;
its two cases are the accepted source-bound evidence.

[Ten confirmation cases](validation/program-offline-confirmation.json) pass
with refreshed child support and normal/mouse parent-frame checks, including
44 exact pressure replies within58.3ms. [Four carrier-loss cases](validation/program-offline-carrier-regression.json)
and [twelve XOFF/CTS cases](validation/program-offline-flow-regression.json)
also pass independent raw verification on parentdd86139f/child183f852d.

[Four recorder/replay sessions](validation/bbs-offline-program-compat.json)
and [two script-window workflows](validation/bbs-offline-program-window.json)
pass on owned stock Synchronet/ENiGMA. [Current normal ENiGMA recorder audio](validation/recording-offline-program-audio.json)
passes26 producer/34 independent/12 serial checks, including77 online bytes
decoded independently from the caller waveform and normal hardware/timer/SIP/VM
cleanup. Its [sealed preparation](validation/recording-offline-program-audio-preparation.json)
retains the current-parent DOS/Telnet helper control and immutable inputs.
This is one normal V22/1200 software route; script-window audio and physical
Boca/SPA2102 remain separate requirements.

## Offline launch failures

[Six independently audited error workflows](validation/script-offline-errors.json)
cover SOFT/BOTH after the same observed MODEM loss:

| Missing or invalid input | Observed result |
| --- | --- |
| ASPECT.EXE absent | Actual DOS EXEC returns carry set/error2; no child exit occurs. The ordinary local acknowledgement is consumed before redial. |
| GO.ASX absent | The actual ASPECT child exits1, reporting the open failure through the adopted renderer. |
| GO.ASX contains one invalid-header byte | The actual ASPECT child exits2, before the source fixture's unreachable file write. |

All six observe the parent offline with no introduced XOFF at direct EXEC,
restore hardware/JFT/file owners and produce clean second ATZ/OK plus exact
BBS/manual-query streams. The observer records actual DOS return FLAGS and AX;
the missing-helper case is not represented as a fictitious child exit65535.
The source compiler is retained, and the valid unused ASX in the missing-helper
case is regenerated independently. No original helper or executable is used.

These checks cover selected file-presence/header faults. Allocation failure,
media faults, helper exit families, other DOS errors and broader application
recovery remain separate requirements. No product source change was needed.

Normal parent: dd86139f44a98279c08ccd003a880aebc3a5341cda079dfea9e9d448a84c69e4.
Mouse parent: 28a80b378a1efbfdcfaf7943be65e434786a61be09ce4e34b3e1fcab05cdb91b.
The ASPECT child remains183f852d, ASIOv6/capabilities12/13 unchanged.

Remaining helper/allocation/media error paths,
initially-low/transient DCD, manual hangup/cancel, sustained flow pressure and
physical UART/modem acceptance remain open. This does not close a full F01–F16
application gate.
