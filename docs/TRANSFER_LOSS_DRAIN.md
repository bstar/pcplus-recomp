# Buffered binary after carrier loss

The [validation receipt](validation/transfer-loss-drain.json) binds the passing
combined workflow, independent replay, component tests and retained failures.

The transfer owner now drains queued binary after an observed carrier loss
before returning input to the terminal parser. The preceding parent could
retire the receiver immediately, then interpret buffered file bytes as terminal
commands and stop with an unsupported-function error. This is a maintained
safety correction, not a claim that the original executable had this behavior.

The combined candidate is `build/carrier-c0-fit-20261104/ordinary/TERMINAL.EXE`,
SHA256 `e2e1f7ec210da06c36be2f8129a622c70788179daf5ab10c4dac22981cc98059`.
An isolated rebuild reproduces it from 570 declared public inputs, without
original binaries or ancestor Git objects. Resident CS occupies 65,534 bytes
(2 bytes spare); near data/stack remains 65,120 bytes. Further resident code
growth requires banking or another explicit size reduction.

## Ownership and flow

Carrier-loss fault 4 retains its diagnostic and removes the partial stage.
It now calls the existing cancellation drain while binary input remains
exclusively owned. Nine quiet BIOS ticks release the owner; 180 total ticks
bound a stream that never becomes quiet. At that bound the program exits with
the existing ownership-failure code 14 rather than passing active binary to
ANSI parsing. These bounds are existing policies, not measured analog delays.

The physical carrier predicate also guards flow polling inside that drain.
After a previously observed DCD falls, neither cancellation CAN/backspace nor
pending XON/XOFF may enter the modem's command channel. Previously high or
untracked carrier retains the existing writer policy. In particular, the
native flow-byte poll uses THRE, independently of the ordinary data writer's
CTS gate; the correction does not silently change that recovered behavior.
The four-tick controller debounce and recovered UART implementation are unchanged.

Twenty-eight linked inputs compare the old and new owners, exercise buffered
tails with both hardware-flow settings, check physical carrier/CTS/pending-flow
combinations, and prove bounded termination under continuous input including
BIOS midnight rollover. Another 58 existing DCD/flow cases and 12 cancellation
close-race cases pass on the same candidate. Only hardware, BIOS and DOS service
boundaries are modeled; actual linked owner, UART, ISR and storage code executes.

## End-to-end fixture

The carrier workflow uses one DOS 8086 parent at COM3/3E8h/IRQ5, 19200/HARD,
25 physical rows and an 80x24 logical area. DOSBox's built-in modem owns Hayes
responses and DCD. A raw socket relay forwards bytes without terminal/Telnet
interpretation to the staged SynthModem proxy, which alone owns Telnet. The
destination is the owned stock Enigma installation and its real SE/X/Y/Z helper.
The relay paces downstream blocks at a synthetic 19200-bit/s wire-like budget;
this is not a measurement of the Boca, analog link or actual throughput.

Native DOS ASPCOMP compiles the login source, byte-for-byte equal to the host
compiler. The source-built ASPECT child performs both automatic logins. After
the first source-prefix disk write, the relay aborts both socket transports.
This lowers the built-in modem's actual emulated DCD; no fixture edits application
carrier state or supplies a synthetic result string. The witness reads only
memory and captures the final state before DOS frees it.

The recorder requires carrier-loss notice, deletion of the partial stage before
the second login, same-process redial and a full exact 65,539-byte retry. The
payload includes all 256 byte values and 215 size-reply lookalikes. Independent
checks require CRC-valid metadata/data, ZEOF, ZFIN/OO and controls, post-transfer
target search, two authenticated sessions, directory accounting and restored
hardware. The interrupted stream may be a prefix at each buffering boundary;
the completed second stream must match exactly at relay/proxy boundaries.

The accepted capture removes a 4,096-byte stage before the second login, then
receives all 65,539 bytes exactly. Both DOS-compiled automatic logins succeed;
all 473 compiled script bytes match the host compiler. Ten copied-capture
controls accept the unchanged evidence and reject nine mutations. Coherent
retry corruption changes the same byte across raw TCP, proxy and relay captures,
preserving their equality; the packet auditor rejects its data CRC.

A separate fresh local-cancel/list/retry/search workflow passes on this same
application, including its independent audit and nine copied-capture controls.
Fresh Synchronet login/editor/abort/NAWS and reference checks match all 1,920
logical cells and cursor with no saved message or transfer changes. These are
current-image regressions, distinct from the frozen earlier receipts.

Final teardown uses the BBS's actual logoff sequence and the proxy's QUIT
request. The lab adapter optionally honors its real `disconnect` event with
socket FIN, allowing pending output to drain. It fabricates no modem response;
the built-in modem observes socket closure itself. The optional behavior is
disabled for existing adapter users. A raw-socket check separately covers all
byte values, scoped abort, ordinary local close and a buffered remote EOF.

## Retained failures and acceptance limits

The old parent actually stopped after the first loss. A passive final-state
witness records fault 4, no UART RX drops and no surviving transfer owner;
that establishes a binary-tail ownership gap rather than an application-ring
overflow. The new parent survives and redials. An early retry fixture navigated
away before completion; its failed result remains excluded. A later run completed
the exact retry but its final Hayes hangup reached the BBS while output remained
queued, so strict teardown checks rejected it. A clean-logoff attempt then
exposed the bridge-local QUIT audit distinction. A subsequent run encountered
stock Enigma's random logoff bytes and stopped at an unrecovered C0 service.
The combined candidate adds [the verified default C0 branches](C0_CONTROLS.md).
Those earlier captures remain failed; a briefly started invalid-newline-assertion
fixture was deliberately stopped and is excluded from acceptance.

The fixture's `AT&K3S12=25` initialization applies to DOSBox only. It is not a
Boca command recommendation or a measurement of that card's escape guard.
Loopback network syntax in the emulated ATD command is likewise a lab feature;
the physical modem dials a telephone route and selects `loc` after carrier.

These checks do not establish physical Boca/SPA2102/SIP/DSP behavior, resolve
the user's physical BUSY report, or establish every display layout/protocol and
full original feature parity. Local cancellation and Synchronet regression
coverage must remain separate from this carrier-loss workflow. No candidate
deployment or private configuration change is implied by a passing lab run.

```sh
./tools/dev --command python lab/bbs/test_proxy_carrier_dos.py \
  --runtime build/STAGED_PROXY/candidate --terminal build/SELECTED/TERMINAL.EXE \
  --runner build/SELECTED/ASPECT.EXE --compiler build/SELECTED/ASPCOMP.EXE \
  --file PABCDEF.BIN --label NEW_LABEL --witness --transfer-wait-ms 150000
./tools/dev --command python lab/bbs/audit_proxy_carrier.py \
  --capture build/bbs-lab/results/enigma/NEW_LABEL \
  --bridge build/bbs-lab/NEW_LABEL-proxy --output build/NEW_LABEL-audit
./tools/dev --command python lab/bbs/check_proxy_carrier_controls.py \
  --capture build/bbs-lab/results/enigma/NEW_LABEL \
  --bridge build/bbs-lab/NEW_LABEL-proxy --output build/NEW_LABEL-controls
```

Choose an existing owned uppercase DOS83 fixture from the transfer matrix.
These commands do not create, replace or remove a catalog payload.
