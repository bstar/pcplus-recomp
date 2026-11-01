# DOS Ethernet file updates

Hardware identified from bstar's photo: 3Com EtherLink III **3C509-TP**, with an
installed boot ROM used for XTIDE. Ethernet uses the RJ45 connector, not AUI.
The Boca modem already uses COM3/3E8h/IRQ5. Preserve those settings and the
NIC's existing boot-ROM enable, address and size.

## Dedicated management boot

Select **Network management (Ethernet / FTP)** in the DOS startup menu.
The default remains EM (Expanded memory + Mouse), with its ten-second timeout.
The management entry uses HIMEM and EMM386 NOEMS, branches before UNISOUND
initialization, loads CuteMouse on COM1/IRQ4 and skips the game shell.
`C:\NET\NETMGR.BAT` loads the packet driver,
runs DHCP, then starts the foreground FTP server only after successful DHCP.
Failures stop at the DOS prompt with the diagnostic visible.

The confirmed NIC settings remain **I/O300h, IRQ5, onboard TP/RJ45**, with
XTIDE ROM at **D8000h–DBFFFh**. No EEPROM or ROM settings were changed.
Software packet interrupt60h is separate from hardware IRQ5.
The Boca modem also uses IRQ5: **reboot before using PCPlus**. Closing FTP does
not unload the packet driver; this setup is for separate management sessions,
not simultaneous modem and Ethernet operation.

Connect RJ45 to the home LAN, boot the management entry, and report the DHCP
IP address. Leave the FTP server running for workstation updates. Use the
named account `bstar`; private credentials remain on the card and in ignored
local storage. No anonymous account is enabled. Alt-X exits the server.
DHCP supplies the IP address; no static LAN IP was assigned.
If DHCP fails after the driver loads, retry:

```dos
SET MTCPCFG=C:\NET\MTCP.CFG
C:\NET\DHCP
C:\NET\NETFTP
```

Do not load the packet driver twice. For a manual driver/DHCP start after a
fresh boot, `C:\NET\NETUP` remains available; observe the same reboot boundary.

`C:\NET` contains the 3C509 packet driver and configuration utility plus the
card's existing mTCP2020 DHCP, FTP server/client, Ping, packet utility and HTTP
client. `C:\UTILS\NET` is unchanged. MTCP.CFG uses hostname LOC386, MTU576,
packet interrupt60h and one FTP client. Boot files were backed up on the card
at `C:\NET\BOOTBK01` and locally in ignored `build/network-boot-01`.
The mouse addition has a separate startup backup at `C:\NET\NETMOUSE.BAK`.
To restore the previous boot menu and startup:

```dos
COPY C:\NET\BOOTBK01\CONFIG.SYS C:\CONFIG.SYS
COPY C:\NET\BOOTBK01\AUTOEXEC.BAT C:\AUTOEXEC.BAT
```

Installation checks verified DOS CRLF text, boot dispatch before sound
initialization, unchanged default selection and required files. **Physical
packet-driver initialization, DHCP and FTP transfer remain untested.**

The first workstation check should download a known file and compare its hash,
then upload a new temporary file and read it back for byte verification. For
subsequent updates, back up the current application, upload/verify new files,
and use checked renames; mTCP FTP does not overwrite existing files directly.
Preserve PRM, directory, key/translation files and the evolving PCPLUS.FON call
log. Full file access is available only while the foreground server runs.

## Mouse and upper memory

The network profile now uses `C:\NET\CTMOUSE.EXE` (CuteMouse 2.1 beta4),
loaded with `LH` and `/S14` to select COM1/IRQ4 explicitly. This replaces
only the network entry's mouse command; normal game boot entries and their
existing drivers remain unchanged. The previous network profile provided
HIMEM alone, so it did not create upper memory blocks for `LH`.

The added network-only line is:

```dos
DEVICE=C:\DOS\EMM386.EXE NOEMS X=D800-DBFF
```

The exclusion keeps the XTIDE ROM's D8000h–DBFFFh range outside EMM386's UMB
allocation. NIC EEPROM and ROM contents are unchanged. Startup saves mouse
messages to `C:\NET\MOUSE.LOG` and a `MEM /C` report to
`C:\NET\MEMBOOT.TXT`. Read these after the next boot to establish successful
mouse detection and actual high-memory placement; file read-back alone cannot
prove either. The prior manual driver worked, but the cause of its failed
boot-time detection was not established.

Pre-change CONFIG.SYS/AUTOEXEC.BAT are in `C:\NET\MOUSEBK`. The driver and
its license/documentation were copied from the
[FreeDOS archive](https://www.ibiblio.org/pub/micro/pc-stuff/freedos/files/dos/cutemouse/2.1beta4/ctm21b4.zip),
leaving the card's old CuteMouse 2.0 alpha4 at `C:\DRIVERS\CTMOUSE.EXE` intact.
Private source hashes, installation verification and original boot copies are
in `build/network-boot-01/cutemouse-install.json` and adjacent ignored files.
The driver documentation describes serial-port selection and the small
resident memory footprint; measured placement on this machine awaits reboot.

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
