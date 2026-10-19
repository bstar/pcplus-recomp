; Owned snapshots/resources for native status drawing. Live callers must stage
; dynamic state before drawing. Compact defaults also serve the DOS diagnostic.
BITS 16
CPU 8086
SEGMENT _DATA public class=DATA use16
%macro status_word 2
 global %1
%1: dw %2
%endmacro
status_word program_state_7a72,80
status_word reset_status_hidden,0
status_word meta_local_echo,0
status_word meta_script_active,1
status_word keyboard_state_373c,0
status_word reset_data_399a,0
status_word reset_data_3732,0
status_word reset_data_1f6c,0x1f
status_word reset_data_332c,0
status_word reset_data_1b8a,1
status_word reset_data_1b8c,8
status_word reset_data_1b88,0
status_word reset_data_1b86,6
status_word reset_data_7a7c,4000
status_word status_error,0
status_word status_carrier,0
status_word reset_data_42b6,status_help
status_word reset_data_42b4,status_recording
status_word reset_data_42b2,status_monitor
status_word reset_data_46ce,status_parity
status_word reset_data_46d0,status_normal_format
global reset_data_299c,reset_data_29de
reset_data_299c: dw status_emulation_0,status_emulation_1,status_emulation_2,status_emulation_3,status_emulation_4,status_emulation_5,status_emulation_6,status_emulation_7,status_emulation_8,status_emulation_9,status_emulation_10,status_emulation_11,status_emulation_12,status_emulation_13,status_emulation_14
reset_data_29de: dw status_baud_0,status_baud_1,status_baud_2,status_baud_3,status_baud_4,status_baud_5,status_baud_6,status_baud_7,status_baud_8
global reset_data_46d2
reset_data_46d2: db 37,45,49,48,46,49,48,115,37,45,49,48,46,49,48,115,37,45,49,48,46,49,48,115,37,45,49,48,46,49,48,115,37,45,49,48,46,49,48,115,37,45,49,48,46,49,48,115,37,45,49,48,46,49,48,115,37,45,49,48,46,49,48,115,0
status_normal_format: db 32,37,45,49,52,46,49,52,115,179,32,37,45,56,46,56,115,32,179,32,37,99,68,88,32,179,37,54,115,32,37,99,37,100,37,100,32,179,32,76,79,71,32,37,45,55,46,55,115,179,32,80,82,73,78,84,32,79,37,45,50,46,50,115,32,179,32,37,45,56,46,56,115,32,32,0
status_parity: db 'NOEMS',0
status_emulation_0: db 'TTY',0
status_emulation_1: db 'VT52',0
status_emulation_2: db 'VT100',0
status_emulation_3: db 'VT102',0
status_emulation_4: db 'VT220',0
status_emulation_5: db 'VT320',0
status_emulation_6: db 'ANSI',0
status_emulation_7: db 'IBM PC',0
status_emulation_8: db 'WYSE 75',0
status_emulation_9: db 'ATT 605',0
status_emulation_10: db 'ATT 4410',0
status_emulation_11: db 'TVI 922',0
status_emulation_12: db 'HEATH 19',0
status_emulation_13: db 'IBM 3101',0
status_emulation_14: db 'IBM 3161',0
status_baud_0: db '300',0
status_baud_1: db '1200',0
status_baud_2: db '2400',0
status_baud_3: db '4800',0
status_baud_4: db '9600',0
status_baud_5: db '19200',0
status_baud_6: db '38400',0
status_baud_7: db '57600',0
status_baud_8: db '115200',0
global status_help
status_help: db 'Alt-Z FOR HELP',0
global status_recording
status_recording: db 'RECORDING...',0
global status_monitor
status_monitor: db 'MONITOR MODE',0
global reset_data_cc9e
reset_data_cc9e: db 'Esc:EXIT',0
global reset_data_432e
reset_data_432e: db 'OPEN   ',0
global reset_data_4336
reset_data_4336: db 'ON HOLD',0
global reset_data_433e
reset_data_433e: db 'CLOSED ',0
global reset_data_4324
reset_data_4324: db 'MONITOR',0
global reset_data_4346
reset_data_4346: db 'ON-LINE ',0
global reset_data_4350
reset_data_4350: db 'OFF-LINE',0
global reset_data_46c1
reset_data_46c1: db 'N ',0
global reset_data_46c4
reset_data_46c4: db 'FF',0
global terminal_reset_script_label
terminal_reset_script_label: db 'TEST.ASX',0
 times 6 db 0
global reset_scratch
reset_scratch: times 11 db 0
global reset_data_cc53
reset_data_cc53: times 11 db 0
global reset_data_cc5c
reset_data_cc5c: times 11 db 0
global reset_data_cc65
reset_data_cc65: times 11 db 0
global reset_data_cc6e
reset_data_cc6e: times 11 db 0
global reset_data_cc77
reset_data_cc77: times 11 db 0
global reset_data_cc80
reset_data_cc80: times 11 db 0
global reset_data_cc89
reset_data_cc89: times 11 db 0
