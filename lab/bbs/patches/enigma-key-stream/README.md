# ENiGMA keyboard stream experiment

This is an isolated server-side experiment for upstream ENiGMA revision
`6c25317168b762f7d9088a54d3f8295438827a0e`. It does not change PCPlus, the
running stock BBS fixture, or anyone else's server. No upstream submission has
been made.

The pinned `core/client.js` decodes each incoming `data` event independently.
An arrow received as `ESC`, `[`, `D` can therefore become Escape plus printable
characters, while the same bytes received together become Left. This matches
the previously retained stock-server/DOS editor failures in
[packetization.md](../../packetization.md). TCP writes are not message boundaries;
modem batching can help a particular session but cannot guarantee server chunks.

`client.patch` integrates the source-owned `key_stream.js` before the existing
keyboard decoder. It holds incomplete escape sequences and UTF-8 code points,
delivers complete candidates immediately, and uses a 100 ms absolute first-byte
deadline for ambiguous/incomplete input. Pending input is limited to 128 bytes.
Lone Escape consequently has up to 100 ms additional latency. Slow sequences
that exceed that deadline can still split; this is an explicit policy requiring
network and physical-modem evaluation.

Raw transfer handlers bypass keyboard framing. An Enter callback that starts a
raw handler receives the untouched remainder of that same input chunk. Owner
changes discard tentative keyboard prefixes, and disconnect cancels timers and
stops processing the current chunk. Input received while ignored stays ignored
after a partial sequence completes; terminal reports still reach their existing
handlers. This experiment preserves the legacy decoder rather than redesigning
its Unicode, CP437 or malformed-input semantics.

Run from the PCPlus repository with the existing pinned ENiGMA fixture and its
installed dependencies:

```sh
./tools/bbs-dev --command python3 lab/bbs/patches/enigma-key-stream/check.py \
  --source build/bbs-lab/enigma/source \
  --output build/bbs-lab/key-stream-check-new
```

The output directory must be new. The runner verifies the source revision,
tracked cleanliness and original client hash, exports a separate candidate,
applies the patch there, and reuses only the fixture's installed `node_modules`.
It records source/tool/input identities, logs and hashes. It neither installs
dependencies nor starts a BBS. The Nix shell is pinned; reused installed modules
are not a fresh dependency-reproducibility proof.

The regression separates four kinds of evidence:

- A deterministic framing oracle covers all partitions of selected sequences,
  all 256 input bytes at every two-chunk split, bounded deadlines, ownership and
  disconnect behavior.
- The actual stock Client reproduces fragmentation failures. Its successful
  test exit means the expected defect was reproduced, not that stock passed.
- The experimental Client must match stock **unfragmented** key/report/editor
  results, then produce the same results under fragmentation. The actual
  multi-line editor tests verify Left insertion, Home insertion and Home plus
  Insert overwrite, without saving a message. Synthetic streams/configuration
  are used; editor exceptions propagate to the test.
- Existing upstream Client teardown, ViewController action-key, multi-line
  editor and full-screen editor focus regressions run against the candidate.

The frozen evidence is in
[`docs/validation/enigma-key-stream`](../../../../docs/validation/enigma-key-stream).
The wider F04/F05 and full application gates remain open. Required next evidence
includes a separately configured running patched server, the actual DOS client,
post-editor transfer handoffs, delayed/fragmented network input and physical
modem testing. A local server patch cannot fix an unmodified remote BBS.

An earlier candidate passed its narrow key tests but changed the unfragmented
event result for Escape followed by a four-byte UTF-8 character. Comparing to
the stock baseline caught that regression; keeping escape-prefixed UTF-8 intact
corrected it. The final oracle includes these inputs. The initial candidate and
counterexample remain local under `build/bbs-lab/key-stream-check-1`; they are
not represented as successful full compatibility tests.

The patch contains small excerpts of upstream BSD-2-Clause code; see
[UPSTREAM-LICENSE.txt](UPSTREAM-LICENSE.txt). Upstream source:
https://github.com/NuSkooler/enigma-bbs/tree/6c25317168b762f7d9088a54d3f8295438827a0e
