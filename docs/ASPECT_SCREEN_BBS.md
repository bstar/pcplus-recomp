# Capability27 owned BBS checkpoint

The frozen screen-command application passes the owned Enigma carrier-loss and
retry regression and the stock Synchronet editor regression. The
[validation record](validation/aspect-screen-bbs.json) records the exact
application hashes, independent audits and clean server shutdowns, with
`passed=true` and `checkpoint_verified=true`.

The application is parent `screen-parent-v6-20261119`, interpreter
`screen-child-overlay-v4-20261119`, and compiler `screen-compiler-v2-20261118`.
Their exact hashes match the ten-file runtime payload
`build/screen-lab-v1-20261119`. The separate
[screen-command evidence](ASPECT_SCREEN_COMMANDS.md) establishes native
semantics and the five full DOS8086 workflows; this BBS regression preserves
the existing connection and transfer contract.

Enigma passes all18 checks with two runtime-compiled source logins, virtual
carrier loss after4096 source-exact bytes, clean staging before redial, an exact
65539-byte retry, the required receiver ZFIN/sender OO ordering, subsequent file
search and normal DOS exit. Its independent raw-wire audit passes. Sixteen
capture controls accept the unchanged evidence and reject15 altered copies.
The established DOS386/UMB profile and150000ms transfer wait are unchanged.

The accepted capture is
`build/bbs-lab/results/enigma/screen-builtins-carrier-v3-20261119`.
Its detached producer has persisted output and an atomic exit receipt at
`build/screen-bbs-v1-20261119/enigma-v3-job/exit.json`, with return code0.
The earlier v2 producer disappeared before persisting its in-memory relay
traces; its second transfer remained incomplete. That negative is retained and
unqualified. No traces were reconstructed and no finish check was waived.

After the requested pause, the frozen manifests, prior Enigma receipts and
checker sources were revalidated. Enigma did not need another run. The archived
partial checkpoint remains at
`build/screen-bbs-resume-v1-20261119/previous-partial-checkpoint.json`.

The fresh Synchronet DOS8086 session passes all22 editor checks: actual ASPECT
login, Insert/overtype, Home/End/Delete/Tab, page boundaries, Ctrl-Y and unsaved
draft abort. Server inputs and message bodies remain unchanged, with no message,
mail or transfer writes. Independent audits match all1920 logical cells with
zero differences, verify the real CPR5,8 boundary and confirm NAWS80x24 for a
physical80x25 display with status shown. The capture is
`build/bbs-lab/results/synchronet/screen-builtins-screen-v1-20261119`.

Synchronet used a durable test job and an owned PTY server supervisor. Both
atomic exit receipts under `build/screen-bbs-resume-v1-20261119` record return
code0; the stock server received its normal console `q` command. All owned
servers, proxies, producers and supervisors are stopped. Ports23231 and23233
were verified free before startup and after cleanup.

No application, protocol or checker source changed for these runs. Installed
selectors, private configuration, physical DOS hardware, live BBS services and
SIP/audio settings remain unchanged. This is a selected software regression
checkpoint, not a release or whole-PCPlus/ASPECT completion claim.
