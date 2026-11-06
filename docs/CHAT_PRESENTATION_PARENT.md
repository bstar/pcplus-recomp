# Matching presentation loader in the parent

`--chat-presentation` selects the API0101 Chat module and matching resident
loader. It requires `--chat-storage`, which requires the loader, original
reference and large-frame options. This remains an opt-in integration build:
normal terminal Chat entry and input/output hooks are not enabled.

Parent `75fdb753` has 478,112 minimum module bytes and retains 29,897 paragraphs
including PSP after startup shrink. Near data remains 65,488 bytes. The loader
bank is 1,296 bytes, 32 more than the API0100 loader. No stack, stream, history
or frame capacity was reduced. This is measured admission for this build,
not a guarantee that the remaining frontend will fit.

The parent composition fixture now selects its ABI from the manifest. In the
presentation build it gives the actual parent loader an 8KB module window in
the exclusively borrowed frozen workspace, with session state at offset12288
and presentation context at13000. Both tested relocation windows end below
state. The existing view frame holds the saved screen; the module paints VGA.
The caller uses the parent's actual DS=SS and declared stack, not a replacement
loader or Chat implementation statically linked into the test host.

Two actual DOS8086 acquire/load/open/type/close/unload/release cycles pass,
including visible/hidden cursors, original full-screen and cursor restoration,
active-unload refusal, continued ordinary viewer-wrapper exclusion, reset
refusal, image CRC, canaries and unchanged PSP/JFT/largest free block. A linked
guard suite still passes 54 cases and 16 lease cycles. Parent main is not run
by this composition fixture.

Normal-main ASPECT admission is tested separately: six buffered streams remain
open across three real child launches, including missing-file recovery, with
normal exit and hardware restoration. The current-source ASPECT rebuild is
byte-identical `cbdee194`. A fresh 635-file public source export reproduces the
parent, module, generated header, composition host and result exactly, without
originals, private settings, prior objects or ancestor Git. Disabling only the
presentation option retains exact parent `75c84373` and its passing original
API0100 DOS composition.

Stock Synchronet editor and external-viewer return pass in the established
386/UMB helper profile, including exact restored editor frame/cursor and
subsequent editing. The initial test omitted explicit display startup settings;
both the new and unchanged parent reject that same incomplete synthetic PRM
before modem traffic. Those captures remain separate from the corrected pass.

The first Enigma carrier test reconnects and authenticates twice, restores
hardware, removes the partial file before redial and exits normally. Its retry
does not complete: the receiver cancels after independently CRC-verified data
has reached a 48,128-byte source prefix. The recipe supplies a key after its
60-second wait; cancellation appears 56.037 seconds after the first receiver
request in that connection's trace. This supports testing a longer wait but
does not establish a complete transfer or diagnose every reliability issue.
Keep the failed capture and its partial-wire analysis when assessing the
separate 150-second-wait control; do not silently replace the failed result.

That control passes the full carrier-loss/redial/exact-retry workflow and an
independent raw-wire CRC/finish/control audit. The recovered file is exactly
65,539 bytes. Both runs use identical applications, PRM, scripts and sampler;
the declared differences are the wait and generated keyboard helper, ephemeral
dialing port and mutable server session state. No application timing behavior
was patched. The prior unobserved redial miss remains unattributed.

The [presentation component](CHAT_PRESENTATION.md) documents the module API and
separate four-geometry lifecycle tests. The [checkpoint receipt](validation/chat-presentation-parent.json)
records current parent and BBS evidence, including unsuccessful test attempts.

Next, bind original Alt-O/reference entry, pre-dequeue ownership, RX/TX and real
history/log callbacks, Help/direct TEXT, notices/traps and retirement policy.
Repeat final parent memory, connection, package and physical gates after those
hooks are integrated. The earlier intermittent Enigma redial miss remains an
open reliability issue. No selected payload, physical files or production
SynthModem/Enigma configuration changes at this checkpoint.
