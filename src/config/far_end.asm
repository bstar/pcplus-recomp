; Link after all C CONFIG_CODE objects so the extent covers their code.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=1 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
global terminal_config_code_end
terminal_config_code_end:
