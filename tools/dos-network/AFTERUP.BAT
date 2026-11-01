@ECHO OFF
SET ADPATH=C:\ADDOS
ECHO Loading After Dark with the saved Flying Toasters configuration.
C:
CD \ADDOS
C:\ADDOS\ADTSR.EXE > C:\NET\ADBOOT.LOG
TYPE C:\NET\ADBOOT.LOG
CD \
