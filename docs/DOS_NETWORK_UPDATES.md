# DOS Ethernet file updates

Hardware identified from bstar's photo: 3Com EtherLink III **3C509-TP**, with an
installed boot ROM used for XTIDE. Ethernet uses the RJ45 connector, not AUI.
The Boca modem already uses COM3/3E8h/IRQ5. Preserve those settings and the
NIC's existing boot-ROM enable, address and size.

The attached DOS card now has these manually started tools in `C:\NET`:

- 3C509.COM packet driver and 3CCFG.EXE adapter configuration/diagnostics.
- The card's existing mTCP2020 DHCP, FTP server/client, Ping, packet utility
  and HTTP client, copied without modifying `C:\UTILS\NET`.
- MTCP.CFG using software packet interrupt60h, hostname LOC386, MTU576 and
  a single FTP client; DHCP supplies the IP/network settings.
- A named FTP account confined to C:, with no anonymous account. Private
  credentials are kept on the card and in ignored local analyst storage;
  they must never enter the public repository or logs.
- NETUP.BAT for driver/DHCP and NETFTP.BAT for the foreground FTP server.

No boot files, motherboard/network settings, NIC EEPROM or boot ROM were
changed. Actual Ethernet initialization, DHCP and file transfer are **untested**.

## First physical check

After reinstalling the NIC and card, run:

```dos
C:\NET\3CCFG LIST
```

The EtherDisk manual documents LIST as adapter enumeration. Then run 3CCFG
without arguments to view its configuration menu. Record the I/O base, IRQ,
transceiver, boot-ROM address and size; exit without saving. Do not use AUTO
configuration. Resolve any IRQ5 conflict before enabling the packet driver.
Software interrupt60h is separate from the hardware IRQ.

After confirming the resource settings, connect RJ45 to the home LAN and run:

```dos
C:\NET\NETUP
```

Report the driver output and DHCP IP, then run:

```dos
C:\NET\NETFTP
```

Leave the FTP server running while the workstation transfers files. Alt-X
exits it before returning to PCPlus. If the driver is already loaded, run
`SET MTCPCFG=C:\NET\MTCP.CFG` and `C:\NET\DHCP` directly instead of loading
the driver twice. No resident TCP/IP stack or DOS startup change is needed.

The first workstation check should download a known file and compare its hash,
then upload a new temporary file and read it back for byte verification. For
subsequent updates, back up the current application, upload/verify new files,
and use checked renames; mTCP FTP does not overwrite existing files directly.
Preserve PRM, directory, key/translation files and the evolving PCPLUS.FON call
log. Full file access is available only while the foreground server runs.

## Sources and installation record

The [packet-driver project](https://github.com/hackerb9/3C509B-nestor) provides
the 8086-compatible driver and configuration utility. The copied tools are
pinned to commit `5f8c76a7fab61768cdc847e37f5d630796451089`. EtherDisk INSTRUCT.TXT,
PACKET.TXT, the configuration help and license accompany them on the card.
The existing [mTCP2020 manual](https://www.ibiblio.org/pub/micro/pc-stuff/freedos/files/net/mtcp/2020-03-07/mTCP_2020-03-07.pdf)
documents the password format, ten-character credential limits and server exit.

Private installation hashes/backups are in `build/network-bootstrap-01`.
The same operation installed the tested connection-alert/carrier candidate at
`C:\PCPLUS`; previous application files are in `C:\PCPLUS\APPBK02`.
The profile still matches `C:\UTILS\PCPLUS`, including sound enabled and
alert countdown5. The new call-log append was preserved, rather than replacing
its history with the older copy. Network transfer remains pending user-operated
hardware setup; no successful DHCP or FTP session is claimed here.
