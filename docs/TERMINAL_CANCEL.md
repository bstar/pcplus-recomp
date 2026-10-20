# Cancellation inside parent foreground owners

Trap-enabled keyboard and mouse terminals now check pending cancellation inside
quiesced BIOS key waits, serial-only polling, transfer service and the serviced
ASPECT return-key loop. Previously the handler could record INT1B while a
dialog continued waiting for a physical key. Capture and transfer prompts had
their own polling paths that also bypassed the main-loop trap check.

The shared far key reader checks parent context and phase, polls cancellation,
uses BIOS status before reading, and sleeps between interrupts while empty.
It returns Escape on cancellation so each caller restores its own saved screen
and staged state. It never jumps directly out of a callback or interrupt frame
to shutdown. It services no parser/UART traffic onto a quiesced dialog screen.
The common foreground reader checks cancellation before taking a deferred key;
ordinary queued answers retain their previous behavior. Invalid/closed/IF0
admission returns Escape without consuming a BIOS key.

Covered direct waits include directory browser/editor, three serial/profile
confirmation paths, input-mode confirmation, common input-table confirmations,
and ordinary PROGRAM return. Serial-only polling now propagates the request to
capture/snapshot/printer clients. Transfer service propagates it through the
existing fault/context unwind and checked file cleanup. Polling while an
attached child owns the machine still observes the CHILD-phase exclusion.
External DOS children retain their declared trap handoff policy.

The [independent cancellation receipt](validation/terminal-cancel.json) records:

- Three actual DOS negative controls on the earlier client. Browser, capture
  and download waits receive the exact owned INT1B callback but require the
  observer's later BIOS Escape rescue; exit takes36/37 ticks.
- 30 fixed actual8086 DOS routes,15 each on keyboard/mouse clients, passing570
  checks: browser, editor, capture, download/upload prompts, running receive/send,
  partial receive, PROGRAM return, script error-return wait with absent local
  ASPECT.EXE, input-table reload and serial/profile/input
  mode/COM confirmations. All exit through ordinary DOS status16 without a
  rescue key, restore the captured trap vectors/flag and sampled UART/PIC state,
  and remove the observed dialog from the final screen.
- The partial-receive peer sends a real CRC-protected128-byte XMODEM block.
  The observer waits for the actual accepted-block counter before arming the
  break. The wire contains DOS's ACK, and neither RECV.BIN nor PCRX.$$$ remains
  after cancellation. Upload fixtures remain unchanged. Configuration children
  write explicitly prepared synthetic PRMs before parent confirmation; those
  saved file edits are retained, while cancellation does not answer Y.
- The source-owned timer observer validates the linked handler offset, derives
  the PSP from its segment, checks PSP/MCB ownership and READY phase, then waits
  three BIOS ticks after finding the target screen. It reads parent fields,
  records the screen and invokes INT1B. It patches no application field and
  makes no DOS call in the timer. Its later rescue mechanism exposes stalled
  cancellation instead of silently making it pass.
- 20 existing DOS trap cases pass;26 normal ASPECT workflows pass1166 checks,
  including real nested DOS compilation. Two retained-child retry controls
  pass132 checks. Three existing input-table controls pass accepted, declined
  and early queued Y workflows. Linked checks preserve BIOS words0000,011B,
  4B00 and1C0D and reject pending/closed/IF0 waits appropriately.
- A fresh declared-source tree reproduces18 products, including six unchanged
  untrapped controls. The standalone directory editor/browser also rebuild to
  their previous hashes after declaring the shared include dependency.

The first implementation increased the mouse parent's retained floor by seven
paragraphs and made its nested compiler report heap error3. That failed matrix
remains in ignored history. Sharing identical trap return/failure epilogues,
removing an unused EXEC flag and avoiding duplicate serial polling restores
the previous keyboard/mouse retained floors21635/21823 paragraphs. The process
bank is661 bytes; near-code spare is636/488 and DS=SS spare remains672/640.
The corrected full mouse/compiler matrix passes. No conventional-memory limit
or test expectation was relaxed to obtain the pass.

The [stock editor follow-up](validation/terminal-cancel-editors.json) retains
the compatibility boundary: Synchronet immediate passes12 semantic checks;
ENiGMA with30ms explicit modem buffering passes seven. Immediate ENiGMA still
fails Home/Insert while emitting the measured keys. The draft abort/no saved
post checks pass. These are keyboard-client editor regressions, not complete
BBS feature or physical-modem acceptance.

The short exit-latency assertions apply to quiet CTS-ready nullmodem fixtures.
The existing bounded CAN send/drain policy remains in force for stalled CTS or
a peer that continues binary traffic; this receipt does not promise identical
latency in those conditions. Actual DOS device critical errors, additional
nonlocal-error paths, other kernels, physical Ctrl-Break/modem behavior and all
whole-application gates remain open.

Run through the pinned Nix shell:

```sh
./tools/build test-terminal-cancel
./tools/dev --command python standalone/test_terminal_cancel_controls.py \
  --label my-cancel-prompt-control
```

Recorded labels and raw file hashes are in the receipt. Preserve failed runs
and choose fresh labels when repeating the DOS matrices. The baseline and
initial unsupported absolute-PRM confirmation fixtures remain separate from
the successful final evidence.
