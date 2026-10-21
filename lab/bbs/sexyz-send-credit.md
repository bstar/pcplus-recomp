# Finite receive credit in the stock sender

The [stock-helper experiment](../../docs/validation/sexyz-receive-credit-stock.json)
uses the unchanged ENiGMA-distributed SEXYZ3.6 helper, a source-built host receiver
and four explicit ZRINIT offers. Every65797-byte transfer passes independent
source/CRC/EOF/ZFIN/OO/control checks in fast local pipes.

| Offer | Maximum packet | Maximum synchronous group |
| --- | ---: | ---: |
|8192 bytes, overlap enabled |8192 |14336 |
|1024 bytes, overlap enabled |8192 |8192 |
|256 bytes, overlap enabled |8192 |8192 |
|1024 bytes, overlap disabled |8192 |8192 |

Reducing credit alone therefore does not bound the observed sender packet. This
helps explain why a slow path needs more than a smaller receiver offer, without
claiming this experiment reproduces audio timing or exclusively explains the
retained failure. The live BBS/helper remains unchanged.

## Isolated Nix candidate

The [candidate record](../../docs/validation/sexyz-send-credit-candidate.json)
builds pinned upstream commit `e7a825704ef5329c7ef8408749671291a85ef7f2` through
Nix. The verified standalone source closure has only `zmodem.c` changed; bytes
outside `zmodem_send_from` remain identical. The receive/closing implementation
and DOS client are unchanged.

The sender computes an effective read limit before `fread`, bounded by remaining
finite receive credit. EOF comparisons use that actual limit, so a full short
credit read is not mistaken for EOF. A credit-filling group requires ZCRCW, and
credit resets only after its matching ZACK. Zero advertised credit retains the
existing unlimited policy.

The same four65797-byte transfers now stay within their advertised packet/group
limits:8192/8192,1024/1024,256/256 and1024/1024 respectively. Another72 cases
exercise credit1..8192, overlap on/off, short/exact/oversize file boundaries,
four unlimited-credit framing comparisons with stock, and two injected receive-
byte CRC recoveries. Full source/finish/control and exact native fixture files
are mandatory. These use host callbacks and pipes, not DOS storage or audio.

```sh
./tools/build-sexyz-send-credit \
  --out-link build/bbs-lab/sexyz-send-credit-build-new --json
./tools/dev --command python3 lab/bbs/probe_sexyz_receive_credit.py \
  --helper build/bbs-lab/sexyz-send-credit-build-new/bin/sexyz \
  --output build/bbs-lab/send-credit-probe-new
```

The build copies verified source before applying the transformation, retaining
the upstream source manifest and a separate change manifest. No new distribution
packages, adapter firmware, global helper or BBS configuration are installed.

## Next integration

The DOS receiver currently advertises8192 bytes. The sender candidate alone
would still permit a group too large for the laboratory1200-bps reply timing.
Define and test an explicit modem receive-credit policy, then pair it with an
isolated helper/server candidate through the actual DOS/audio path. Retain the
stock counterexample, exact full streams, installed file, protocol completion,
official accounting and post-helper cleanup gates. Configurable profiles and
high-rate behavior need separate evidence; do not trade away the general
compatibility objective for one conservative profile.

This candidate is not installed on the live owned BBS and has no accepted audio,
physical Boca/SPA2102 or whole-application result.
