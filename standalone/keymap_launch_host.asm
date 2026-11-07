; Authored DOS ABI diagnostic. All six external services are declared models.
BITS 16
CPU 8086
GROUP DGROUP PADSEG _DATA STACK
SEGMENT _TEXT public class=CODE use16
extern keymap_launch
..start:
 mov ax,DGROUP
 mov ds,ax
 mov es,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
.next:
 mov word [event_count],0
 mov bx,[case_index]
 mov ax,bx
 shl bx,1
 mov dx,[cs:profiles+bx]
 mov [keymap_profile],dx
 mov [reload_result],ax
 mov word [locate_result],0
 test ax,1
 jz .located
 mov word [locate_result],0x6200
.located:
 mov word [program_result],0
 test ax,2
 jz .programmed
 mov word [program_result],0xffff
.programmed:
 mov word [screen_low],0
 mov word [screen_high],0
 test ax,4
 jz .saved
 mov word [screen_low],0x2345
 mov word [screen_high],0x6789
.saved:
 mov bp,0xb0b0
 mov si,0x5151
 mov [saved_sp],sp
 call keymap_launch
 cmp ax,[reload_result]
 jne failed
 cmp sp,[saved_sp]
 jne failed
 cmp bp,0xb0b0
 jne failed
 cmp si,0x5151
 jne failed
 cmp word [event_count],6
 jne failed
 inc word [case_index]
 cmp word [case_index],8
 jb .next
 mov dx,passed
 mov ah,9
 int 0x21
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
; AL is the required next event; no model uses BP/SI/DI.
event:
 xor ah,ah
 cmp ax,[event_count]
 jne failed
 inc word [event_count]
 ret
global keymap_format,keymap_save_screen,keymap_locate,keymap_program,keymap_restore_screen,keymap_reload
keymap_format:
 push bp
 mov bp,sp
 mov al,0
 call event
 cmp word [bp+4],keymap_tail
 jne failed
 cmp word [bp+6],keymap_format_text
 jne failed
 mov ax,[keymap_profile]
 cmp [bp+8],ax
 jne failed
 cmp word [bp+10],keymap_filename
 jne failed
 mov word [keymap_tail],0x4154
 mov word [keymap_tail+2],0x4c49
 mov byte [keymap_tail+4],0
 pop bp
 ret
keymap_save_screen:
 mov al,1
 call event
 mov ax,[screen_low]
 mov dx,[screen_high]
 ret
keymap_locate:
 push bp
 mov bp,sp
 mov al,2
 call event
 cmp word [bp+4],keymap_program_name
 jne failed
 cmp word [bp+6],keymap_tail
 jne failed
 cmp word [bp+8],0
 jne failed
 cmp word [bp+10],0
 jne failed
 cmp word [bp+12],0
 jne failed
 mov ax,[locate_result]
 pop bp
 ret
keymap_program:
 push bp
 mov bp,sp
 mov al,3
 call event
 mov ax,[locate_result]
 cmp [bp+4],ax
 jne failed
 cmp word [bp+6],keymap_tail
 jne failed
 cmp word [bp+8],0
 jne failed
 cmp word [bp+10],0
 jne failed
 cmp word [bp+12],0
 jne failed
 mov ax,[program_result]
 pop bp
 ret
keymap_restore_screen:
 push bp
 mov bp,sp
 mov al,4
 call event
 mov ax,[screen_low]
 cmp [bp+4],ax
 jne failed
 mov ax,[screen_high]
 cmp [bp+6],ax
 jne failed
 pop bp
 ret 4
keymap_reload:
 mov al,5
 call event
 mov ax,[reload_result]
 ret
profiles: dw 0,4,6,32,0xffff,1,7,31
SEGMENT PADSEG public align=16 class=DATA use16
 times 128 db 0xa5
SEGMENT _DATA public class=DATA use16
global keymap_profile,keymap_filename,keymap_tail,keymap_format_text,keymap_program_name
keymap_profile: dw 0
keymap_filename: db 'SYNTH.KBD',0
keymap_format_text: db '%d %s',0
keymap_program_name: db 'PCKEYMAP.EXE',0
keymap_tail: times 128 db 0
event_count: dw 0
case_index: dw 0
locate_result: dw 0
program_result: dw 0
screen_low: dw 0
screen_high: dw 0
reload_result: dw 0
saved_sp: dw 0
passed: db 'PASS KEYMAP LAUNCH 8 ABI CASES',13,10,'$'
SEGMENT STACK stack align=16 class=STACK use16
 resb 2048
stack_top:
