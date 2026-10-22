# Stock ENiGMA larger-file software-audio download

The [accepted current campaign](validation/current-enigma-native-conservative-audio-01.json)
completes one65797-byte automatic ZMODEM download with the source-built DOS
terminal through software SIP/RTP/V.22-1200 DSP/Telnet to the owned stock ENiGMA
board. This campaign uses the unchanged stock SEXYZ helper, without the earlier
sender-credit candidate. It passes79 producer/independent checks and19 verifier
counterexamples. Physical Boca/SPA2102 acceptance and all F01–F16 remain open.

| Observation | Result |
| --- | --- |
| Terminal SHA256 | `4986b1991a9973234c37f81fdbd7ebf22d84ba8fe03f3f9a159cccba3f6a6d04` |
| ENiGMA revision | `6c25317168b762f7d9088a54d3f8295438827a0e` |
| Stock helper SHA256 | `d1aeb1347fee332be75dd638dd4cb10a1bf7c418d96d0ebb79ca90470b0ed4bd` |
| Launch policy | Native `/Z:256`, credit256, flags33: CANFDX/CRC32, no CANOVIO |
| Installed file | `PCPRESS.BIN`,65797 exact bytes, above64KiB |
| Source and received SHA256 | `205e79f0e63f900f27e159239f186e23b955f89203b9bf3b9940fd409d5d7078` |
| Observed protocol interval |800.600 seconds, ZFILE through OO at the decoded frontend |
| Effective file payload rate |82.18 bytes/second; includes recovery and protocol time |
| Largest observed packet / synchronous group |2048 /2048 payload bytes |
| Verified retransmissions |18 packets,18432 payload bytes; none after EOF |
| Exact online / BBS-display bytes |1663 /157310 |
| Official download count |3 to4 |
| Finish and interaction |CRC/source/position/EOF/ZFIN/OO and76 opposite-control records; Search/List resumes in the authenticated session |
| Cleanup |DOS0, Node0, helper0, no staging file, UART/IRQ state restored, keyboard helper retired |
| Provenance |453 unchanged root/frozen-copy inputs, including all367 terminal build sources and its manifest |

Small receive credit remains a request: the stock sender uses packets larger
than256 bytes. The receiver keeps its8192-byte decoder workspace. The checked
active-file path verifies stored prefixes and requests the current position;
it does not append duplicate data or acknowledge an unverified endpoint. This
run exercises recovery rather than avoiding retransmissions. The separately
accepted sender-candidate campaign retains its own smaller packet bounds and
zero-retransmission result; those measurements do not describe this stock run.

The independent audits cover the complete BBS input/display streams, independently
decoded caller waveform, contiguous serial ownership, exact installed bytes,
all protocol CRCs and finish, official accounting, authenticated post-helper
menus and normal return. The79 checks comprise25 producer,26 independent byte/
cleanup,12 serial-ownership and16 download-policy/protocol checks. The19 negative
cases comprise nine damaged TCP-reference protocols, two premature-control
timings and eight altered receive-policy declarations. The latter keep raw
captures unchanged; valid alternative declarations fail only the policy gate,
while internally inconsistent declarations fail before a receipt is written.

The original stock larger-file failure at15360 bytes remains retained. The
[native host/component checkpoint](validation/zmodem-native-conservative.json)
and [independent CRC16/CRC32 DOS/lrzsz runs](validation/zmodem-native-conservative-lrzsz.json)
are supporting evidence with distinct transport and storage scopes. This audio
acceptance is for the recorded current binary and one file/direction/profile;
it does not establish arbitrary-duration load, other speeds, upload/cancel/
reconnect coverage for this binary, physical analog hardware or complete PCPlus.

The owned ignored cohort is
`build/bbs-lab/current-enigma-native-conservative-audio-01`. Raw streams, frozen
source copies, start/exit/clock manifests, exact journal ranges and all audit
receipts remain there. The public validation record binds their hashes. Audits
use the pinned Nix modem environment and canonical module entrypoint:

```sh
./tools/modem-dev --command python3 lab/bbs/audit_audio_download_bound.py \
  build/bbs-lab/current-enigma-native-conservative-audio-01 \
  --output build/bbs-lab/current-enigma-native-conservative-audio-01/recheck.json
```

Use a fresh output name for a recheck. Capture-bound results remain historical
if later source or server state changes; re-run the campaign for a new binary
instead of rewriting the accepted observations.
