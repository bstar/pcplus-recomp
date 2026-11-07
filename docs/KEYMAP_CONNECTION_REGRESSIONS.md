# Connection regressions for the keyboard-mapper candidate

[The validation receipt](validation/keymap-connection-regressions.json) binds
these exact products, captures and test sources. Application bytes and the
selected deployment remain unchanged by this checkpoint.

The candidate's exact `44891156…` parent and matched modules pass fresh stock
Enigma and Synchronet ZMODEM download/upload tests through the actual SynthModem
Telnet proxy. Each download is11521 bytes; each upload is65539 bytes and includes
all256 byte values plus Telnet/window-control patterns. Checks require CRCs,
offsets, exact file contents/length, ZEOF/ZFIN/OO, subsequent BBS menu response,
unchanged configuration, hardware restoration and no staging residue. Upload
also verifies the actual installed bytes and official server metadata.

The Enigma cancel/retry test observes a4096-byte stage containing the correct
source prefix, sends cancellation, verifies cleanup before retry, then receives
the exact65539-byte file and returns to the actual file list in the same DOS
process. The independent audit checks protocol ordering and closure against
the captured streams. The harness now stages the selected parent's matched
Line/Meta companions rather than copying its executable alone.

The same source products pass25 bounded carrier tests: three idle/call-log-write
cases, four XMODEM cases, ten YMODEM/ZMODEM metadata/partial/retained-file cases,
four interrupted metadata-fragment policy cases, and four ASPECT cases. Transfer
cases run DOS8086. The observed ASPECT cases explicitly use386/UMB for their
diagnostic TSRs. Socket closure supplies virtual modem DCD/results; no application
state or carrier classification is injected. Checks cover actual first/second
connections, clean initialization, subsequent input, call-log records, directory
accounting, resource cleanup, preserved committed files and no RX loss. These
bounded fixtures do not substitute for large-file live-BBS loss acceptance.

The actual stock Enigma large-file loss/redial test now passes separately:
socket loss interrupts a live receive, staging is cleared before the second
login, the same parent automatically authenticates twice through the source
ASPECT/compiler, and retry receives the exact65539-byte file. Directory
accounting records two connections; carrier/RX-complete notices, final file-list
response, normal exit and hardware restoration pass. The independent audit
reconstructs the protocol and timing from raw captures. DOSBox's built-in modem
owns Hayes/UART/DCD and SynthModem owns Telnet; this is not a SIP/audio call.

The default25-row/status-visible isolated LoC main-menu fixture also passes.
Its selected module/layout hashes still match their source files. All1920
reference cells,1906 source-art cells, cursor and focused input/menu-return checks
match. This is a copied-menu stock-core fixture with synthetic accounts, not a
test of the live board's private database or every available screen/layout.
The extra owned fixture was stopped after the test.

## Reload-close quarantine

A new source test TSR is explicitly armed by an owned fake PCKEYMAP child. It
matches the frozen SYN.KBD open, performs the real DOS close, then reports
error6 to exercise uncertain-close handling. The actual parent exits14 with
the source KBD and hardware intact. The TSR verifies restoration of its INT21
and INT2F vectors. No application-memory or file-data mutation is used. Because
the real close succeeded before error injection, this proves the reported-error
quarantine path, not retention of a genuinely unclosed DOS handle or disk-fault
atomicity. The fixture is never packaged or deployed.

Thirty-two CPU-emulation cases also execute the relocated linked Alt-F8
start/queue code. Every tested nonzero recording/parser/macro/transfer/monitor/
controller/snapshot/ANSI-wait/redisplay gate refuses without changing the prior
PROGRAM kind. A busy common-owner result is retained; accepted entry selects
kind13, with DS=SS and the far-return stack preserved. Recording-query and
common-PROGRAM services are modeled, so these are branch/ABI checks rather than
DOS UI transitions into each owner state.

```sh
./tools/dev --command python standalone/test_keymap_close_return_dos.py \
  --terminal build/keymap-connection-verified-20261107/terminal/TERMINAL.EXE \
  --output build/my-keymap-close-test
./tools/dev --command python tools/inspect_kbd.py /path/to/copied/PCPLUS.KBD \
  --profile 6
```

At this checkpoint the inspector read only and reported selected-profile load compatibility and
the stricter full33-profile helper requirement separately, without displaying
bindings or padding/rewriting a file. Known full33, short7, malformed and absent
profile cases were checked. No current private KBD was inspected: the DOS card
is not locally mounted and the selected record's cached configuration source
is unavailable. The newer [prefix-file extension](KEYMAP_PREFIX.md) updates
the inspector for contract2 and retains a separate legacy full-file result.
Physical access, I/O-close reliability and DOS path permissions
remain separate from this content check.

The installed RA608E10 package and selected payload remain unchanged. Physical
Boca/SPA2102/SIP/audio/CTS/DCD acceptance, current private KBD validation,
foreground-refusal DOS UI transitions and the broader original-feature inventory remain
open. Results are bound separately from earlier-parent receipts; passing these
software checks is not a full native-parity or hardware-completion claim.
