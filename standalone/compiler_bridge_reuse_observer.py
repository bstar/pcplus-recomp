"""Owned two-interpreter compiler-error/reuse observer; no application code."""
import re
from compiler_bridge_recovery_observer import PREFIX

FIELDS=['stage','menu_ticks','first_jft_equal','first_owners_equal','first_history_equal',
 'first_compilers','first_psp','first_ds','prompt_seen','second_compiler_seen','second_psp','second_ds','second_extent']
WORDS=len(FIELDS)+7+6+len(PREFIX)

def attach(source, *, listing, parent, offsets):
 match=re.search(r'^([0-9a-f]+):([0-9a-f]+)\s+_compiler_lease_storage\b',listing,re.M);assert match
 segment,offset=(int(n,16) for n in match.groups())
 assert (segment*16+offset+28+15)//16+16<=parent['experimental_compiler_lease_module']['keep_paragraphs']
 storage='get_reuse_sample:\n'+''.join('get_reuse_'+n+': dw 0\n' for n in FIELDS)
 storage+='get_reuse_first_header: times 7 dw 0\nget_reuse_first_probe: times 6 dw 0\nget_reuse_second_kernel: times 14 dw 0\n'
 marker='get_recovery_sample:\n';assert source.count(marker)==1;source=source.replace(marker,storage+marker)
 marker='get_finish_tick:\n';assert source.count(marker)==1;source=source.replace(marker,marker+' call get_reuse_tick\n jc .done\n')
 marker='get_recovery_dos:\n save\n';assert source.count(marker)==1
 source=source.replace(marker,marker+' cmp word [cs:get_reuse_stage],0\n jne .no\n')
 marker=' inc word [cs:get_compiler_attempts]\n';assert source.count(marker)==1
 source=source.replace(marker,marker+' call get_reuse_compiler\n')
 body=ASM.replace('REUSE_KERNEL',str(segment)).replace('REUSE_STATE',str(offset)).replace('PROGRAM_ACTIVE',str(offsets['terminal_program_active'])).replace('REUSE_PENDING',str(offsets['terminal_program_pending']))
 marker='resident_end:\nstart:';assert source.count(marker)==1
 return source.replace(marker,body+'\n'+marker)

ASM=r'''
get_reuse_tick:
 call get_reuse_watch
 cmp word [cs:get_reuse_stage],0
 jne .menu
 cmp word [cs:exec_done],1
 jne .allow
 mov ax,[cs:parent_ds]
 or ax,ax
 jz .allow
 mov es,ax
 cmp word [es:PROGRAM_ACTIVE],0
 jne .allow
 cmp word [es:REUSE_PENDING],0
 jne .allow
 ; Record the completed first interpreter before rearming the passive observer.
 push cs
 pop ds
 push cs
 pop es
 mov si,sample
 mov di,get_reuse_first_header
 mov cx,7
 rep movsw
 mov si,get_child_ds
 mov di,get_reuse_first_probe
 mov cx,6
 rep movsw
 mov ax,[get_compiler_attempts]
 mov [get_reuse_first_compilers],ax
 mov ax,[parent_psp]
 mov [get_reuse_first_psp],ax
 mov ax,[parent_ds]
 mov [get_reuse_first_ds],ax
 mov si,before_jft
 mov di,after_jft
 mov cx,20
 call get_reuse_equal
 mov [get_reuse_first_jft_equal],ax
 mov si,before_owners
 mov di,after_owners
 mov cx,416
 call get_reuse_equal
 mov [get_reuse_first_owners_equal],ax
 mov si,exit_history
 mov di,after_history
 mov cx,72
 call get_reuse_equal
 mov [get_reuse_first_history_equal],ax
 ; The counters below belong to the fixture, not the product. The second real
 ; ASPECT EXEC must establish its own captures and compiler/child-exit counts.
 mov word [exec_seen],0
 mov word [exec_done],0
 mov word [child_exits],0
 mov word [exit_code],0xffff
 mov word [get_compiler_attempts],0
 mov word [get_input_injected],0
 mov word [get_finish_phase],0
 mov word [get_finish_ticks],0
 mov word [get_reuse_stage],1
 mov dx,0x6c00 ; Alt-F5 opens the current Script Files prompt.
 call get_finish_key
 jc .key_failed
 stc
 ret
.menu:
 cmp word [cs:get_reuse_stage],3
 jae .allow
 inc word [cs:get_reuse_menu_ticks]
 cmp word [cs:get_reuse_menu_ticks],6
 jb .hold
 mov word [cs:get_reuse_menu_ticks],0
 ; Require the actual rendered filename prompt before supplying any text.
 mov ax,0xb800
 mov es,ax
 mov di,1762*2
 mov si,get_reuse_prompt
 mov cx,20
.prompt:
 mov al,[es:di]
 cmp al,[cs:si]
 jne .hold
 inc si
 add di,2
 loop .prompt
 mov word [cs:get_reuse_prompt_seen],1
 push cs
 pop ds
 mov si,get_reuse_filename
 mov cx,9
.next_key:
 lodsw
 mov dx,ax
 call get_finish_key
 jc .key_failed
 loop .next_key
 mov word [cs:get_reuse_stage],3
.hold:
 stc
 ret
.key_failed:
 mov word [cs:get_reuse_stage],0xffff
 stc
 ret
.allow:
 clc
 ret
get_reuse_equal:
 repe cmpsb
 mov ax,0
 jne .return
 inc ax
.return:
 ret
get_reuse_compiler:
 save
 cmp word [cs:get_reuse_stage],3
 jne .done
 inc word [cs:get_reuse_second_compiler_seen]
 mov ax,[cs:parent_psp]
 mov [cs:get_reuse_second_psp],ax
 dec ax
 mov es,ax
 mov ax,[es:3]
 mov [cs:get_reuse_second_extent],ax
 mov ax,ss
 mov [cs:get_reuse_second_ds],ax
 mov ax,[cs:parent_psp]
 add ax,16+REUSE_KERNEL
 mov es,ax
 mov si,REUSE_STATE
 mov di,get_reuse_second_kernel
 mov cx,14
.copy:
 mov ax,[es:si]
 mov [cs:di],ax
 add si,2
 add di,2
 loop .copy
.done:
 restore
 ret
; Bounded diagnostics for fixture failures in a menu or parent prompt. Only
; fixture-owned sample bytes and VGA are read; no product/tail state mutation.
get_reuse_watch:
 save
 cmp word [cs:get_reuse_stage],0
 je .done
 inc word [cs:get_reuse_watch_ticks]
 cmp word [cs:get_reuse_watch_ticks],180
 jb .done
 cmp word [cs:get_reuse_watch_dumped],0
 jne .done
 les bx,[cs:get_watch_indos]
 cmp byte [es:bx],0
 jne .done
 mov word [cs:get_reuse_watch_dumped],1
 push cs
 pop ds
 mov dx,get_reuse_watch_name
 xor cx,cx
 mov ah,0x3c
 pushf
 call far [cs:old21]
 jc .done
 mov bx,ax
 mov dx,sample
 mov cx,sample_end-sample
 mov ah,0x40
 pushf
 call far [cs:old21]
 mov ax,0xb800
 mov ds,ax
 xor dx,dx
 mov cx,4000
 mov ah,0x40
 pushf
 call far [cs:old21]
 mov ah,0x3e
 pushf
 call far [cs:old21]
.done:
 restore
 ret
get_reuse_watch_ticks: dw 0
get_reuse_watch_dumped: dw 0
get_reuse_watch_name: db 'D:\REUSEW.BIN',0
get_reuse_prompt: db 'Script DOS 8.3 path: '
get_reuse_filename: dw 0x2267,0x186f,0x186f,0x2064,0x342e,0x1e61,0x1f73,0x1970,0x1c0d
'''
