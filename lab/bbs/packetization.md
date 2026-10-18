# Serial packet buffering experiment

The stock ENiGMA editor consumes incomplete escape sequences as individual keys
when they arrive in separate input events. The independent
`enigma_fragmentation.py` reference probe reproduces that boundary. A DOS
terminal cannot guarantee TCP receive boundaries at the remote server.

The lab now has an explicit `--packet-delay-ms 0..100` option. Zero remains the
immediate default. Nonzero collects at most256 raw serial bytes until a deadline
measured from the first byte, then forwards them through the existing Telnet
encoder. It does not recognize, replace or synthesize ANSI sequences, terminal
replies, transfer ACKs or other application bytes. Incoming BBS data is unchanged.
A lone Escape has the same bounded delay. This experiment accepts NONE/HARD
only; software flow-control tests retain immediate forwarding.

This models a modem's serial-to-network buffering policy, not any specific
firmware or AT command. One write is still a TCP byte stream: network stacks can
split or combine it. A passing run is evidence for the observed local buffering
experiment, not a general fix for every remote ENiGMA board. The robust server
solution requires incremental decoding of incomplete key sequences, including
a timeout to distinguish a standalone Escape. That upstream change is not
implemented here.

Start the owned stock loopback server, build the DOS terminal, then run the same
retained unsaved editor recipe twice through the pinned Nix toolchain:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma.py start
./tools/dev --command python3 lab/bbs/packetization_editor_probe.py \
  --delay-ms 30 --label editor-screen-print-buffer30
./tools/dev --command python3 lab/bbs/packetization_editor_probe.py \
  --delay-ms 0 --label editor-screen-print-immediate
```

Use new labels for subsequent runs; existing result folders are preserved.
The recipe comes from the public ENiGMA editor baseline. Both tests use
COM2/19200/8N1/HARD and the same synthetic PRM, DOS executable and keyboard recipe.
The runner verifies executable and test-source hashes before and after each
run. It types an unsaved local draft, exercises keys, then closes without an
editor-menu Enter. Server logs must confirm that no post was saved. A successful
runner exit means the experiment was recorded safely; inspect `editor_passed`
and the individual behavior checks for the compatibility result.

Run byte-preservation, timing-bound, Telnet and query-pass-through regressions:

```sh
./tools/bbs-dev --command make test-bbs-modem
```

The tests include all256 byte values, bounded packet size, a continuous trickle
that must not extend the first-byte deadline, and a socket peer that receives
actual serial cursor reports rather than a reply fabricated by the modem.
These fixtures remain separate from actual DOS/server behavior.

The original immediate-bridge editor aggregate remains in
`docs/validation/bbs-editors.json`. Buffering experiments belong in a separate
report and must never turn that aggregate into a pass. Physical Wi-Fi modem
buffer sizes, timeout settings, UART handshake timing, serial overruns, TCP
fragmentation under other network conditions and full editor functionality
remain unverified.

## Observed comparison

The frozen d4cfa4dc DOS executable passes all seven ENiGMA editor checks with
30ms buffering under `editor-screen-print-buffer30`. With immediate forwarding,
`editor-screen-print-immediate` fails Home positioning and Insert mode again. Both
emit all eight expected key sequences, restore the sampled UART/PIC/IRQ state,
preserve the synthetic PRM and close without saving a post. The buffered run includes complete Home and Insert sequences in individual
writes; its exact write count is retained in the paired JSON report.
The executable, test-source hashes, keyboard recipe and serial/PRM settings
match across runs. The stock server/user state was not reset between runs.
This supports modem buffering as a possible workaround for this local case;
it does not establish that every modem or remote TCP path will behave the same.

See `docs/validation/bbs-enigma-packetization.json` for both current runs and
artifact hashes. Prior runtime pairs, including fd68875e and9d90aa1a, remain
in `prior_experiments`; their outcomes are not attributed to the current build. The six packetization fixtures and seven modem protocol/socket checks
are recorded separately. Re-record a new pair with:

```sh
./tools/dev --command python3 lab/bbs/record_packetization.py \
  --buffered editor-screen-print-buffer30 --control editor-screen-print-immediate
```

The dedicated-controller checkpoint repeats this comparison on51b94da6:
`editor-controller-51b9-buffer30-rerun` passes all seven editor checks;
`editor-controller-51b9-immediate` fails Home/Insert again while preserving
all eight outgoing key sequences. Both close unsaved. The paired report retains
the older screen-print checkpoint as history; see [current results](modern-compatibility.md).
