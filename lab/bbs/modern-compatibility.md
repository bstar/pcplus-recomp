# Modern BBS compatibility checkpoint

The source-built DOS terminal is tested against owned loopback instances of
[Synchronet](https://www.synchro.net/) and
[ENiGMA½](https://enigma-bbs.github.io/). DOSBox-X runs the DOS program with
COM2/19200/8N1/HARD through the modeled Hayes/Telnet modem. Nix supplies the
toolchains. These results do not establish physical Wi-Fi modem compatibility.

## Latest editor-tested build

This runtime includes serviced 63 KB redisplay and frozen-history export, confirmed live input-mode changes, bounded default-XLT
PCPLUS directory lookup, saved translation modes, explicit XLT input translation,
confirmed idle COM switching and supported profile changes. The BBS probes use
saved mode0 (identity) without /X.
The editor probes below exercise ordinary BBS editing with that binary; actual
Alt-F10 application is
proved separately in [the live settings report](../../docs/validation/setup-live.json).
Ctrl-PgUp browsing is exercised separately in [the redisplay report](../../docs/validation/redisplay-live.json).
W export is exercised separately in [the history report](../../docs/validation/history-export.json); the editor probes use ordinary editing without opening redisplay.

DOS executable SHA-256:
`4ad7d3a2e4ad760149c95fe09c4ee96f29855d8aa9173e1819eb4db1e78d3d05`.

| Server / modem forwarding | Result | Evidence |
| --- | --- | --- |
| Synchronet 3.22a development snapshot / HARD COM2/19200, immediate | All 12 audit checks and eight key-wire checks pass; draft aborted | `editor-history-4ad7-hard`, actual DOS rerun; [editor report](../../docs/validation/bbs-editors.json) |
| ENiGMA½ 0.5.1-beta / immediate | Correct outgoing keys; Home and Insert/overtype fail | Current paired experiment below |
| Same ENiGMA / explicit 30 ms buffering | All seven audited checks and eight key-wire checks pass; closes unsaved | Current paired experiment below |

The ENiGMA pair uses the same DOS executable, keyboard recipe, synthetic PRM,
serial settings and unchanged stock decoder. Only the modem's explicit
`packet_delay_ms` differs. Server/user state is not reset between runs.
Retained labels are `editor-history-4ad7-buffer30` and
`editor-history-4ad7-immediate`; full hashes and checks are in
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

An additional [control-alias keymap experiment](keymap-aliases.md) was rejected:
although the multi-line view offers Ctrl-A for Home, the stock compose form
intercepts it to change the subject. The actual DOS candidate emits the expected
controls but fails editing checks. Its paired report remains separate from the
default and packet-buffering results; it is not a supported BBS profile.

The first redisplay Synchronet attempt, `editor-redisplay-27df-hard`, received
connection refused because the owned listener was unavailable. Its failed
prerequisite evidence is retained separately. Restarting the existing listener
and retrying passed that earlier redisplay build; both attempts remain in the
report history. This does not establish why the previous listener stopped.

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

The editor runs above use the saved-mode build with identity translation. Their harness records
and rechecks the executable hash; ordinary BBS startup is exercised without `/S`
or opening Alt-F10. The separate settings suites prove the new settings behavior.
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


## Retained matched Synchronet flow comparison

`editor-com-0666-soft-pair` and `editor-com-0666-hard-pair` use the same
COM2/19200/8N1, source-built runtime, complete keyboard recipe, harness sources
and synthetic PRM except its SOFT/HARD words. The SOFT run passes11/12 editor
checks but consumes the single emitted Ctrl-Q as XON in the modem model, leaving
zero Ctrl-Q bytes at the BBS and no abort. HARD delivers that byte and passes
all12 checks, including actual editor abort. The independent byte captures and
XON event isolate this modeled flow-selection conflict; physical modem firmware
and changing CTS timing remain untested. The server/user state was not reset,
and both recipes explicitly clear the synthetic body line. See the
[flow guide](flow-control.md) and
[matched evidence](../../docs/validation/bbs-synchronet-software-flow.json).

The initial current HARD run, `editor-com-0666-hard-clean`, also passed all12
checks. It is retained with the failed SOFT run in editor history; the matched
HARD control remains in the matched flow report; the latest editor aggregate
uses the separately identified redisplay build above. Earlier editor and buffering
checkpoints remain in their reports. No older menu/transfer results are relabeled.

## Earlier live-settings preparation and flow boundary

The first Synchronet run, `editor-live-7f48`, used SOFT COM1/38400. Eleven
audit checks passed, but Ctrl-Q did not reach the server: the raw serial capture
contains one11h byte, the BBS-bound capture contains none, and the modeled modem
records the corresponding XON event. The editor abort therefore failed. This
is a measured software-flow boundary of the local bridge, not physical Wi-Fi
firmware validation. The HARD run also differs in port/baud, so these are not
a controlled comparison with flow as the sole changed parameter. See
[the earlier flow observation in report history](../../docs/validation/bbs-synchronet-software-flow.json).

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
