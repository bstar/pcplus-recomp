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

The static far-code bdeb347c checkpoint repeats the result: buffered
`editor-farcode-bdeb-buffer30` passes seven editor checks; immediate
`editor-farcode-bdeb-immediate-retry` enters the message editor but fails
Home/Insert with all eight wire sequences present. The initial immediate label
missed editor navigation and is retained as a prerequisite failure. Paired
recording rejects that attempt; see [current results](modern-compatibility.md).

The private UI-storage checkpoint repeats the paired test on8b38144e:
`editor-ui-8b38-buffer30` passes all seven audited editor checks;
`editor-ui-8b38-immediate` reaches the editor but fails Home/Insert. Both
emit all eight expected key sequences, preserve the synthetic PRM, restore
sampled hardware and close without saving a post. Current hashes and
artifacts are in the paired JSON report; prior experiments remain in its
history. See [the current checkpoint](modern-compatibility.md).

The separate modem-CS7a0ea9d3 checkpoint repeats the result with canonical
checked-in editor input: `editor-modem-7a0e-buffer30-recipe` passes all seven
audited checks; `editor-modem-7a0e-immediate-recipe` fails Home/Insert despite
all eight outgoing keys. Both enter the editor, restore hardware/configuration
and close without posting. The initial `editor-modem-7a0e-immediate` label
failed preflight and is excluded from the paired comparison. The recipe now
comes from `editor-recipes.json`, independently of mutable run reports.
`make test-bbs-modem` checks its aliases, safety and complete ADDKEY length.
See [the current checkpoint](modern-compatibility.md) for provenance and limits.


The setup-startup0fea93ec pair also reproduces the result with explicit
new-scan decline: `editor-setup-0fea-buffer30-noscan` passes seven editor checks,
while `editor-setup-0fea-immediate-noscan` enters the editor but fails Home and
Insert. The original setup immediate run did not reach the editor because of a
login new-items scan and is excluded from the paired comparison. The following
buffered run passed but is retained separately because its counterpart missed
the prerequisite. Current canonical input is377 characters; complete ADDKEY is
400 characters. No Enter follows draft-body input. See the current checkpoint.


The live-settings7f481c92 pair repeats the same ENiGMA result in
`editor-live-7f48-immediate` and `editor-live-7f48-buffer30`. Both enter the
stock editor and send all eight measured key sequences. Immediate forwarding
fails Home/Insert; explicit30ms buffering passes all seven audit checks. Both
close without saving. The binary also includes live settings application,
tested separately; this pair exercises ordinary editor interaction.

The COM-switching0666c496 checkpoint repeats the unchanged-source comparison
under `editor-com-0666-immediate` and `editor-com-0666-buffer30`. Both enter the
stock editor, emit all eight measured keys, preserve the PRM, restore sampled
hardware and close without saving. Immediate forwarding fails Home/Insert;
the explicit30ms buffer passes all seven audited checks. Runtime, recipe,
serial settings and PRM match across the pair; only packet delay differs.
The current paired report retains all earlier experiments. This remains a
local workaround with uncontrolled TCP receive boundaries, not a physical
firmware result or a replacement for the failed immediate aggregate.
