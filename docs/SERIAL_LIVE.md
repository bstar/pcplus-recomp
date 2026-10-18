# Serial changes during setup

Alt-F10 can now apply baud, parity/data/stop and software/hardware flow changes
on the current COM port. Save and close PRMEDIT, then answer Y to the serial
question. Any other key keeps the active serial settings; the saved file remains
available for later application/startup. The answer itself returns to the
terminal, preserving the next ordinary key for transmission. A peer must match
the selected rate and format; the application does not renegotiate modem firmware.

COM/base/IRQ changes defer the entire serial/profile group. The separately
tested ownership prerequisite in [PORT_HANDOFF.md](PORT_HANDOFF.md) is not yet
connected to this settings workflow. Supported profile
changes have a separate [confirmation/reset workflow](PROFILE_LIVE.md). This implementation deliberately retains the same port, IRQ vector
and original hardware snapshot; cross-port restoration/migration and other emulations remain separate
application work. Existing CLI categories
retain precedence and modem negotiation/competing owners still block setup.

## Foreground handoff

The candidate owner has an explicit permitted-category policy, separate from
the original API that always defers serial changes. Only bits2/4/8 can be
permitted. A port change disables that permission for every serial category.
The candidate remains staged until the foreground choice is known.

The parent has already drained TX, paused configured flow and released its
UART interrupt for the editor. On Y it restores the old effective divisor and
LCR while IRQ remains masked, IER0 and RTS low. It waits for THRE/TEMT and sends
any necessary XON at that **old** format, bypassing ordinary CTS/peer-XOFF gates
as the existing flow-control owner does. It then waits for physical TEMT again.
A full BIOS-tick36-tick deadline bounds the gate; timeout keeps the old serial
settings, leaves the saved request deferred and presents a visible result.
An observed overrun is accounted rather than silently cleared by the LSR read.
No RBR byte is read/discarded by this handoff.

After successful validation/gating, the parent installs the proposed serial
globals and prepares future modem actions with the new rate. Unexpected prepare
failure restores the old serial/modem plan; failure to reprepare the old plan
terminates through normal hardware cleanup. Successful changes reconcile the
driver's flow flags before its ISR is reinstalled. Disabling SOFT clears stale
peer XOFF. Newly enabling SOFT announces XON when the receive queue is low.
Buffered input above the conservative128-byte resume watermark stays paused
until drained. When both flow flags are set, the recovered receive driver owns
SOFT first; RTS must therefore stay releasable rather than being lowered under
an owner that will never raise it. Hardware flow still gates ordinary TX by CTS.

Normal child return then programs the new divisor/LCR, restores the parent ISR
and applies the new RTS policy while preserving DTR. The original startup
hardware snapshot is never recaptured. Exit restores the exact original UART,
PIC and vector state even after multiple changes. Existing ring bytes, screen,
cursor and transient BBS state remain owned by the session.

Only a successfully committed baud change acknowledges a new PRM source-rate
baseline. This prevents an unrelated save from reverting negotiated autobaud
while still allowing a previously applied rate to be deliberately reverted.
Declines, failed gates and superseded offers do not advance that baseline.

## Evidence and limits

`check_live_setup_policy.py` checks27 independent policy/lifetime inputs, including profile permission.
`check_live_setup_link.py` executes53 actual linked foreground cases, covering
changed supported rates, every changed7/8-bit parity/stop combination, flow
transitions, old-format control bytes before new-rate payload, high receive
queues, dual flow ownership, decline keys, bounded TEMT waits, repeated changes
and an established modem session with pending input. Kernel/BIOS/UART boundaries
are modeled; product validators, native setters, flow code and restore paths run.

The production DOS editor suite independently observes1200/115200 divisor
transitions and8N1/7E2 LCR transitions using an INT1C sampler. Six serial/settings DOS cases
also cover decline, display color and newly enabled SOFT's XON before typed
payload. The peer sends fresh display bytes and receives a fresh cursor reply
after each return. Final42-byte UART/PIC/vector snapshots equal startup.
DOSBox-X's TCP peer does not enforce real baud/parity agreement or physical CTS
timing. Those hardware/firmware properties still need the user's machines.

Run `./tools/build test-terminal`; current evidence is bound in
[validation/setup-live.json](validation/setup-live.json). Stock BBS editor
results retain their explicitly tested older executable hashes in
[the compatibility ledger](../lab/bbs/modern-compatibility.md); these serial
handoff tests do not relabel those runs.
