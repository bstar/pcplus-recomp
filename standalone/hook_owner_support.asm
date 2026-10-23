BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern __STACKTOP,__curbrk,process_psp,process_minimum_paragraphs,process_keep_paragraphs
extern process_memory_released,process_busy
global _hook_diag_initialize
_hook_diag_initialize:
 push bx
 push si
 push es
 mov ah,0x51
 int 0x21
 mov [process_psp],bx
 mov si,bx
 mov ax,ss
 mov bx,[__STACKTOP]
 cmp bx,[__curbrk]
 jae .near_end
 mov bx,[__curbrk]
.near_end:
 add bx,15
 mov cl,4
 shr bx,cl
 add ax,bx
 mov dx,seg hook_diagnostic_end
 mov bx,hook_diagnostic_end
 add bx,15
 shr bx,cl
 add dx,bx
 cmp ax,dx
 jae .maximum
 mov ax,dx
.maximum:
 sub ax,si
 mov [process_keep_paragraphs],ax
 mov [process_minimum_paragraphs],ax
 mov word [process_memory_released],0
 mov word [process_busy],0
 pop es
 pop si
 pop bx
 ret
extern _hook_owner_close
global _hook_diag_context
_hook_diag_context:
 push bp
 mov bp,sp
 pushf
 push ds
 push es
 push bx
 push si
 push di
 mov bx,[bp+4]
 cmp bx,1
 jne .direction
 cli
 jmp short .call
.direction:
 cmp bx,2
 jne .segment
 std
 jmp short .call
.segment:
 mov ax,0x1234
 mov ds,ax
.call:
 mov ax,seg _hook_diagnostic_state
 push ax
 mov ax,_hook_diagnostic_state
 push ax
 call far _hook_owner_close
 add sp,4
 pop di
 pop si
 pop bx
 pop es
 pop ds
 popf
 pop bp
 ret
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
global _hook_diagnostic_state
_hook_diagnostic_state: times 84 db 0
hook_diagnostic_end:
