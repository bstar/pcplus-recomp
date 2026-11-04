# Auto Answer at accepted display heights and typed carrier readiness

The composed row-geometry build now admits Auto Answer on visible reserved status
rows at25/28/43/50 physical rows. Alt-Y, the original reference menu and command
browser keep the configured answer-on selection, bounded typed sender, native
post-write echo and generation-owned information tone. The existing dynamic
connection-notice lease already owns save/restore and stale-row retirement.
No modem commands, user settings, original shortcuts or splash were replaced.

## Admission and display ownership

The optional larger-height path checks DS=SS, IF1/DF0, the existing pure canonical
row/status layout, visible status,80 logical/physical columns, narrow video and
attribute strides and no viewport. Valid custom scroll bounds remain within the
logical body; terminal addressing cannot reach the reserved status row. BIOS must
agree on height, color text mode2/3 and page0. Legacy BDA height0 means25 rows.
The public admission entry preserves all non-result registers and the caller's
IF/DF, including refusals with a different SS. Refusal precedes typed-command,
notice or speaker effects. Builds without row geometry retain the fixed gate.

The notice remains the recovered leading blank plus `AUTO ANSWER...` within its
fifteen-cell lease. Incoming body text, queries and the native status refresh
continue while the typed command owns output. Completion releases the notice
before deferred keys dispatch. Cancellation, hangup, exit and qualified carrier
loss retain the existing command cleanup, sound-generation rules and retry-line
resynchronization. The shared fixed gate itself is unchanged.

## Typed commands during DCD grace

Inspection found a separate foreground bug: normal flow/output respected the
shared immediate carrier-readiness result in BP, but manual Init and Auto Answer
were always given a physical-write grant of1. They could send more command bytes
after tracked DCD fell, before the existing four-tick disconnect qualification.

A linked differential reproduces the old behavior against the preceding accepted
image. With `A` already sent, the old image sends `T` during known-low DCD; the
short manual Init can even complete `ATZ` and CR in that interval. The corrected
foreground passes its actual readiness grant to the existing typed owner.
Desired command bytes and local echo remain withheld during a transient drop,
then continue exactly when carrier returns. Qualified loss cancels the command
through existing cleanup. Offline Init/Auto Answer still work without DCD: an
untracked, disconnected modem must accept local commands.

The controller's debounce, deadlines, UART instructions, typed engine and
protocol framing are unchanged. The fix does not promise to eliminate a physical
carrier transition after the final hardware read and before an output instruction.

## Evidence

The [receipt](validation/large-auto-answer.json) binds exact parents, current
public sources, independent rebuilds and immutable case captures.

-117 linked larger-height inputs execute actual dispatcher/notice/command/tone
 code across profiles4/6 and all four heights. They cover direct/reference/browser
 routes, complete body/planes/history preservation, quiet/sound behavior, custom
 scroll bounds, lower-row RX/CPR/typeahead, cancel/hangup/exit/loss/redial, and
 canonical/BIOS/stack/register/IF/DF/SS refusals before side effects.
-40 baseline/candidate linked inputs cover both manual Init and Auto Answer,
 low-DCD durations within the qualification interval, captured duplex/echo,
 returning-carrier completion, sustained loss and coherent offline command use.
 Baseline command completion before qualified loss is recorded as the observed
 defect, rather than incorrectly requiring that completed baseline owner to
 remain active or report cancellation.
-Existing regressions pass:34 Auto Answer inputs,31 manual dispatcher inputs,
 117 manual-owner inputs,262 typed-answer inputs and58 shared carrier-readiness
 inputs. Source memory inspection still verifies the six near-cdecl speaker
 calls and existing cross-bank manual owner bindings.
-Ten actual DOS8086 workflows exercise quiet direct entry and original-reference
 entry with live duplex/sound, in the ordinary parent and four height diagnostics.
 An owned answer-on field contains two legitimate pause markers, giving the
 passive timer time to capture two complete notice frames. The markers neither
 transmit nor echo. Exact answer bytes, incoming text/CPR, typeahead ordering,
 unchanged PRM, notice cleanup and42-byte hardware restoration are required.
-Eight actual DOS8086 virtual-modem workflows cover HARD/SOFT at each height.
 A legitimate leading configured pause permits notice capture before transmission.
 The peer receives a partial `ATS` command, sends a partial CSI and closes TCP.
 DOSBox-X supplies real virtual DCD and NO CARRIER. The same parent must retire
 the command/UI, take the original Connection-menu redial path, initialize cleanly
 and return keyboard/parser replies. Exact modem command lists reject retired
 command suffixes, stray flow bytes and ERROR; each new initialization requires
 its own OK. Both recorded calls, previous call history, directory accounting
 and UART/PIC/vector restoration remain checked by the passive log observer.
-The independent artifact verifier passes all18 workflows and36 complete notice
 frames, with16 virtual modem connections in the carrier subset. It rebuilds
 the passive observer, checks its exact used bytes, full-height placement and
 lower-body data, serial ordering, clean command phases, raw call records and
 hardware restoration. Exact tone timing, transient DCD and post-retirement
 screen-plane ownership remain linked-model evidence.
-Five isolated569-source rebuilds reproduce exactly without original binaries
 or ancestor Git. Startup-row diagnostics remain rejected by application staging.

The ordinary candidate is SHA256
`d4709b762fdd4c47f64da1b245bc126b9d86fc46f01849f1cb245b6741086733`.
Near data/stack remains65,120 bytes and resident CS65,500 bytes (36 spare).
CONFIG grows59,457→59,537 bytes. Height diagnostics use65,524 resident bytes
(12 spare). There is no additional static data or resident-code growth.
Further resident additions still need banking.

The initial passive probe looked at the first reserved-row cell, missing the
recovered notice's leading blank. Correcting the observer to start at column1
fixed that fixture without changing the UI. The later carrier-grant fix is a
separate application correction supported by differential and actual modem
evidence. Exploratory artifacts are not used as acceptance results.

## Reproduction and remaining work

Build fresh parents with the pinned `./tools/dev --command` environment and the
receipt's exact flags. Run `standalone/check_large_answer_live.py`, the existing
Auto Answer/manual owner regressions and `standalone/check_manual_carrier_grant.py`
against the documented preceding baseline and new ordinary parent. Use
`standalone/prove_terminal_variant.py` for isolated source reproduction.

```sh
./tools/dev --command python standalone/test_auto_answer_dos.py \
  --terminal build/NEW/28/TERMINAL.EXE --rows 28 --label new-answer-28
./tools/dev --command python standalone/test_large_answer_carrier_dos.py \
  --build build/NEW --rows 28 --output build/NEW-carrier/28
```

Use fresh output directories and repeat at the other heights; test the ordinary
parent separately. The independent checker accepts the five direct reports and
four carrier reports. Exact accepted paths and hashes are in the receipt.

Owned virtual-modem commands are test fixtures, not new recommendations for the
Boca hardware. No physical DOS files/card, private configuration/call history,
selected connection-test payload, installed bridge/BBS/service or networking
changed. These checks do not establish Boca/SPA2102/SynthModem audio or
Enigma/Synchronet acceptance. Normal line controls/startup preferences, other
original feature parity and hardware/BBS validation remain open. Full goal active.
