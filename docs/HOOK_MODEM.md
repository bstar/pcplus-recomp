# Prepared helper modem settings

The optional `--hook-modem` product prepares returned modem resources before
active connection state changes. It expands six configured commands, builds
the dial string, checks optional initialization reply framing and preserves
all eleven already-expanded response slots. The accepted proposal advances
from phase2 to phase3 only after the complete command offer is staged.
No UART, matcher, active modem, accepted register or baseline is changed.

## Corrected response validation

The earlier helper validator incorrectly ran command expansion over response
slots. The PRM importer and recovered matcher instead consume those bytes
literally: a caret is valid response data, and `^M` means two matcher bytes.
The validator now bounds response slots without expanding them. Commands still
use the native caret grammar and bounded expansion. The previous receipts
record historical runs with that restrictive policy; they do not establish the
correct response semantics. The new regression passes every nonzero byte in
each of the eleven slots from returned validation through the actual matcher,
including a two-byte literal `^M` and unterminated-slot refusal.

This is a deliberate correction in the optional helper-return products. The
older BBS-tested register executable remains byte-identical; it has no helper
return validator in its build. There is no new live BBS acceptance claim.

## Resource preparation

`hook_modem_prepare(settings490, target64, wait, output1086, result4)` is a
far cdecl entry in HOOK_CODE. The four pointed objects must be pairwise
disjoint, non-null and nonwrapping. Foreground admission checks the actual
terminal DS=SS with IF=1 and DF=0. The function performs no interrupt, port,
file, timer, active-state or transmission operations. Failure leaves the output
unchanged. Geometry/context rejection leaves the result unchanged.

The 1,086-byte plan contains:

| Offset | Bytes | Value |
| --- | --- | --- |
| 0 | 6 | active flag, effective DTE baud index, pause character |
| 6 | 774 | six expanded command buffers of129 bytes |
| 780 | 129 | prefix + expanded target + suffix |
| 909 | 176 | exact eleven16-byte response slots, including opaque tails |
| 1085 | 1 | zero padding |

The native nine-rate order covers300 through115200. Command order is
initialization, dial prefix, dial suffix, hangup, answer-on and answer-off.
Native expansion can emit an embedded zero; dial concatenation observes the
same C-string boundary as the production controller. Fully bounded ordinary
prefix/target/suffix input fits at most111 bytes in the129-byte destination.

When reply waiting is enabled, initialization uses the actual production
framing validator with the proposed pause byte. Each nonempty command requires
a physical CR; embedded LF before CR is rejected. The new far adapter accepts
an explicit pause rather than temporarily modifying the active pause global.
The existing controller entry still reads its active pause. Inactive modem
groups stage only the DTE rate; private modem data and target are unconsumed.

The four-byte result is status/field. Status0–7 means success, argument, rate,
command expansion, response bounds, reply framing, concatenation and owner
state. Fields0–5 identify commands,6–16 responses,17 target,18 concatenation,
19 framing, and FFFF other cases.

`terminal_hook_prepare_modem` copies validated phase2 settings into near
working storage, prepares commands against the current target/reply policy,
then publishes a1,086-byte far offer and sets phase3. Wrong phase or occupied
exchange/register owner rejects. Preparation failure preserves phase2 and the
old offer; a second stage cannot silently replace a ready offer. The existing
discard operation also releases phase3. Resource adoption remains separate.
The terminal converts its `/I:0..32767` duration to the framing check's enabled
flag; it preserves the actual duration for the normal initialization controller.
Active-modem helper diagnostics explicitly use `/I:3`.

## Evidence

[The receipt](validation/hook-modem.json) binds3,394 linked preparation cases,
4,822 returned-PRM/matcher cases,152 transaction admission cases, fifty real8086
helper attempts with seventeen exact modem offers, fourteen ASPECT register
recovery workflows, nine normal initialization workflows and six products
reproduced from703 source files without original inputs. The DOS diagnostic
preserves its bottom256-byte stack guard, active registers, retained baseline,
PRM file and hardware snapshots while publishing proposals/offers. The normal
initialization cases cover immediate/delayed/numeric acknowledgements, ERROR,
quiet fallback/timeout, multi-command sequencing and echo/unrelated lines.

The initialization runner now accepts an explicit source-built executable and
supplies valid8/4 scales when it selects a mouse-enabled product. Its first
attempt was rejected at startup because the older partial fixture left mouse
scales as A5A5; that run provides no initialization acceptance.

Resident code stays64,904 bytes and DGROUP65,520 bytes. Relative to the previous
executor checkpoint, HOOK_CODE grows2,127 bytes (including1,086 offer bytes)
and MODEM_CODE grows48 bytes. No near storage or near bridge is added.

```sh
./tools/dev --command python3 standalone/build_terminal.py \
  --external-render --mouse --notice-sound --notice-input --aspect-keys \
  --directory-keys --process-bank --session-capture --session-projection \
  --session-baseline --register-handoff --session-controls --hook-return \
  --hook-execute --hook-modem
./tools/dev --command python3 standalone/check_hook_modem.py \
  --output build/hook-modem-linked-next
```

The helper diagnostic adds `--hook-probe`; its test accepts `--hook-modem`.
Source proof, returned validation, admission and register recovery tools also
accept that selector. Normal initialization tests accept `--terminal` with
this product's `TERMINAL.EXE` path.

The subsequent [input resource stage](HOOK_INPUT.md) now prepares keyboard/profile
and translation offers. UART handoff, interactive
KEY kind2 routing and atomic settings/register adoption still need integration.
Full application, ENiGMA immediate-forwarding and physical modem gates remain
open. The new offer does not itself apply settings or establish hardware use.
