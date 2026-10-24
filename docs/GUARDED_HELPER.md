# Helper terminal with trap and exit ownership

The full helper-enabled terminal can now include the existing DOS trap and
final-exit owners. The explicit build combines directory scripts, register
handback, settings/resource adoption, sound and mouse controls with the
INT 1Bh/23h/24h handlers, foreground cancellation and retained-callback guard.
This remains an optional application checkpoint; native parity and complete
application acceptance are open.

The ordinary helper terminal retains SHA-256
`a024383fa0171baa88ca317c27b01461f14abd2c9c33cec364975c27a5483679`.
The new product has the suffix `-guarded-traps`. Probe products add `-probe-0`
through `-probe-4`; their controlled stimuli are absent from the normal product.
The interpreter and compiler retain their preceding bytes.

The first combined link exceeded the 64 KiB near-data limit by 16 bytes.
Its 1,493-byte read-only command help now occupies a separate retained far
segment. The help path selects the relocated segment for DOS09, then restores
DS before shared shutdown. The memory auditor checks that exact linked
instruction sequence, MZ relocation, string extent and final terminator.
Actual DOS output must equal the unchanged control's help bytes, both for
`/?` with exit 0 and invalid options with exit 1.

The normal combined product uses 64,064 near bytes, leaving 1,472 bytes free.
Its stack remains 8,192 bytes, resident code is 65,180 bytes, and the retained
parent floor is 24,686 paragraphs. Working buffers and language limits are
unchanged. This composition does not replace trap or EXEC policy: every
maintained child uses the existing suspend/reacquire boundary, and final exit
still validates callback ownership before releasing the process.

## Verification

The [independent receipt](validation/guarded-helper.json) binds current sources,
products and raw witnesses to these distinct scopes:

- Ten actual 8086 DOS trap cases cover both caller break settings, ordinary
  exit, synthetic INT 1Bh, kernel Ctrl-C through DOS08, synthetic critical Fail
  and unknown-vector retention. An independent DOS parent observes startup
  child handoff, kernel termination, vector/break restoration and retained ISR
  survival after largest-free-block overwrite.
- Fourteen timer-driven cancellation cases cover directory/editor screens,
  capture, transfer prompts and active transfers, PROGRAM return, translation
  reload and live setup questions. Witnesses require exit 16, restored traps,
  no rescue key and the existing quiet-fixture latency bound. The accepted
  partial receive must leave neither an installed target nor a staging file.
- Forty-two helper workflows cover thirteen offline modes on COM1/COM2 and
  eight online modes per port. Three actual helper invocations check accepted
  settings/register/resource state, rejected returns, nonzero child exit,
  UART handoff/restoration and continued RX/parser/TX. Four additional online
  cases read map-bound trap/exit fields inside each helper: CHILD phase,
  borrowed caller state, the child lease and trusted parent/floor remain
  consistent through acceptance and rejection. These witnesses do not inject
  an interrupt during the helper itself.
- Eight bare 8086 serial cases cover explicit ASP, missing-ASX fallback,
  chained source retaining numeric/BREAK state and rejected-source recovery on
  both ports. Generated ASX, PRM/UART preservation and a post-child query/reply
  are checked under the combined parent.
- Directory source compilation, three helpers and unsaved stock editor return
  run against the owned Synchronet and ENiGMA services. These use a 386 profile
  and an observer whose actual upper-memory placement is checked. Synchronet
  uses immediate forwarding; ENiGMA uses explicit 30 ms buffering.
- Nine products reproduce in an empty tree containing 701 declared maintained
  sources: the combined terminal and five probes, unchanged helper control,
  register interpreter and compiler. Original executables, installed dialing
  files, images, REA databases and prior objects are absent from build inputs.

The [negative evidence checks](validation/guarded-helper-counterexamples.json)
reject eight damaged raw inputs without changing captured files on disk. They
cover trap/child state, cancellation rescue, returned frames, register ownership,
the helper child lease, compiled bytecode and the BBS observer. The initial
observer-address mutation exposed missing comparison with the probe's frozen
artifact hashes. The corrected recorder requires both those hashes and exact
agreement between the raw observer address and the reported address.

The earlier over-limit build and superseded runs remain in ignored build
history. A changed source hash invalidates an earlier run; it is not converted
into a pass. The final receipt requires current source closure throughout.

The ENiGMA immediate-forwarding issue remains open. These tests do not prove
physical Ctrl-Break, actual device-critical failures under this combined
product, every interrupt timing, arbitrary resident-driver memory budgets,
native feature parity or the complete application gates. The existing FreeDOS
critical-error evidence belongs to its separately recorded products. The card
has not been remounted or updated during this checkpoint.

## Build and repeat

Use the pinned Nix toolchain:

```sh
./tools/build guarded-helper
./tools/build test-guarded-helper
./tools/dev --command python3 standalone/prove_guarded_helper_source.py \
  --output build/guarded-helper/source-next
```

The DOS terminal is
`build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply-guarded-traps/TERMINAL.EXE`.
It uses the existing PRM/KEY resources and sibling interpreter/compiler; no new
DOS command-line switch enables trap protection.

For owned BBS comparisons use `lab/bbs/directory_script_dos_probe.py` for
Synchronet and `lab/bbs/enigma_directory_script_probe.py` for ENiGMA. Select
this terminal, `build/aspect-register-parent/ASPECT.EXE`, fresh labels and
`--source --hook-session accept --cpu 386 --observer-high --mouse-scales 8 4`.
ENiGMA's passing comparison also selects `--packet-delay-ms 30`.
