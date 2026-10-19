; Source-owned isolated 8086 cross-EXEC stack-switch experiment.
; No product ASIO publication or native PCPlus recovery claim. Parent CS=DS
; owns one 1024-byte stack slice, bounded by two32-byte redzones. Service code
; deliberately makes DOS62, BIOS1A, INT60 and a far child callback; arbitrary
; renderer call depth, DOS reentrancy and asynchronous aborts are not proved.
; Far ABI AX request/BX value, return AX=3456; all other registers and FLAGS
; survive. FFFE rejects depth1 before mutating saved owner stack/FLAGS.
BITS 16
CPU 8086
%include "resident_service.inc"
resident_service_entry:
 RS_SAVE_FRAME
 mov bp,sp
 cli
 mov ax,[cs:resident_service_parent_ds]
 mov es,ax
 cmp word [es:resident_service_descriptor+RS_BUSY],0
 jne .refuse
 inc word [es:resident_service_descriptor+RS_BUSY]
 mov ax,ss
 mov [es:resident_service_descriptor+RS_SAVED_SS],ax
 mov [es:resident_service_descriptor+RS_SAVED_SP],sp
 mov ax,[ss:bp+RS_FRAME_FLAGS]
 mov [es:resident_service_descriptor+RS_FLAGS],ax
 mov ax,es
 mov ss,ax
 mov sp,resident_service_stack_top
 mov ds,ax
 mov ax,[resident_service_descriptor+RS_FLAGS]
 and ax,0xfbff ;Body DF=0; caller DF still restored from original frame.
 push ax
 popf
 inc word [resident_service_descriptor+RS_CALLS]
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne .bad
 cmp ax,[resident_service_descriptor+RS_PARENT_DS]
 jne .bad
 inc word [resident_service_descriptor+RS_PARENT_CHECKS]
.bad:
 mov ah,0x62
 int 0x21
 mov [resident_service_descriptor+RS_LAST_PSP],bx
 cmp bx,[resident_service_descriptor+RS_CHILD_PSP]
 je .psp_ok
 inc word [resident_service_descriptor+RS_FAILURES]
.psp_ok:
 ; Deterministic child interrupt while DS=SS=parent. It must save/restore DS.
 int 0x60
 xor ax,ax ;Controlled child UART status callback op0, BX=LSR port.
 mov bx,0x3fd
 call far [resident_service_descriptor+RS_CALLBACK]
 and ax,0x60
 cmp ax,0x60
 je .callback_ok
 inc word [resident_service_descriptor+RS_FAILURES]
.callback_ok:
 ; Real timer proof only when the caller entered IF=1. No STI for IF=0.
 test word [resident_service_descriptor+RS_FLAGS],0x200
 jz .no_wait
 xor ax,ax
 int 0x1a
 mov si,dx
.wait_tick:
 xor ax,ax
 int 0x1a
 cmp dx,si
 je .wait_tick
.no_wait:
 int 0x60
 mov [resident_service_descriptor+RS_LOW_SP],sp
 cli
 dec word [resident_service_descriptor+RS_BUSY]
 mov ax,[resident_service_descriptor+RS_SAVED_SS]
 mov dx,[resident_service_descriptor+RS_SAVED_SP]
 mov ss,ax
 mov sp,dx
 mov ds,ax
 mov bp,sp
 mov word [ss:bp+RS_FRAME_AX],0x3456
 RS_RESTORE_FRAME
.refuse:
 inc word [es:resident_service_descriptor+RS_REFUSED]
 mov word [ss:bp+RS_FRAME_AX],0xfffe
 RS_RESTORE_FRAME
resident_service_parent_ds: dw 0
resident_service_descriptor: times RS_DESCRIPTOR_BYTES db 0
resident_service_stack_low: times 32 db 0xa6
resident_service_stack: times RS_STACK_BYTES db 0xcc
resident_service_stack_top:
resident_service_stack_high: times 32 db 0x5a
