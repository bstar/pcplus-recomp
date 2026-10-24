# DOS child execution with a wide logical screen

This campaign exercises a real ASPECT `RUN` after the remote peer requests
132 columns. The parent still uses physical mode3/80x25/page0 and overlapping
panes. It does not select a physical132-column BIOS mode.

All16 final cases pass. The [independent receipt](../../docs/validation/peer-width-process.json)
binds448 artifacts, exact product identities and the full matrix. Accepted
directories are `build/peer-width-process-final-SSSS-02`, where the four binary
digits select source compilation, window, NOCLEAR and graphics respectively.
The earlier `-01` matrix is retained separately and is not accepted.

The full matrix crosses source/precompiled scripts, open/closed cooperative
script windows, SAVE/NOCLEAR and text/graphics children. The source-built COM
child records its actual initial BIOS mode, columns and page, then writes a
colored text cell or changes to graphics mode13h. It exits with code37.
The script retains its numbered output stream, resumes rendering, completes
and returns to the same parent. Manual keyboard input then requests a narrow
display and obtains another actual cursor reply.

A passive observer identifies the root only after the actual wide request.
It records the nested child's37 exit separately from ASPECT's0 exit and
observes a real nested DOS EXEC with SAVE owner2 or NOCLEAR owner1. Exactly
one renderer PROGRAM_BEGIN/END pair must retire. Root and interpreter DS=SS,
idle final owners and the independent42-byte hardware restoration snapshot
are required. No instruction, return value, key or serial reply is supplied
by the observer.

The fixture uses8086, COM1/IRQ4,38400/8N1/HARD with synthetic configuration.
Its result file retains the legacy harness's final-screen greeting check as
false because the test deliberately changes that screen. The enclosing audit
instead requires the actual initial CPR/DA and the complete ordered wide/
child-return/narrow reply sequence, alongside every applicable hardware,
configuration, file and modem check.

The cursor reply sequence is ordered:2;128 before RUN,3;6 after RUN at the
retained logical cursor,3;128 after new remote output, then2;80 after manual
parent input and a narrow request. DOS compilation must publish exactly the
host compiler's ASX. These are continued-renderer/geometry checks; they do
not establish byte-for-byte preservation of every logical screen plane.

The initial pilot exposed a harness lifecycle mistake: the legacy harness
invoked the observer again after it had already unhooked itself at root exit.
Removing that second installation restores the exact hardware snapshot.
The first matrix also showed that short closed-window renderer calls can
finish between timer ticks. The final observer checks ownership at the actual
BIOS cursor calls as well as retaining timer samples. Earlier failed outputs
remain local and are not included in the accepted receipt.

For fresh output directories:

```sh
./tools/dev --command python3 lab/bbs/peer_width_process_dos.py \
  --terminal build/SELECTED-SOURCE-PRODUCT/TERMINAL.EXE \
  --runner build/aspect-register-parent-custom-irq/ASPECT.EXE \
  --compiler build/aspect-compiler-dos/ASPCOMP.EXE \
  --window --noclear --graphics --output build/YOUR-FRESH-PROCESS-CASE
```

Omit each optional flag for the other matrix members. Supply all16 fresh
directories to `record_peer_width_process.py` as repeated `--case` arguments,
with `--output` selecting the public receipt.

This uses an actual DOS child with a synthetic serial modem. It does not
establish arbitrary OS interruption, every DOS kernel/command processor,
wide transfers or real BBS/audio/physical modem acceptance. Application,
interpreter and compiler sources remain unchanged. General F01–F16 and card
deployment requirements remain open.
