# Chat native-parser wait and cancellation

This follow-up addresses two failures found by exercising real BIOS keys while
foreground Chat TEXT is inside the native echo parser. It is an opt-in
development checkpoint, separate from installed-package and physical acceptance.
The validation receipt records final identities and passing/negative evidence.

## Failures and changes

The first foreground TEXT parent, e03c6e41, can exhaust4096 read attempts before
its whole36-BIOS-tick echo deadline. A synthetic delayed CSI continuation then
arrives after Chat has aborted and appears in the ordinary terminal. A CPU
control with a clock advancing once per256 polls independently reproduces
budget fault4 at4096 polls, before36 ticks. The initial CPU fixture jumped the
clock to100 after admission instead of starting it there; its corrected control
sets the initial clock first and is the authoritative negative evidence.

The echo owner now replenishes4096 attempts when the BIOS tick changes. The
whole36-tick deadline is still measured from admission and is never extended
by incoming bytes or clock progress. A stopped clock still terminates after
4096 read attempts. Cancellation and clock are serviced before the final
budget refusal, giving4097 polls in the plain stopped-clock test. The nested
alternate CSI-M controller already polls before reading and retains its tested
4098 total-poll edge count. No sleep, private stack or new near allocation is
introduced; the progress-tick word remains in the optional echo bank.

The clock-only follow-up, fad73851, exposed a second bug. The frontend's busy
branch passes cancellation keys to the parent, but the next redisplay guard
consumes every key while storage owner2 is active. Escape and Alt-H therefore
wait for the deadline rather than cancelling promptly; a single Alt-X is lost
and leaves the program running. The actual DOS quit test times out after40
seconds. Earlier tests that only checked eventual return could not distinguish
this timeout recovery from successful local cancellation.

The redisplay storage guard now passes Escape, Alt-H and Alt-X to the existing
parent cancellation/connection dispatcher when native Chat echo is enabled.
All other keys retain the guard. This does not enter viewer code, unload the
busy module, release its executable storage or manufacture a BIOS key. The
echo scope unwinds first; normal module/frame retirement follows. Alt-H and
Alt-X retain the configured modem hangup and exit controller.

## Actual DOS observer and tests

`standalone/test_chat_busy_keys_dos.py` uses the ordinary parent main, imported
KEY text and real BIOS key events. TEXT sends GO and then echoes ESC through
the actual native parser, which needs an incoming continuation. Four cases
cover a delayed CSI completion with queued X/Enter, Escape, Alt-H and a single
Alt-X. The completed send must put ESC/TAIL before queued typing on the wire;
cancelled sends must not emit ESC/TAIL. Ordinary input/CPR, frame/banner return,
configured hangup, normal exit and hardware restoration are checked where
applicable.

`standalone/chat_busy_watch.asm` is a passive INT16 observer which tail-chains
the original BIOS provider with registers and flags restored. It validates
DS=SS, the exact module signature/API and foreground STEP/TEXT/owner/parser/
wait state using offsets from the selected parent map. It reads the actual
BIOS queue before dequeue, confirming queued X during the wait. BIOS tick
samples distinguish prompt cancellation from36-tick expiry. It also observes
owner/parser/wait retirement. It only writes its own resident sample buffer;
there is no product-memory write, key injection, UART access or substituted
parser/BIOS service. The observer consumes conventional memory, so unobserved
nested-ASPECT capacity testing remains separate.

The CPU suite also covers the whole deadline with more than4096 total polls,
stopped-clock expiry, register/cursor restoration, native CSI/C1 with IRQ input,
external cancellation/modem changes, nested alternate wait and admission
refusals. Its hardware remains modeled and its Chat owner/context supplied;
it does not replace the normal-main BIOS tests.

Full original Chat/controller execution, Help/Alt-Z/configuration, broader
binding/failure/geometry/mouse coverage, flow/printer/logging stress, final
package and physical analog/SIP/audio acceptance remain open. Stock BBS
regressions leave Chat inactive; their scope is reported separately.
