; Original PCPlus2.01 ALARM and shared connect-alert controller.
; Native baseline only: blocking tone/delay and direct keyboard/clock services.
; Not linked into the serviced interpreter or terminal.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_ALARM_FLAT
%if ASPECT_ALARM_UNIT=1
ORG 0xe660
%define aspect_alarm_alert 0x3616
%elif ASPECT_ALARM_UNIT=2
ORG 0x3616
%else
%error Select ASPECT_ALARM_UNIT1or2
%endif
%define alarm_duration 0x1d42
%define alarm_enabled 0x1d40
%define alarm_option 0xe0e4
%define alarm_operand 0xdd9c
%define alarm_seconds 0x3323
%define alarm_tone 0x7722
%define alarm_ticks 0x6b98
%define alarm_peek 0x651a
%define alarm_read 0x64fe
%else
%define ASPECT_ALARM_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_alarm_command,aspect_alarm_alert
extern alarm_duration,alarm_enabled,alarm_option,alarm_operand
extern alarm_seconds,alarm_tone,alarm_ticks,alarm_peek,alarm_read
%endif
%if ASPECT_ALARM_UNIT=0 || ASPECT_ALARM_UNIT=1
aspect_alarm_command:
 push si
 mov si,[alarm_duration]
 call alarm_option
 or_load ax,ax
 jz .alert
 call alarm_operand
 mov [alarm_duration],ax
.alert:
 call aspect_alarm_alert
 mov [alarm_duration],si
 pop si
 ret
%endif
%if ASPECT_ALARM_UNIT=0 || ASPECT_ALARM_UNIT=2
aspect_alarm_alert:
 push di
 push si
 mov si,[alarm_duration]
 call alarm_seconds
 mov_load di,ax
 jmp short .poll
.cycle:
 or_load si,si
 jz .finish
 cmp word [alarm_enabled],byte 0
 jz .clock
 mov ax,880
 push ax
 mov cx,15
 push cx
 call alarm_tone
 mov ax,1
 push ax
 call alarm_ticks
 mov ax,880
 push ax
 mov ax,15
 push ax
 call alarm_tone
 mov ax,6
 push ax
 call alarm_ticks
.clock:
 call alarm_seconds
 cmp_load ax,di
 jz .poll
 call alarm_seconds
 mov_load di,ax
 dec si
.poll:
 call alarm_peek
 or_load ax,ax
 jz .cycle
.finish:
 call alarm_peek
 or_load ax,ax
 jz .done
 call alarm_read
.done:
 pop si
 pop di
 ret
%endif
