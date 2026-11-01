@ECHO OFF
ECHO LoSs oF CoNtRoL - Network management
ECHO 3Com EtherLink III: existing adapter settings, 300h / IRQ5.
SET MTCPCFG=C:\NET\MTCP.CFG
C:\NET\3C509.COM 0x60
IF ERRORLEVEL 1 GOTO DRIVER
C:\NET\DHCP.EXE
IF ERRORLEVEL 1 GOTO DHCPERR
REM After Dark disabled after physical crash during activation.
C:\DOS\MEM.EXE /C > C:\NET\MEMNET.TXT
ECHO Note the assigned IP address for workstation file updates.
ECHO Starting FTP. Account: bstar. Alt-X exits the server.
C:\NET\FTPSRV.EXE
GOTO END
:DRIVER
ECHO Packet driver failed. Read its message above.
GOTO END
:DHCPERR
ECHO DHCP failed. Check the Ethernet cable and switch link.
ECHO To retry: C:\NET\DHCP then C:\NET\NETFTP
:END
ECHO Reboot before using PCPlus: Ethernet and modem share IRQ5.
