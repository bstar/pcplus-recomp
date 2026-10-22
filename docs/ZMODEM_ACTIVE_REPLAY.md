# Checked active-file ZMODEM recovery

The source-built terminal can now consume an old active-file data frame,
compare its stored prefix, append only a new suffix and request the verified
current position. It no longer treats that frame's payload as header-search
noise or repeatedly acknowledges endpoints behind its stored file position.
The [validation record](validation/zmodem-active-replay.json) binds current
source, actual DOS component tests, linked terminal tests and a separate
unmodified-stock-sender host experiment. These scopes are distinct.

The [native conservative follow-up](validation/zmodem-native-conservative.json)
now covers53 host cases,99 actual DOS cases,64 file-owner fault assertions,
14 linked recovery cases and160 ordinary linked regressions. Checked reception
with an explicit credit from1 through8191 clears CANOVIO while retaining CANFDX
and CRC32 (flags33). Default/8192-byte checked offers and all legacy API offers
retain flags35. This selects synchronous framing; it does not force a peer to
use256-byte packets. The8192-byte decoder workspace remains available.

Two fresh stock-helper host experiments complete65797 exact bytes, with helper
exit0 and full source/CRC/EOF/ZFIN/OO/opposite-control audits. The6000bps case
uses native default8192-byte credit/flags35; the1200bps case uses native256-byte
credit/flags33. Both experiments require every complete offer to pass through
byte-for-byte and reject rewriting. Both receiver libraries are byte-identical
to the current host build. The native ledger is a component/host checkpoint;
current DOS-to-stock-BBS software-audio acceptance remains a separate campaign.
The counts and wrapper-selected1200bps experiment below describe the earlier
[active-recovery checkpoint](validation/zmodem-active-replay.json).

The [independent lrzsz follow-up](validation/zmodem-native-conservative-lrzsz.json)
adds two actual DOS automatic-receive sessions for this same terminal binary.
CRC16 and CRC32 each pass empty, one-byte and65797-byte all-octet files with
native256-byte synchronous offers, exact passive source/CRC/EOF/finish checks,
post-transfer keyboard/DSR and normal DOS/UART/IRQ restoration. It is separate
from the stock-helper host experiments and current stock ENiGMA audio campaign;
the direct harness has no per-byte opposite-control timing evidence.

The opt-in `zm_run_checked_profile` API accepts a far readback verifier in
addition to the existing callback table. Legacy APIs pass no verifier and keep
their existing mismatch policy. The normal terminal selects the checked API.
The workspace grows by the verifier and a32-bit recovery frontier; callers must
recompile. Near arguments, far callbacks, DS=SS and the exclusive transfer arena
remain required. The ten-entry ordinary callback table retains its layout.

For a frame starting behind the active file position, the engine:

1. Consumes and CRC-checks a complete data subpacket.
2. Compares any old prefix against the currently owned stage.
3. Appends only a new suffix, with checked storage results.
4. Sends ZRPOS for the stored position when the sender remains behind, or ACK
   when a requested response reaches the verified current position.

An old CRCE frame also requests the stored position after framed consumption.
CRC failures cannot reach the readback verifier or earn an ACK. A stored-prefix
mismatch aborts; it cannot silently combine changed old bytes with a new tail.
Future positions retain ordinary recovery. File installation still requires
the checked EOF/close/rename path and complete protocol finish remains separate.

Protocol retry debt can retire when verified old-packet endpoints move forward.
This permits a sender that reduces its packet size to catch up through more
than ten old packets. Repeated or rewound endpoints remain bounded. Readback
does not advance accepted file position, byte accounting or the terminal's
accepted-progress watchdog. Linked tests observe the real progress routine
without replacing it, including successful recovery with a moving modeled
clock and timeout after an explicit idle-clock jump.

`transfer_download_compare` uses the existing exclusive stage handle. It reads
at most128 bytes at a time and restores the append cursor after success,
mismatch, read failure and initial seek failure. A failed restore poisons the
stage and records its secondary DOS error. Zero-length comparisons perform no
filesystem IO; invalid ranges or overlaps reject before IO. No stage is reopened
or installed by readback. The terminal services cancellation/transport between
bounded128-byte calls. Offsets and saved byte counts remain32-bit.

The fault diagnostic executes8086 code with a declared fault filesystem. Its64
assertions cover short/oversized read results, initial/restore seek errors,
wrong reported cursor positions, preserved first failures, rejected append and
installation, and checked close/removal. The separate97-case actual DOS session
suite uses real DOS read/seek and file installation, including overlap across
64KiB. The39-case host check includes a source/hash-verified predecessor which
fails the forward-recovery case. Fourteen linked terminal cases cover the UART
ISR, real engine/verifier/file-owner instructions and modeled kernel/hardware.
Ordinary linked regression receipts are retained separately in the ledger.

The stock SEXYZ helper completes65797 exact bytes in the paced host experiment
with a6000bps input ceiling, default8192-byte credit and default flags35. Every
complete offer is byte-identical before and after the experiment's wrapper.
The independent source/CRC/EOF/ZFIN/OO/opposite-control audit passes and the
helper exits0. The receiver library is byte-identical to the current host build;
the isolated prototype's active-replay function is the adopted implementation.
This is a live helper/host-memory-storage test, not DOS file IO, DSP/audio or a
logged-in BBS workflow.

The earlier completed6000bps experiment exhausts its retry budget at15360
bytes despite forward verified old endpoints. That failure is retained. Other
ACK-old-endpoint explorations were intentionally stopped after the fully
audited resume-position prototype succeeded; their partial traces are neither
acceptance nor spontaneous product failures. The original stock audio failure
and the previous successful isolated-helper audio campaign remain historical
evidence for their exact binaries and conditions.

The separate1200bps experiment also completes65797 exact bytes with helper
exit0 and full independent source/CRC/finish/control checks. It requests flags33
and256-byte credit through the explicitly identified wrapper; its receiver
library is also byte-identical to the current host build. That earlier checkpoint does not implement native selection; the follow-up
above implements and tests it without the wrapper.
Current DOS/stock-BBS/audio acceptance, arbitrary-duration load, other protocol
directions, physical Boca/SPA2102 behavior and all F01–F16 application gates
remain open. No14.4 negotiation or complete application claim follows.

```sh
./tools/build test-zmodem test-terminal-zmodem-live
```

The optional stock-helper experiment requires the ignored, pinned installed
helper and writes only a new owned lab directory:

```sh
./tools/dev --command python3 lab/bbs/probe_sexyz_active_replay.py \
  --output build/bbs-lab/stock-active-replay-new \
  --bps 6000 --credit 8192 --flags 35
```
