# Synchronet width composition

The separate loopback fixture on `127.0.0.1:23240` runs the official lab
Synchronet executable with a private runtime copy and the synthetic `LABUSER`
account. A test command-shell wrapper changes width and receives arrow keys,
then loads the unmodified stock command shell. The existing lab server remains
unchanged. Setup checks that the copied user database contains only LABUSER.
Private node state, statistics, PID and recycle files remain mutable; the
actual configuration, executable and module inputs are hashed and checked.

```sh
./tools/bbs-dev --command python3 lab/bbs/synchronet_peer_width_fixture.py setup \
  --candidate build/bbs-lab/peer-width-synchronet-03
./tools/bbs-dev --command python3 lab/bbs/synchronet_peer_width_fixture.py start \
  --candidate build/bbs-lab/peer-width-synchronet-03
./tools/dev --command python3 lab/bbs/synchronet_peer_width_dos.py \
  --candidate build/bbs-lab/peer-width-synchronet-03 \
  --terminal build/SELECTED-SOURCE-PRODUCT/TERMINAL.EXE \
  --label peer-width-synchronet-04
./tools/bbs-dev --command python3 lab/bbs/synchronet_peer_width_fixture.py stop \
  --candidate build/bbs-lab/peer-width-synchronet-03
```

Use fresh candidate and result names. The explicitly selected source-built DOS
parent runs as an8086, with COM2/IRQ5,19200/8N1/HARD and immediate modem
forwarding. The wrapper uses the server's native `console.getxy()` parser,
which sends the query and receives the actual DOS cursor reply. Normal
`console.inkey()` handles the arrows. No reply or key is supplied by the
fixture. Five states must match:132/selection0,132/1,132/0,80/0,132/0.
The required CPRs are `(128,2)` four times and `(80,2)` once, independently
confirmed in the UART capture.

The return audit requires both the actual `text/menu/transfer` server route
and the final `File` prompt. Generic mentions of File Transfer on Main are
insufficient. The first complete pilot passed the width checks but its
original broad text check incorrectly accepted Main. The stricter retry
retains that failure: its `T` dismissed the stock shell's `[Hit a key]` pause.
The current recipe explicitly dismisses that pause with Space before sending T.

`peer-width-synchronet-04` passes all nine producer checks and the independent
audit. The [sealed receipt](../../docs/validation/synchronet-peer-width.json)
binds22 artifacts, the five server-side cursor results, actual arrow bytes,
the File Transfer server route, final File prompt and exact42-byte hardware
restoration. It uses immediate forwarding; no modem batching workaround is
applied. The receipt retains `full_compatibility=false` and
`accepted_for_deployment=false`.

```sh
./tools/dev --command python3 lab/bbs/record_synchronet_peer_width.py \
  --label peer-width-synchronet-04 \
  --output docs/validation/synchronet-peer-width.json
```

This is a synthetic command shell, not proof that stock artwork adapts to132
columns. Active ASPECT sessions against a BBS, compilation/transfer at wide
width, carrier/OS interruption, physical modem behavior, full application
acceptance and card deployment remain separate gates.
