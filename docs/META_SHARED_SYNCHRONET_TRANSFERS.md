# Shared-parent Synchronet transfers

The installed candidate's exact parent bytes pass actual stock Synchronet
ZMODEM download and upload through the on-disk SynthModem Telnet proxy.
The11521-byte download and65539-byte upload match exactly; the latter includes
all byte values plus Telnet/window-control patterns. The
[receipt](validation/meta-shared-synchronet-transfers.json) binds the package,
server/helper identities, protocol captures and official metadata audit.

Both run DOS8086, COM3/IRQ5,19200,8N1,HARD with VGA25/status visible and80x24
advertised to the server. The actual BBS helper supplies ZMODEM. Independent
auditing requires data/header CRCs, offsets, exact length, ZEOF/ZFIN/OO and
post-transfer BBS input/response, plus unchanged PRM/source files, hardware
restoration and no staging residue. Upload also verifies physical installed
bytes and official FileBase CRC16/CRC32/SHA1/MD5/size metadata. Proxy input and
output must equal the audited streams exactly; no terminal/protocol replies
are synthesized. Tests use250ms framing and0ms input-byte pacing.

The owned lab's existing lock prevents concurrent DOS integration sessions.
Official archive/runtime identity and static-source/message-body snapshots
bracket the upload; they do not retroactively bracket the earlier download.
Both wrapper runs separately verify their selected server/helper/config hashes.
Synthetic account statistics and file records are expected to change.

No physical machine files, running SIP/audio service or BBS configuration were
changed. The installed candidate still awaits the user's physical connection
and modal-return observations. These results supplement the Enigma transfers
and earlier Synchronet rendering/editor regressions without closing physical
acceptance or the remaining original-feature inventory.
