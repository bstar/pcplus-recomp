# Stock sender failure replay

The [current source-built stock ENiGMA software-audio campaign](ENIGMA_STOCK_AUDIO_DOWNLOAD.md)
now completes the larger file with checked recovery and native conservative
offers. This document retains the earlier failed captures and byte-replay
counterexample for their recorded binaries; its references to a current cached
receiver describe that earlier checkpoint. The original observations are unchanged.


The [retained-byte replay](validation/stock-download-failure-replay.json)
reproduces the earlier stock ENiGMA download failure through two cached
source-built host receivers. Both return protocol status6 at verified position
15360, write the same four source-exact blocks of1024/2048/4096/8192 bytes,
request position15360 nine times and abort the stage exactly once. Neither
commits or installs a file. All12 diagnostic checks pass; transfer acceptance
remains false.

The byte input is the unchanged independently decoded caller capture from
`current-enigma-pressure-download-audio-01`, starting at its unique CRC-valid
PCPRESS.BIN ZFILE. This replay supplies no new peer responses and removes
elapsed-time effects. It demonstrates that the retained byte order is
sufficient for the core failure, without claiming to reproduce the sender's
timeout scheduling, the complete DOS/UI failure or a physical modem session.

The older library's core/codec C and header hashes match the failed campaign's
frozen manifest. The current library additionally validates its current source
dependencies. Name and metadata sources were not individually frozen by that
campaign; they match both cached library manifests and current source files.
The two libraries produce identical callback events, aborted bytes and complete
response wire on this input. Thus the receive-credit API addition does not fix
this default-policy counterexample. It is not claimed to be the identical
original DOS binary or an original-instruction replay.

The core currently handles a mismatched active-file ZDATA position by requesting
the verified position and returning to header scanning. Its separate completed-
file replay handler consumes stale framed data only after checked installation.
Further recovery work must consider stale frames during an active file and
timeout-driven queued retransmissions, while keeping CRC/position bounds,
progress deadlines, checked ownership and no-premature-ACK rules. Increasing a
retry count alone would not prove recovery or limit queued protocol leakage.

The isolated sender-credit candidate remains a separate integration test.
Success against that helper cannot close compatibility with an unmodified
remote sender. The [capability matrix](SEXYZ_CAPABILITIES.md) establishes that
stock8K mode ignores small receiver credit offers; standard1K mode is a remote
invocation choice. Neither replay nor capability testing grants an audio or
hardware pass.

```sh
./tools/dev --command python3 lab/bbs/replay_stock_download_failure.py \
  --cohort build/bbs-lab/current-enigma-pressure-download-audio-01 \
  --library-proof build/bbs-lab/sexyz-receive-credit-07/result.json \
  --campaign-library-proof build/bbs-lab/sexyz-receive-credit-06/result.json \
  --output build/bbs-lab/stock-download-failure-replay-new/result.json
```

The command reads retained evidence and cached source-built libraries. It does
not rebuild the running terminal, alter either board, or replace captures.
