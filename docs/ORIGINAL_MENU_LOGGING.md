# Original command menu with call logging

The coherent 24-row logging build can now include the original 39-command
reference layout and original local shortcuts. It previously exceeded resident
CS by 50 bytes. Moving the existing deadline selector through the typed modem
bank interface resolves that limit without removing commands or logging.
The new combined candidate is
`99f0a1ac69b851082bf601d3daaa568b8588cc8dfec6f6aceaaabfc4dc775744`.

## Code placement and ABI

The 140-byte transfer-deadline selector moves from resident _TEXT into MODEM_CODE.
Its near public entry retains the existing register/no-argument interface through
NEAR_ENTRY/FAR_ENTRY. DS=SS is unchanged; the selector still reads the same near
settings and writes the same budget word. The instruction body is byte-exact
with the accepted resident implementation. No protocol deadline policy changes.

The bank comparison executes the old resident function, the banked public entry
and direct implementation, and both entries in the original-menu variant:
324 connection/protocol/baud configurations, 1,620 executions. Every result,
register, FLAGS, caller-stack return and DS=SS check matches. The selector makes
no UART/modem calls. Two deliberately damaged new bridges are rejected by the
map/relocation verifier, which now validates all 24 modem bridge pairs.

The banked logging variant has 65,400 resident bytes/136 spare. The combined
original-menu variant has 65,452/84 spare and 64,768 near data/stack bytes/768
spare. The original reference uses its separate code segment; CONFIG_CODE is
52,545 bytes and MODEM_CODE is 3,124. These are code-size/layout facts, not a full
application or DOS-child-memory acceptance claim.

## Menu and key behavior

All 39 original labels, columns and assigned shortcuts remain present. Plain
`L` on the reference menu opens the existing call-log status/retry pane; its
footer advertises this extension. Escape returns to the reference. Alt-L still
executes the actual printer-toggle routine. A linked code-entry witness checks
that dispatch rather than the request word, which the controller consumes.

Original Alt-R records scripts and Alt-S/Alt-P open setup. Assigned BBS page-key
bindings remain intact; transfers are reachable through the original menu.
The call-log and transfer fixtures now use those actual user paths. Redial
uses the visible command browser's Connection/Redial entry, preserving Alt-D
for its original directory role. The reference's existing unavailable commands
remain dim and guarded; displaying all labels does not implement every command.

The interpreter is rebuilt against current source declarations and remains
byte-identical to accepted ASPECT `495d4852275bb7f14c897c8ea9fcaee4620c939690402898fd0c3c6e64723dd7`.
The Synchronet fixture now accepts an explicit matching interpreter path.

## Validation and reproduction

The [receipt](validation/original-menu-logging.json) binds the budget/ABI
comparison, actual DOS reference/help/browser capture, log-pane and mid-header
reconnect probes, the committed-source replay and fresh BBS editor sessions.
The public replay includes 67 logging/connection workflows plus the actual
original-menu DOS workflow, with separate linked menu/original-key reports.
The export rebuilds TERMINAL/ASPECT without original executables, previous
objects, installation data or Git metadata.

```sh
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/transfer-budget-banked-source-01/build/terminal-phone-log-bank-c0238634b651 \
  --runner build/transfer-budget-banked-source-01/build/aspect-register-parent-custom-irq/ASPECT.EXE \
  --output build/combined-original-menu-public-repeat-01 \
  --commit 1561c0e --extended --permissions --slow --watermark --carrier \
  --aspect-carrier --transfer-carrier --batch-carrier --fragment-carrier
```

Use fresh labels/output directories. The initial banked-menu build preceded the
L extension and is excluded from final product evidence. An initial linked
Alt-L check incorrectly inspected the already-consumed action word; the final
check observes the real printer routine executing without replacing it.

Matched helper-package staging/acceptance, unavailable original commands, full
F01–F16/UI integration, wider rendering and physical Boca/SPA2102/card validation
remain open. The published package/card, live BBS, ATA and host network are unchanged.
The live bridge was aligned from25 to24 rows while idle; see
[connection readiness](CONNECTION_TEST_READY.md) for the applied change and limits.

Automatic in-app ASP compilation exceeds conventional RAM in the combined
package. The separate DOS-precompile/ASX workflow is validated; the nested-memory
failure remains explicit in the connection-readiness evidence.
