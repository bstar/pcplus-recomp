; C adapters around the exact native alert's RET2/RET4 service conventions.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_alarm_alert
extern _alarm_coop_seconds,_alarm_coop_peek,_alarm_coop_read
extern _alarm_coop_ticks,_alarm_coop_tone
global _alarm_coop_native,alarm_seconds,alarm_peek,alarm_read
global alarm_ticks,alarm_tone,alarm_option,alarm_operand
_alarm_coop_native: jmp aspect_alarm_alert
alarm_seconds: jmp _alarm_coop_seconds
alarm_peek: jmp _alarm_coop_peek
alarm_read: jmp _alarm_coop_read
%ifdef ASPECT_ALARM_VM
extern aspect_string_option_flag,aspect_console_pause_operand
alarm_option: jmp aspect_string_option_flag
alarm_operand: jmp aspect_console_pause_operand
%else
; The standalone component calls the alert, not the ASPECT operand wrapper.
alarm_option:
alarm_operand:
 xor ax,ax
 ret
%endif
alarm_ticks:
 push bp
 mov bp,sp
 push word [bp+4]
 call _alarm_coop_ticks
 add sp,2
 pop bp
 ret 2
alarm_tone:
 push bp
 mov bp,sp
 push word [bp+6]
 push word [bp+4]
 call _alarm_coop_tone
 add sp,4
 pop bp
 ret 4
GROUP DGROUP _DATA
SEGMENT _DATA public class=DATA use16
global alarm_duration,alarm_enabled
alarm_duration: dw 0
alarm_enabled: dw 0
