# Modern BBS compatibility checkpoint

The source-built DOS terminal is tested against owned loopback instances of
[Synchronet](https://www.synchro.net/) and
[ENiGMA½](https://enigma-bbs.github.io/). DOSBox-X runs the DOS program with
COM2/19200/8N1/HARD through the modeled Hayes/Telnet modem. Nix supplies the
toolchains. These results do not establish physical Wi-Fi modem compatibility.

## Latest editor-tested build

This runtime includes selective live settings adoption. The editor probes below
exercise ordinary BBS editing with that binary; actual Alt-F10 application is
proved separately in [the live settings report](../../docs/validation/setup-live.json).

DOS executable SHA-256:
`7f481c92daa1755f002bb7943f92dd420a823d4ec1eb2884405f09c8b301683d`.

| Server / modem forwarding | Result | Evidence |
| --- | --- | --- |
| Synchronet 3.22a development snapshot / HARD COM2/19200, immediate | All 12 audit checks and eight key-wire checks pass; draft aborted | `editor-live-7f48-hard-clean`, actual DOS rerun; [editor report](../../docs/validation/bbs-editors.json) |
| ENiGMA½ 0.5.1-beta / immediate | Correct outgoing keys; Home and Insert behavior fail | Current paired experiment below |
| Same ENiGMA / explicit 30 ms buffering | All seven audited checks and eight key-wire checks pass; closes unsaved | Current paired experiment below |

The ENiGMA pair uses the same DOS executable, keyboard recipe, synthetic PRM,
serial settings and unchanged stock decoder. Only the modem's explicit
`packet_delay_ms` differs. Server/user state is not reset between runs.
Retained labels are `editor-live-7f48-buffer30` and
`editor-live-7f48-immediate`; full hashes and checks are in
[the paired report](../../docs/validation/bbs-enigma-packetization.json).

The checked ENiGMA source, commit
`6c25317168b762f7d9088a54d3f8295438827a0e`, parses each input event in
[core/client.js](https://github.com/NuSkooler/enigma-bbs/blob/6c25317168b762f7d9088a54d3f8295438827a0e/core/client.js#L321)
without retaining an incomplete escape sequence. The separate
[fragmentation probe](enigma_fragmentation.py) reproduces the difference between
complete and split keys. The current DOS pair supports modem buffering as a
workaround for this local case. TCP can still split a buffered write, so this
is not a general guarantee. A server-side incremental decoder is the robust
fix; no upstream decoder modification is included here.

An earlier screen-print checkpoint’s first Synchronet run was ended by a forced
maintenance event before the editor opened. That prerequisite failure is retained. The current run retains
the lab's corrected event-disable policy, preserving stock editor code and
account quotas; see [the event restriction and retry](editors.md#source-built-screen-print-checkpoint).

The initial controller-checkpoint harness attempts stopped before DOS launch
because the server-only Nix shell lacked NASM. Those prerequisite failures are
retained under `editor-controller-51b9` (Synchronet) and
`editor-controller-51b9-buffer30` (ENiGMA). The selected reruns above use
`./tools/dev`, which provides NASM and DOSBox-X; neither failed setup attempt is
an editor compatibility result.

The first far-code immediate run, `editor-farcode-bdeb-immediate`, missed
message-editor navigation and reached the page/private-mail flow. It emitted all
eight key sequences, restored DOS hardware and saved no post, but it is not
editor-behavior evidence. The unchanged recipe's retry above reached the message
editor and reproduced Home/Insert failure after the concurrent DOS regression
finished. This does not establish why the earlier navigation failed. Both
attempts are retained in the editor report. Paired recording now requires actual
stock-editor entry on both sides before accepting a comparison.

The editor runs above use the setup-before-connect build. Their harness records
and rechecks the executable hash; normal BBS startup is exercised without `/S`.
All three preserve the synthetic PRM and restore independently sampled
IRQ/UART/PIC state. Earlier7a0ea9d3,8b38144e and bdeb347c comparisons remain in
the reports' histories.

The first setup-build immediate run, `editor-setup-0fea-immediate`, did not reach
the editor: login's new-items scan found synthetic messages/files and consumed
the subsequent navigation keys. It restored hardware and saved no post; this is
a prerequisite failure, not a Home/Insert result. The subsequent
`editor-setup-0fea-buffer30` reached and passed the editor, but those two runs do
not form a valid pair. Both remain in editor history. The canonical recipe now
explicitly declines `loginGlobalNewScan` with N, dismisses User Stats and enters
Messages. Both selected `-noscan` attempts reach the stock editor with exactly
the same input, giving the paired result above without resetting user state.

The initial ENiGMA label `editor-modem-7a0e-immediate` failed preflight before
DOS or a BBS connection: repeatedly reusing the report's generated keyboard
output had accumulated startup waits and exit retries beyond the ADDKEY bound.
It is retained as a harness prerequisite failure, not an editor result. The
runner now uses the checked-in `editor-recipes.json` input, derived from the
historical `editor-network-immediate` body with its single automatic startup
prefix removed. New run metadata records `keyboard_input` separately from the
complete generated `keyboard` string; old run sequences are unchanged.
The current pair uses canonical377-character input and a400-character complete
ADDKEY command; the earlier7a0 checkpoint used369/392 before the explicit scan
decline. Earlier and current checkpoints have different preparation schedules;
the current immediate/buffered comparison itself has identical keys/settings.
The dedicated [recipe report](../../docs/validation/bbs-editor-recipes.json)
records the preflight failure and safety/length checks. No Enter is submitted
after draft-body editing begins; both completed ENiGMA runs close unsaved.

## Other verified workflows

Login/menu navigation and XMODEM/YMODEM upload/download have separate retained
DOS tests against these servers. Their executable hashes differ from the
current editor build: consult the [menu matrix](../../docs/validation/bbs-matrix.json),
[XMODEM report](../../docs/validation/bbs-transfers.json) and
[YMODEM report](../../docs/validation/bbs-ymodem.json). They were not all rerun
for this checkpoint. Mystic also has earlier menu coverage.

The current modem regression run passes seven protocol/socket checks and six
buffering checks, including all 256 byte values, Telnet escaping, bounded delay,
and passing queries through to the real DOS responder. See
[buffering method and commands](packetization.md). These model checks remain
separate from actual DOS editor behavior.

## Next hardware comparison

Record the user's modem model/firmware, packet timer/buffer settings, flow
control, and exact failing board screen. Compare immediate versus buffered
serial forwarding before changing key mappings. Then repeat on the physical
386 and modem. Multiline paging, complete editor coverage and arbitrary public
BBS configurations remain unverified.


## Live-settings checkpoint preparation and flow boundary

The first Synchronet run, `editor-live-7f48`, used SOFT COM1/38400. Eleven
audit checks passed, but Ctrl-Q did not reach the server: the raw serial capture
contains one11h byte, the BBS-bound capture contains none, and the modeled modem
records the corresponding XON event. The editor abort therefore failed. This
is a measured software-flow boundary of the local bridge, not physical Wi-Fi
firmware validation. The HARD run also differs in port/baud, so these are not
a controlled comparison with flow as the sole changed parameter. See
[the exact flow observation](../../docs/validation/bbs-synchronet-software-flow.json).

The following HARD attempt, `editor-live-7f48-hard`, successfully aborted but
resumed the prior synthetic autosaved `UNSAVED` line. Its End/Delete/Tab column
assertions expected an empty line and were invalid preparation for that attempt.
Both attempts remain in the public editor report's history. The accepted HARD
run explicitly clears the draft body with Ctrl-Y before the measured ABCDE
sequence; all12 audit checks then pass. The separate canonical
`synchronet-editor-recipe.json` and `synchronet_editor_dos_probe.py` preserve
that preparation and the previously validated HARD COM2/19200 profile. No Enter
follows the measured draft-body input.

The ENiGMA pair still uses the unchanged shared canonical recipe. It again
enters the editor in both runs, preserves all eight outgoing key sequences,
fails Home/Insert with immediate forwarding and passes all seven checks with
explicit30ms buffering. Neither run saves a post. Earlier menu/transfer hashes
remain separate; these probes do not upgrade those older runtime claims.
