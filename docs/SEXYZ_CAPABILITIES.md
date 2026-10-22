# Stock sender capability limits

The [20-case capability matrix](validation/sexyz-capability-matrix.json) uses
the unchanged stock SEXYZ helper and the maintained host receiver over local
stdio pipes. It changes only complete CRC-checked ZRINIT offers in the fixture.
Every case completes the65797-byte source exactly and passes independent
source/CRC/EOF/ZFIN/OO/opposite-control checks.

For `-raw -8 sz`, all sixteen combinations of CRC16/CRC32, full-duplex,
overlap and256/8192-byte credit still produce8192-byte packets. CRC16 or clearing
overlap therefore cannot be assumed to turn this sender into a small-packet
peer. With overlap enabled, measured groups can reach14336 bytes despite an
8192-byte offer. This is a sender-capability measurement, not a new slow-link
transfer failure.

Removing `-8` selects a separate standard sender mode: all four measured cases
then use1024-byte packets. Without overlap, each synchronous group is1024 bytes;
with overlap and8192-byte credit, the measured group is7168 bytes. A256-byte
offer still does not bound those1024-byte packets. This CLI choice belongs to
the remote helper invocation; the DOS client cannot install it merely by
advertising different CRC flags.

The active audio test uses the separately identified finite-credit/EOF sender
candidate. That test cannot establish compatibility with an unmodified remote
sender. These measurements keep that distinction explicit and rule out an
unsupported flag-only solution. No fallback is installed, and no DOS/BBS/audio,
slow-link timing, physical modem or whole-application gate closes here.
