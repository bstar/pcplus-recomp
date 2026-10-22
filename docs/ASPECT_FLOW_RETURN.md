# Script software-flow control and parent return

[Validation](validation/aspect-flow-return.json) covers two source-built8086 DOS
sessions with the normal parent4dae4ddb and unchanged ASPECTdfee1e95. One uses
SOFT; the other uses BOTH. DOSBox-X nullmodem keeps CTS asserted, so BOTH is not
a hardware-flow stall test.

The owned peer recognizes KEYREADY from the actual script, sends XOFF followed
by GO, waits1.2seconds, then sends XON. GO releases the script's WAITFOR while
its following TRANSMIT remains paused. A passive timer reads the real child
pause flag for22 BIOS ticks. It neither changes product state nor substitutes
UART status. Both scripts then transmit2,048 bytes and publish FLOW.OK. The
parent subsequently accepts manual `ready`, responds to the peer's cursor
query and performs the configured hangup. All2,113 serial bytes, including the
two XOFF/XON pairs surrounding child ownership, match the declared stream.

The independent auditor checks the peer's chronological receive events, absence
of application bytes during XOFF, native child exit, JFT and file-owner snapshots,
42 hardware bytes before/after, source identities and every capture hash. The
parent is observed on its own stack for105 ticks after return, with its pause
flag clear. The same expected whole stream applies to both modes.

Run the fixture with the pinned toolchain:

```sh
./tools/build test-aspect-flow-return-dos
```

For a named evidence run and independent sealing, choose unused output names:

```sh
./tools/dev --command python3 standalone/test_aspect_flow_return_dos.py --label selected-run
./tools/dev --command python3 standalone/audit_aspect_flow_return.py \
  --run build/aspect-flow-return-dos/selected-run \
  --cohort build/aspect-flow-return-dos/selected-accepted \
  --output docs/validation/selected-flow-return.json
```

The first fixture resumed after2seconds. The existing sender's36-BIOS-tick
pending bound expired first, producing child14/serial7. Its observer also used
the wrong segment for the child's DS field; its zero pause count is invalid.
The second fixture corrected that segment and resumed within the bound, but a
superfluous driver space failed the exact-stream assertion. Both attempts and
their frozen producer sources remain in the accepted cohort as rejected history.
The third fixture removes that key and checks all flow bytes as well as data.

This does not establish acceptable behavior for arbitrary BBS pauses. Longer
XOFF/CTS stalls, timeout/cancel handback, configurable stall policy, sustained
receive high water, disconnect/reconnect, software audio flow pressure and
physical UART/modem timing still need separate coverage. The passing normal
recorder audio route does not close those requirements. Every full application
gate remains open.
