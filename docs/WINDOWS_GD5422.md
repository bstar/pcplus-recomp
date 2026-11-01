# Windows 3.11 on the GD5422 machine

bstar requested the display driver matching this physical machine at640x480.
The card photo shows Cirrus Logic CL-GD5422. The previous active configuration
used standard VGA at640x480/16colors, alongside inactive settings accumulated
from Tseng, Video7 and newer Cirrus cards.

The model-specific Cirrus Logic GD5422/GD5424 release1.50 package was obtained
from the [archived driver package](https://www.vogonsdrivers.com/getfile.php?fileid=1083).
Its manufacturer OEM542X.INF explicitly defines av6256 as GD5422/GD5424 v1.50,
640x480x256. This differs from the already-present OEM542X.INF for GD5426/28;
the board-family name alone was insufficient to establish compatibility.

Installed configuration:

| Setting | Value |
| --- | --- |
| boot display.drv | 256_1024.drv |
| boot 386grabber | AVGA.3GR |
| boot 286grabber | VGACOLOR.2GR |
| 386Enh display | VDD54XX.386 |
| CLVGA videomode | 95 decimal, per the av6256 optional section |
| CLVGA dpi | 96 |
| drivers DCI | DCI5422 |

Matching display/VDD, grabbers, VGA fonts and DCI/UDH/DCIMAN/DVA components were
copied from the same package. Compressed SZDD members were expanded with exact
declared-length checks. Every installed file and the final SYSTEM.INI were
downloaded over FTP and compared byte for byte with the staged contents.
Old SYSTEM.INI and replaced files are backed up at C:\WINDOWS\WINBK01.
The private receipt, hashes, source archive and installer are in ignored
build/network-boot-01/windows-gd5422-install.json and adjacent files.

**Physical Windows startup and rendering remain untested.** Reboot into the
normal non-network configuration and run WIN to test resolution, colours and
mouse behavior. Existing mouse and sound configuration was not changed.
If the display fails, exit/reboot to DOS and run:

```dos
C:\NET\WINVGA.BAT
```

This restores the original VGA SYSTEM.INI, including its original VGA driver
and grabber selections. The standard VGA components remain installed.
