# ASPECT carrier loss and logged redial

The optional 24-row call-log terminal and source-built ASPECT runner now exercise
carrier loss inside WAITFOR, with and without WHEN DISCONNECT, and with and
without the cooperative Alt-Z script window. The application bytes are unchanged.
This extends script/connection/logging composition; full application and physical
acceptance remain open.

## What the scripts and modem actually do

Each case dials an owned loopback TCP peer through DOSBox-X's built-in modem,
then launches a real compiled ASPECT script through the terminal's Alt-1 binding.
The script opens its own marker file, optionally arms `when disconnect call lost`,
pauses, transmits `SCRIPTREADY` and waits for a deliberately absent string.
The peer waits for that actual transmission before sending an incomplete CSI
and aborting TCP. DOSBox-X supplies the modem result and actual virtual DCD loss;
the peer never writes fake CONNECT/NO CARRIER strings or product state.

Without a handler the script writes `START|RETURN|`, confirming false WAITFOR
and ordinary continuation. With a handler it writes `START|LOST|`, confirming the
disconnect callback and script exit. Both scripts close their marker file. The
two window cases send real Alt-Z while the script runs. An observer requires
both the window-active and overlay-visible states; the non-window cases require
no such observation. It also witnesses WAITFOR opcode D4, the actual handler-arm
state, low carrier, stable child DS, last sampled runtime error zero and the
child's verified DOS exit.

The child is initially identified by its exact live UART interrupt vector.
Its DS remains tracked until its own verified INT21/4C; the parent is retained
during EXEC and reads stop before parent exit. Render callback leases are brief
and are not used as the lifetime of the running script or visible window.
The optional observer extension reads state and MSR, makes no product-memory or
UART-output writes, and does not call DOS from its interrupt handlers. Reading
MSR clears delta bits; the application carrier policy uses the level bit.

## Return to the same parent

Real Alt-D then redials in the original DOS process. The second connection must
answer fresh cursor/capability queries, accept keyboard `ready` and answer a
new positioned cursor query. Each case preserves the entire old call-log prefix,
appends exactly two START/END pairs, retains original START timestamps and updates
directory accounting twice. There are four append attempts, no retained records,
no retry acknowledgements and no logger error. PRM, scripts, fixture executables
and configuration remain byte-exact, and the 42-byte hardware snapshot is restored.

These are 8086, COM3/IRQ5, 19200/8N1 HARD cases. AT&K3 belongs to the emulated
fixture, not a prescribed initialization for the Boca modem.

## Reproduction and evidence

The [validation receipt](validation/phone-log-aspect-carrier.json) binds the final
four native cases and their committed-public-source repeat, alongside the 45
previous logging/access/flow/carrier cases. The clean export of 1,983 public
source files rebuilds both
TERMINAL and ASPECT without original executables, previous objects, installation
data or Git metadata. The default observer remains byte-exact with its earlier
carrier version when the ASPECT extension is disabled.

Terminal SHA256: `003bc6b7a0529c737b697c1149d2cfecfef930b5e96406df9dba31d9c137380f`.
ASPECT SHA256: `495d4852275bb7f14c897c8ea9fcaee4620c939690402898fd0c3c6e64723dd7`.

```sh
./tools/dev --command python3 standalone/test_phone_log_carrier_terminal.py \
  --terminal build/terminal-phone-log-bank-d882144fee4f \
  --aspect --runner build/aspect-register-parent-custom-irq/ASPECT.EXE \
  --label aspect-carrier-check-01
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/terminal-phone-log-bank-d882144fee4f \
  --runner build/aspect-register-parent-custom-irq/ASPECT.EXE \
  --output build/phone-log-aspect-carrier-public-repeat-01 \
  --commit 9b0a537 --extended --permissions --slow --watermark --carrier --aspect-carrier
```

Use fresh lowercase labels/output directories. Earlier observer probes are
excluded from accepted evidence. This checkpoint does not repeat stock-BBS
rendering sessions; their evidence still applies to the exact unchanged terminal.
Transfer loss, generic-child/fault exits, every script/window/flow combination,
broad rendering, F01–F16 integration and physical Boca/SPA2102/card acceptance
remain open. Published package/card, live BBS, installed bridge, ATA and host
network are unchanged.
