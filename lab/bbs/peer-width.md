# Authenticated ENiGMA width navigation

This fixture exercises the experimental transaction parent against ENiGMA's
normal authenticated menu stack. It adds a synthetic `WIDTH` command to Main;
the upstream Telnet, client input parser and terminal writer are unchanged.
It is a separate server on `127.0.0.1:23239`, with copies of only the stock
lab's synthetic users and databases. The installed Node dependencies are
shared; no package installation or existing service changes occur.

Run the fixture through the pinned Nix BBS shell:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_peer_width_fixture.py setup \
  --candidate build/bbs-lab/peer-width-enigma-01
./tools/bbs-dev --command python3 lab/bbs/enigma_peer_width_fixture.py start \
  --candidate build/bbs-lab/peer-width-enigma-01
./tools/dev --command python3 lab/bbs/enigma_peer_width_dos.py \
  --candidate build/bbs-lab/peer-width-enigma-01 \
  --terminal build/SELECTED-SOURCE-PRODUCT/TERMINAL.EXE \
  --label peer-width-enigma-01
./tools/bbs-dev --command python3 lab/bbs/enigma_peer_width_fixture.py stop \
  --candidate build/bbs-lab/peer-width-enigma-01
```

Use a fresh candidate directory and result label. Select the actual source
built transaction parent explicitly; the driver validates its manifest and
all declared source inputs. It never replaces the default application.

The DOS8086 driver logs in as the synthetic `loclab` account, selects WIDTH,
uses Right and Left, selects narrow then wide mode, returns to Main and opens
Files. Each repaint positions a seven-byte marker at column121 or73 and asks
for CPR. ENiGMA must receive the actual DOS replies `[2,128]` or `[2,80]`.
The server event log and independently captured serial bytes must agree with
all five width/navigation states. A generic successful DOS exit cannot pass
the interaction audit by itself. Before/after UART/PIC snapshots and immutable
binary/config/source checks remain part of the maintained DOS harness.

This is an explicit test menu, not evidence that stock artwork automatically
adapts to132 columns. It does not cover an active ASPECT child, source
compilation, file transfer at wide width, arbitrary Telnet packet splitting,
physical carrier interruption or the Boca/SPA2102 connection. Synchronet
width composition and full application/card acceptance remain separate gates.

## Observed stock-server comparison

`peer-width-enigma-immediate-03` authenticates and sends the correct initial
`ESC[2;128R` reply, but the unmodified ENiGMA client consumes its fragments as
keys. Its passive input log records the actual TCP chunks. The following
arrows also arrive split; the width menu cannot advance. This is a retained
interaction failure despite normal DOS exit and sampled hardware restoration.

`peer-width-enigma-buffer20-03` passes all ten checks on the same binary,
fixture, source inputs and keyboard recipe, with an explicit20ms modem packet
deadline. All five server-side cursor replies, both arrow actions, narrow/wide
changes and subsequent File Base entry match. The independently captured UART
stream and server input log agree. The modem groups raw bytes without recognizing
or synthesizing ANSI; its source is unchanged. Use `--packet-delay-ms 20` to
select this experiment. TCP can still split a buffered write elsewhere.

A separate fixture can explicitly compose the previously checked incremental
decoder, using `setup --decoder-candidate build/bbs-lab/key-stream-check-3/candidate`.
That option checks its recorded upstream revision and both replacement source
hashes. It does not modify the stock fixture or an existing board. Keep its
results distinct from the stock immediate/buffered comparison.

`peer-width-enigma-framed-01` passes all ten checks with immediate forwarding
against that explicitly patched instance. It receives the exact same serial
width/key sequence and returns through Main to Files. The
[sealed comparison](../../docs/validation/enigma-peer-width.json) binds all
three runs and69 artifacts, including both the stock failure and the two
passing configurations. Its successful recorder result accepts this comparison;
`full_compatibility` and `accepted_for_deployment` remain false.

To reproduce the comparison receipt after the three selected runs:

```sh
./tools/dev --command python3 lab/bbs/record_enigma_peer_width.py \
  --immediate peer-width-enigma-immediate-03 \
  --buffered peer-width-enigma-buffer20-03 \
  --framed peer-width-enigma-framed-01 \
  --output docs/validation/enigma-peer-width.json
```
