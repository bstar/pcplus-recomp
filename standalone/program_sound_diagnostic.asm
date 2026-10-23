; Actual DOS execution of exact native switches, tone and calibrated delay.
BITS 16
CPU 8086
GROUP DGROUP _DATA STACK
SEGMENT _TEXT public class=CODE use16
global sound_test
extern sound_error,sound_information,sound_tone,sound_on,sound_off
sound_test:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 in al,0x61
 mov [baseline],al
 and al,0xfc
 out 0x61,al
 mov word [sound_enabled],0
 call sound_error
 call sound_information
 call check_off
 mov word [sound_enabled],1
 call sound_error
 call check_off
 call sound_information
 call check_off
 mov ax,660
 push ax
 mov ax,1
 push ax
 mov [expected_sp],sp
 call sound_tone
 mov ax,[expected_sp]
 add ax,4
 cmp sp,ax
 jne failed
 call check_off
 call sound_on
 in al,0x61
 and al,3
 cmp al,3
 jne failed
 call sound_off
 call check_off
 mov al,[baseline]
 out 0x61,al
 mov dx,passed
 mov ah,9
 int 0x21
 mov ax,0x4c00
 int 0x21
check_off:
 in al,0x61
 test al,3
 jnz failed
 mov ah,[baseline]
 ; Bits4/5 are live hardware status, not stable output ownership.
 and ah,0x0c
 and al,0x0c
 cmp al,ah
 jne failed
 ret
failed:
 mov al,[baseline]
 out 0x61,al
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public class=DATA use16
global sound_enabled,sound_delay_floor,sound_delay_count
sound_enabled: dw 0
sound_delay_floor: dw 0
sound_delay_count: dw 100
expected_sp: dw 0
baseline: db 0
passed: db 'SOUND native DOS passed',13,10,'$'
SEGMENT STACK stack class=STACK use16
 resb 4096
stack_top:
