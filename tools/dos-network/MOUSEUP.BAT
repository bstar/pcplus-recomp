@ECHO OFF
ECHO Loading MMOUSE using the saved machine-profile command.
LH C:\DRIVERS\MMOUSE\MMOUSE.COM /A6 > C:\NET\MOUSE.LOG
TYPE C:\NET\MOUSE.LOG
