; Owned startup-only full-parent PCCONN (shared owner kind5) loader diagnostic.
; Runs before UART startup and never enters the module. A successful run writes
; the 16-byte report, the allocated image after the first load, the image after
; a reload over a deliberately overwritten extent, then the final report.
; Every run ends with the final 16-byte report.
BITS 16
CPU 8086
SEGMENT CONNECTION_PROBE_CODE public align=16 class=FARCODE use16
GROUP CONNECTION_PROBE_GROUP CONNECTION_PROBE_CODE
extern _connection_overlay_load,_connection_overlay_release,_connection_overlay_phase
extern _connection_overlay_arena
extern _compiler_overlay_load,_compiler_overlay_release,_compiler_overlay_phase
extern process_psp
; magic 'CP', version, checks, failure, final phase, arena, image bytes, PSP
report: dw 0x5043,1,0,0,0,0,0,0
%macro expect 2
 inc word [cs:report+4]
 %1
 cmp ax,%2
 jne failed
%endmacro
global terminal_connection_overlay_probe
terminal_connection_overlay_probe:
 push ds
 push es
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 mov ax,[process_psp]
 mov [cs:report+14],ax
 expect {call far _connection_overlay_load},0
 ; The shared arena has one owner: duplicate and compiler loads refuse.
 expect {call far _connection_overlay_load},1
 expect {call far _compiler_overlay_load},1
 expect {call far _compiler_overlay_release},1
 expect {call far _compiler_overlay_phase},0xffff
 expect {call far _connection_overlay_phase},2
 inc word [cs:report+4]
 call far _connection_overlay_arena
 or ax,ax
 jz failed
 mov [cs:report+10],dx
 mov [cs:report+12],ax
 call write_report
 call dump
 expect {call far _connection_overlay_release},0
 expect {call far _connection_overlay_release},1
 expect {call far _connection_overlay_phase},0
 expect {call far _connection_overlay_arena},0
 ; Another owner may overwrite the released extent completely.
 mov es,[cs:report+10]
 xor di,di
 mov cx,[cs:report+12]
 mov al,0xa5
 cld
 rep stosb
 expect {call far _connection_overlay_load},0
 inc word [cs:report+4]
 call far _connection_overlay_arena
 cmp dx,[cs:report+10]
 jne failed
 call dump
 expect {call far _connection_overlay_release},0
 xor ax,ax
 jmp done
failed:
 mov [cs:report+6],ax
 or ax,ax
 jnz done
 mov word [cs:report+6],0xffff
done:
 ; The final report is always the last 16 bytes of output.
 call far _connection_overlay_phase
 mov [cs:report+8],ax
 call write_report
 mov ax,[cs:report+6]
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop es
 pop ds
 retf
write_report:
 push ds
 push cs
 pop ds
 mov bx,1
 mov cx,16
 mov dx,report
 mov ah,0x40
 int 0x21
 pop ds
 ret
dump:
 push ds
 mov ds,[cs:report+10]
 xor dx,dx
 mov cx,[cs:report+12]
 mov bx,1
 mov ah,0x40
 int 0x21
 pop ds
 ret
