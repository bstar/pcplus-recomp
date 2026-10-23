BITS 16
CPU 8086
SEGMENT NOTICEINPUT_CODE public align=16 class=FARCODE use16
extern notice_input_keyboard_bios_peek,notice_input_keyboard_bios_read
global _notice_input_bios_peek,_notice_input_bios_read
_notice_input_bios_peek:
 push bx
 push si
 push di
 push es
 call notice_input_keyboard_bios_peek
 jmp short done
_notice_input_bios_read:
 push bx
 push si
 push di
 push es
 call notice_input_keyboard_bios_read
done:
 pop es
 pop di
 pop si
 pop bx
 ret
