# Transient native Line/Port setup

The optional `--line-port-overlay` build resolves the resident prototype's
ASPECT capacity regression. The maintained native Alt-P popup, checked prefix
save and UART handoff remain available; its code is loaded only while needed.
The installed RBADE091 package and release selector are unchanged.

The subsequent [matched package](LINE_PORT_CONNECTION_CANDIDATE.md) includes the
required module and passes separate package/source/DOS gates. Installation and
physical acceptance remain separate from that software package milestone.

The reviewed parent is
`ff6bb369a8b3693cefc357fec901ae576139cafe8915f8e60818ddcdde2e5399`.
It requires its exact `PCLINE.OVL` beside `TERMINAL.EXE`. The unchanged ASPECT
interpreter is `5c641ac4…`; disabling Alt-P still builds exact control `856a9c85…`.
[The validation receipt](validation/line-port-overlay.json) binds the products,
current source hashes, tests and isolated rebuild.

## Residency and ownership

The source-only builder first links the complete program. It extracts
LINE_PORT_CODE, redirects its ordinary MZ segment fixups to a reserved arena,
updates retained segment addresses and SS:SP, and removes those initialized
paragraphs from the resident image. The companion contains the extracted bytes
and their parent-relative relocation offsets. No original executable, guessed
instruction patch or prior object is an application input. The linked precursor
is retained as `terminal-linked.bin` for auditing, not as an executable product.

The arena starts 16,384 bytes into the separate 63,000-byte frozen-history
snapshot. Direct menus have zero frozen-history length; live history and both
screen frames remain separate. Admission requires the actual direct-menu owner
with no search/export operation. The far module state survives a queued internal
PROGRAM kind12 operation even after its visible menu closes. The resident
dispatcher enters module code only while that lease is live. Once the operation
and file claim retire, other owners can reuse the arena and a later Alt-P loads
the original bytes again. Uncertain file ownership retains the recovery path.

File reads and CRC32 work are limited to 512 bytes per foreground turn, with
continued serial/input service. Pending load work prevents a gratuitous BIOS
tick sleep. File size, CRC, sorted relocation bounds and physical target bounds
are checked before code entry; missing/invalid input produces a visible refusal.
Ready/error transitions request one menu repaint. Escape cancels loading;
other setup keys are accepted after the popup is ready. Close uncertainty asks
for DOS recovery rather than silently retrying an ambiguous handle. CRC binds
the compiled pair; it is not an authentication mechanism.

## Funding without smaller capacities

Resident minimum module allocation is **479,024 bytes**, compared with 479,504
for the unchanged control and 488,544 for the rejected resident Alt-P prototype.
All existing stacks, stream counts, file buffers and UART rings retain their
capacities. DGROUP is 65,520 bytes with 16 bytes spare; persistent loader state
is in CONFIG_CODE and the popup's 256-byte state is in the transient image.

The explicit near-cdecl CONFIG entries widen their return IP to CS:IP and
tail-enter a far adapter. Far adapters share a 30-byte argument-copy body, using
only volatile AX/CX and preserving SI/BP and caller argument slots. The declared
0..10-word cdecl contract is unchanged. A real DOS8086 fixture compares original
and compact bridges against compiled C callees: 2,200 calls check DX:AX returns,
caller slots despite callee parameter writes, stack balance, separate CS and
DS=SS. The linked verifier checks every selected stub, relocation and shared
body. Builds without the option retain their original bridge bytes.

The same companion also holds startup help data. `/?` streams the bounded text
span without executing it or allocating persistent storage. Actual DOS output
matches all 1,492 bytes from the source-built control, including when the current
drive differs from the executable's drive. A missing companion yields a bounded
message and nonzero exit. Executable module entry still requires full CRC/fixup
validation, independently of this read-only help path.

## Observed application gates

- Ten DOS8086 popup sessions pass the native-frame, routes, save/session,
  background traffic, refused-port, read-only and recovery-backup checks.
- An offline COM3/IRQ5 to COM1/IRQ4 move uses the actual handoff and restores
  all four UART/PIC/vector snapshots. The reusable lab copies the settings
  editor but does not invoke it for this native Alt-P workflow.
- The full six-held-stream/nested-child/EMULATE workload passes all 30 checks.
  A second 30-check run opens Alt-P before and after the scripts, proving that
  released code can be reloaded after another owner uses the scratch region.
- Missing, short, corrupted and extra-byte modules are refused visibly. Each
  test retries and then verifies ordinary input/parser service and cleanup.
- An isolated 692-file public-source export reproduces both products exactly
  and repeats save, serviced input, read-only and connected-port refusal cases.
  It has no originals, private configuration, prior objects or ancestor Git.
- Stock Enigma and Synchronet editor/viewer workflows pass through the recorded
  SynthModem proxy stage with 250ms sequence framing, 20ms byte pacing and the
  terminal-size probe. These are explicitly scoped to that bridge profile.
  Immediate forwarding failed Enigma editor semantics on both the new parent
  and the unchanged control; the passing profile does not validate that mode.
- Independent editor audits match all 1,920 cells and the cursor on each BBS,
  and derive the actual 80x24 NAWS negotiation from captured Telnet bytes.
- One ordinary DOS8086 parent passes the Enigma carrier-loss/redial workload:
  two ASPECT logins, partial-file cleanup and an exact 65,539-byte binary retry.
  An independent raw-stream audit checks both sessions, CRC/finish/controls and
  the received file. This transfer fixture uses 250ms framing and zero byte
  delay; it is separate from the paced editor fixture above.

```sh
./tools/dev --command python standalone/build_line_port_profile.py \
  --overlay --output build/NEW-line-port-overlay
```

These are named software gates. Matched package/source/deployment,
broader transfer/fault and physical Boca/SPA2102/SynthModem acceptance remain
separate. Other geometry/color comparisons, complete port pairs, live injected
close/rollback uncertainty and full F01–F16 parity remain open.
