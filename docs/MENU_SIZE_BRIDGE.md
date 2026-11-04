# Owned terminal-size handoff to Telnet

The staged SynthModem candidate now asks PCPlus for its accepted text area while
owning the local CONNECT menu, before opening a BBS TCP connection. The actual
8086 terminal produces CSI8;24;80t through COM3/3E8/IRQ5; the candidate consumes
that metadata and a real loopback TCP peer receives NAWS80×24. Ordinary CPR/DA
and keyboard data still reach that peer afterward. No terminal reply is supplied
by the test peer on DOS's behalf.

This connects the [optional size-report component](WINDOW_SIZE_REPORT.md) to a
Linux owner, rather than inferring logical rows from saved configuration or
physical VGA rows. It remains an isolated candidate. No installed SynthModem
source/config/service, connection-test package pointer or physical DOS files
changed. The unchanged terminal input is SHA256
`f995e1a14dd8925a51aff8331aeefaac085f19c89b01989f9347d479ef3157b4`.

## Ownership and failure behavior

See the [candidate README](../lab/bbs/patches/synthmodem-menu-size/README.md)
for configuration, GPL attribution, pinned baseline hashes and reproduction.
The option is off by default. Enabled probing makes exactly one bounded query,
retains up to1024 bytes of typing and constructs the existing Telnet codec with
the confirmed dimensions. Peer NAWS refusal sends no unsolicited size payload.
No receive parser scans PROXYING data; all256 byte values and size-looking
sequences remain ordinary payload, with Telnet IAC escaping unchanged.

Invalid dimensions, reserved malformed responses, timeout or input overflow close
the modem session. This avoids silently advertising a guessed size or retrying
while an unanswered old reply can arrive. This is not authenticated metadata;
there is no wire nonce. Connection failure/cancellation clears retained typing
so it cannot reach a different BBS. A later successful menu connection probes
fresh dimensions.

Tests exposed two cancellation defects in the initial candidate. A synchronous
output callback could close the owner, after which setup still opened TCP or
recreated its codec. An already-queued cancelled TCP deadline could return a newer
connection to the menu. State/socket checks after callback output and identity
checks on the deadline now prevent both; dedicated regressions fail on the prior
candidate and pass after correction. Socket identity is detached before destroy,
so synchronous/stale close/error/data events cannot replace the current owner.

## Bound evidence

[Validation receipt](validation/menu-size-bridge.json) binds the public inputs,
pinned external sources, candidate hashes and raw evidence hashes. It records:

- 17 passing Node groups: collector boundaries/splits, default stock equivalence,
  query fragmentation/deadline, CRLF/typing, inline callback reentry, NAWS escaping
  and refusal, failure/overflow/configuration, stale timers/sockets, reconnect,
  both directions of all256 bytes and lookalikes at every two-chunk split, ACL,
  real TCP, cancellation and backpressure/solicited negotiation.
- Actual DOSBox-X8086 application/BIOS keyboard/UART/ISR/parser workflow with
  numeric ATD1, local `loc` selection, one actual size reply, independent NAWS
  decoding, CPR/DA/typed z, visible banner, unchanged synthetic PRM/image and
  matching42-byte interrupt-vector/UART/PIC snapshots after exit.

The deterministic tests supply sockets, timers, configuration and logging at
module boundaries; the product class and collector run unchanged. The real TCP
test retains real networking/timers with synthetic terminal callbacks. The DOS
test uses the actual class and real Linux sockets/timers, with a synthetic Hayes
peer instead of the physical modem/SIP/DSP path. Its accepted dimensions are24
rows, not evidence of a larger-screen startup or live online change.

Raw isolated evidence is under `build/menu-size-accepted-20261104/` and
`build/menu-size-dos-accepted-20261104/`. Failed early candidate/test attempts
remain in their separate directories. All declared source and binary inputs
are verified unchanged across the successful runs.

## Remaining gates

Expose the accepted display selectors through guarded normal controls and startup
preferences, then exercise the handoff with owned Enigma and Synchronet layouts,
editor/focus/modal return and supported larger text areas. Live online changes
need their own session synchronization and are not enabled here. SIP/DSP/analog,
physical modem acceptance, binary-transfer routes and verified deployment remain
separate gates. These results do not establish full PCPlus feature parity; the13
unavailable reference commands and the broader inventory remain open.
