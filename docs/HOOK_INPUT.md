# Prepared helper input resources

The optional `--hook-input` product freezes translation lookup paths before
helper EXEC and prepares returned profile/translation resources in a private
offer. Missing or invalid resources reject before active settings change.
The caller can inspect or discard the offer; resource adoption and interactive
KEY kind2 routing remain unimplemented.

## Binding and preparation

The executor first projects the actual session. Once projection succeeds, it
calls `terminal_hook_bind_input` before allocating/executing the helper. The
existing translation owner captures canonical current/PCPLUS fallback paths.
The profile keyboard path was already frozen by normal startup binding. The
helper can change DOS CWD without redirecting those later reads.

`terminal_hook_prepare_input(result12)` requires phase3 (modem offer ready),
a valid resource binding and no parser, transfer, monitor, controller, register
or exchange owner. Foreground DS=SS must identify the actual terminal group,
with IF=1/DF=0. Supported profiles are4/6 and translation modes0/1/2. Explicit
`/X` rejects a returned mode change rather than silently deferring it.

Unchanged resources reuse the exact active keyboard/table bytes. A profile
change uses the existing profile stager: source-owned defaults, or a checked
selected profile from the frozen KBD path. A translation change stages the
matching table; only a missing current file may fall back. Damaged files do
not trigger fallback. Modes0/2 retain unused table bytes and need no XLT read.

The new `xlt_live_offer` copies a matching stage without consuming it or
changing `active_path`/active binding. This avoids the partial adoption that
would result from calling `xlt_live_commit` into a temporary buffer. Existing
setup/reload behavior and executables are unchanged when the option is absent.

After both resource operations succeed, the full1,212-byte offer is copied to
retained far storage and phase advances to4:

| Offset | Bytes | Value |
| --- | --- | --- |
| 0 | 8 | profile, translation mode, profile-changed, translation-changed |
| 8 | 948 | exact79-slot keyboard profile |
| 956 | 256 | exact translation table, including unused bytes |

The12-byte result contains status/source-status words and the existing8-byte
translation IO result. Status0–5 means success, argument, owner state, policy,
keyboard and translation failure. A failed preparation leaves phase3 and the
previous offer intact. Private reader scratch/readiness may change; active
keys, mode/table, editor source identity, registers and PRM remain untouched.
Discard clears resource binding/profile readiness and releases the proposal
phase. New binding replaces stale private translation work before another EXEC.

## Evidence and footprint

[The receipt](validation/hook-input.json) binds39 linked input checks, the
existing3,394 modem and4,822 return/matcher cases,152 executor admission checks,
nineteen actual8086 input resource workflows, fifty helper regression attempts,
fourteen register recovery workflows and seven products reproduced from708
source files without original inputs.

The input workflows execute a source-built helper that actually changes CWD to
`D:\ALT`, confirmed by DOS47, with valid alternate KBD/XLT decoys there. Cases
cover default/imported4↔6 profiles, removed/damaged/missing keyboard blocks,
short/long/missing XLT files, valid fallback, malformed-current refusal despite
valid fallback, modes0/1/2, unchanged files removed after startup and explicit
`/X` policy. Successful offers compare byte for byte. Failed offers retain all
1,212 sentinel bytes. Before/after keys, table, mode, XLT editor source identity,
projected PRM, baseline, accepted registers and hardware remain identical; the
bottom256 bytes of the real8KiB stack retain their guard.

These diagnostics run after genuine startup and before UART/mouse acquisition.
They establish resource preparation in the terminal layout, rather than online
helper routing, resource adoption or physical hardware behavior.

DGROUP remains65,520 bytes. Resident code grows four bytes to64,908; HOOK_CODE
grows1,846 bytes (including1,214 bytes of offer/binding storage), and CONFIG_CODE
grows125 bytes. Both the preceding modem-preparation executable and older
BBS-tested register executable reproduce byte for byte.

```sh
./tools/dev --command python3 standalone/build_terminal.py \
  --external-render --mouse --notice-sound --notice-input --aspect-keys \
  --directory-keys --process-bank --session-capture --session-projection \
  --session-baseline --register-handoff --session-controls --hook-return \
  --hook-execute --hook-modem --hook-input
./tools/dev --command python3 standalone/check_hook_input.py \
  --output build/hook-input-linked-next
```

Build `--input-probe` for the dedicated diagnostic and run
`standalone/test_hook_input_dos.py --output build/hook-input-DOS-next` through
the same Nix wrapper. Existing source proof, modem/return/admission, helper and
register tests accept `--hook-input` as a product selector.

Next is checked mouse/UART ownership and atomic adoption of the complete
settings/register/resource transaction, followed by interactive safe-point
routing. Full application, ENiGMA immediate-forwarding and physical modem gates
remain open. A phase4 offer is not permission to switch those owners.
