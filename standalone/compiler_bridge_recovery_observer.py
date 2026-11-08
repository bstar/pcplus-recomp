"""Owned DOS fault fixture; never linked into the application.

Inject precisely scoped preparation, restoration or cleanup failures. Observe
BIOS quarantine/retry only for invalid memory; inspect retained/child state
while the parent tail is invalid. INT21 frame offsets follow the observer's save macro.
"""
import re

KINDS={'grow':1,'read':2,'unlink':3,'create':4,'write':5,'short-write':6,'begin-close':7,'close':8}

FIELDS = ['kind','injected','prompt_seen','hold_ticks','retry_key','retry_calls',
 'parent_resize_calls','backup_create_calls','backup_write_calls','backup_position_lo','backup_position_hi',
 'close_calls','closed_handle','close_probe_error','retired_phase','retired_dos_error','retired_busy','retired_handle',
 'captured_cells','display_checked','display_cells','display_cursor_ok','display_shape_ok','display_valid',
 'unsafe','parent_extent','child_ds','paused','scope','serial','steps','current_psp','program_active']
PREFIX = ['cookie','parent','keep','full','owner','token','phase','handle','crc',
 'dos_error','created','valid','sequence','busy']
WORDS = len(FIELDS)+len(PREFIX)

def attach(source, *, kind, parent, listing, offsets, child_symbols, child_group):
 assert kind in KINDS
 kernel=parent['experimental_compiler_lease_module']
 match=re.search(r'^([0-9a-f]+):([0-9a-f]+)\s+_compiler_lease_storage\b',listing,re.M)
 assert match
 assert kernel['arena_offset']>=8006
 frame=re.search(r'^([0-9a-f]+):([0-9a-f]+)\s+redisplay_snapshot\b',listing,re.M);assert frame
 frame_segment,frame_offset=(int(n,16) for n in frame.groups())
 assert frame_offset+8006<=65536
 segment,offset=(int(n,16) for n in match.groups())
 keep=kernel['keep_paragraphs'];full=parent['memory_layout']['retained_parent_paragraphs']
 assert (segment*16+offset+28+15)//16+16<=keep<full
 prefix='get_recovery_sample:\n'+''.join('get_recovery_'+name+': dw '+str(KINDS[kind] if name=='kind' else 0)+'\n' for name in FIELDS)+'get_recovery_prefix: times 14 dw 0\n'
 marker='get_compiler_largest: dw 0';assert source.count(marker)==1
 source=source.replace(marker,prefix+marker)
 marker=' mov bp,sp\n cmp byte [ss:bp+17],0x4b';assert source.count(marker)==1
 source=source.replace(marker,''' mov bp,sp
 call get_recovery_dos
 jnc .recovery_chain
 restore
 iret
.recovery_chain:
 cmp byte [ss:bp+17],0x4b''')
 marker='timer:\n save\n cld';assert source.count(marker)==1
 source=source.replace(marker,marker+'\n call get_recovery_tick')
 constants=dict(RECOVERY_KIND=KINDS[kind],RECOVERY_KEEP=keep,RECOVERY_FULL=full,
  RECOVERY_MODULE=kernel['relative_target_segment'],RECOVERY_END=kernel['relative_target_segment']+(kernel['bank_bytes']+15)//16,
  RECOVERY_KERNEL=segment,RECOVERY_STATE=offset,RECOVERY_CHILD_GROUP=child_group,
  RECOVERY_SCREEN=frame_segment,RECOVERY_FRAME=frame_offset,RECOVERY_FRAME_META=frame_offset+8000,
  RECOVERY_PAUSE=child_symbols['_aspect_serial_compile_pause_owned'],
  RECOVERY_SCOPE=child_symbols['_runtime_compiler_scope_state'],RECOVERY_SERIAL=child_symbols['_aspect_serial_active'],
  RECOVERY_STEPS=child_symbols['_runtime_steps'],RECOVERY_ACTIVE=offsets['terminal_program_active'])
 body='\n'.join('%define '+name+' '+str(value) for name,value in constants.items())+'\n'+ASM
 marker='resident_end:\nstart:';assert source.count(marker)==1
 return source.replace(marker,body+'\n'+marker)

ASM=r'''
get_recovery_dos:
 save
 call get_recovery_display
 cmp word [cs:exec_seen],1
 jne .no
 cmp word [cs:exec_done],0
 jne .no
%if RECOVERY_KIND >= 4 && RECOVERY_KIND != 8
 cmp word [cs:get_compiler_attempts],0
%else
 cmp word [cs:get_compiler_attempts],1
%endif
 jne .no
 ; Authenticate the interrupted caller CS as the loaded kernel, not compiler.
 mov ax,[cs:parent_psp]
 add ax,16
 mov di,ax
 add ax,RECOVERY_MODULE
 cmp [ss:bp+22],ax
 jb .no
 mov ax,di
 add ax,RECOVERY_END
 cmp [ss:bp+22],ax
 jae .no
 cmp byte [ss:bp+17],0x4a
 jne .not_resize
 mov ax,[cs:parent_psp]
 cmp [ss:bp],ax
 jne .not_resize
 inc word [cs:get_recovery_parent_resize_calls]
.not_resize:
%if RECOVERY_KIND == 1
 cmp byte [ss:bp+17],0x4a
 jne .no
 mov ax,[cs:parent_psp]
 cmp [ss:bp],ax ; ES saved by outer observer frame.
 jne .no
 cmp word [ss:bp+14],RECOVERY_FULL
 jne .no
%elif RECOVERY_KIND == 2
 cmp byte [ss:bp+17],0x3f
 jne .no
 mov ax,[cs:parent_psp]
 add ax,RECOVERY_KEEP
 cmp [ss:bp+2],ax ; DS:DX first restoration buffer, never compiler input.
 jne .no
 cmp word [ss:bp+10],0
 jne .no
 cmp word [ss:bp+12],4096
 jne .no
%elif RECOVERY_KIND == 3 || RECOVERY_KIND == 8
 mov ax,[cs:parent_psp]
 add ax,16+RECOVERY_KERNEL
 mov es,ax
 cmp word [es:RECOVERY_STATE+12],4
 jne .no
 cmp word [es:RECOVERY_STATE+22],1
 jne .no
 cmp byte [ss:bp+17],0x3e
 jne .unlink
 mov ax,[es:RECOVERY_STATE+14]
 cmp ax,0xffff
 je .no
 cmp [ss:bp+14],ax
 jne .no
 mov [cs:get_recovery_closed_handle],ax
%if RECOVERY_KIND == 8
 jmp .close_matched
%else
 inc word [cs:get_recovery_close_calls]
 jmp .no ; Unlink fixture passes actual close through to DOS.
%endif
.unlink:
 cmp byte [ss:bp+17],0x41
 jne .no
 mov ax,es
 cmp [ss:bp+2],ax
 jne .no
 cmp word [ss:bp+10],RECOVERY_STATE+156 ; compact state's absolute name
 jne .no
 cmp word [es:RECOVERY_STATE+14],0xffff
 jne .no
%else
 mov ax,[cs:parent_psp]
 add ax,16+RECOVERY_KERNEL
 mov es,ax
 cmp word [es:RECOVERY_STATE+12],1
 jne .no
 cmp word [es:RECOVERY_STATE+22],1
 jne .no
 cmp word [es:RECOVERY_STATE+26],1
 jne .no
%if RECOVERY_KIND == 4
 cmp word [ss:bp+16],0x6c00
 jne .no
 mov ax,es
 cmp [ss:bp+2],ax
 jne .no
 cmp word [ss:bp+8],RECOVERY_STATE+156 ; DS:SI exclusive-create name
 jne .no
 inc word [cs:get_recovery_backup_create_calls]
%elif RECOVERY_KIND == 7
 cmp byte [ss:bp+17],0x3e
 jne .no
 mov ax,[es:RECOVERY_STATE+14]
 cmp ax,0xffff
 je .no
 cmp [ss:bp+14],ax
 jne .no
%else
 cmp byte [ss:bp+17],0x40
 jne .no
 mov ax,[es:RECOVERY_STATE+14]
 cmp ax,0xffff
 je .no
 cmp [ss:bp+14],ax
 jne .no
 cmp word [ss:bp+10],0
 jne .no
 cmp word [ss:bp+12],4096
 jne .no
 mov ax,[cs:parent_psp]
 add ax,RECOVERY_KEEP
 cmp word [cs:get_recovery_backup_write_calls],0
 je .first_write
 add ax,256
 cmp [ss:bp+2],ax
 jne .no
 inc word [cs:get_recovery_backup_write_calls]
 jmp .write_match
.first_write:
 cmp [ss:bp+2],ax
 jne .no
 inc word [cs:get_recovery_backup_write_calls]
 jmp .no ; First4096 bytes must be written by actual DOS.
.write_match:
%endif
%endif
.close_matched:
 mov ax,[cs:parent_psp]
 dec ax
 mov es,ax
%if RECOVERY_KIND == 1
 cmp word [es:3],RECOVERY_KEEP
%else
 cmp word [es:3],RECOVERY_FULL
%endif
 jne .no
 cmp word [cs:get_recovery_injected],0
 je .fail
 cmp word [cs:get_recovery_retry_key],1
 je .retry
 mov word [cs:get_recovery_unsafe],1
 jmp .no
.retry:
 inc word [cs:get_recovery_retry_calls]
 jmp .no
.fail:
%if RECOVERY_KIND >= 3
%if RECOVERY_KIND == 3
 ; Duplicating the previously closed child JFT entry must fail with DOS6.
 mov bx,[cs:get_recovery_closed_handle]
 mov ah,0x45
 pushf
 call far [cs:old21]
 jc .closed
 mov bx,ax
 mov ah,0x3e
 pushf
 call far [cs:old21] ; retire only our unexpected duplicate, never original
 xor ax,ax
.closed:
 mov [cs:get_recovery_close_probe_error],ax
%elif RECOVERY_KIND == 7 || RECOVERY_KIND == 8
 ; Close the real owned backup first, then report an error to the caller.
 ; DOS is permitted to have closed a handle despite returning a close error.
 mov bx,[ss:bp+14]
 mov [cs:get_recovery_closed_handle],bx
 xor cx,cx
 xor dx,dx
 mov ax,0x4201
 pushf
 call far [cs:old21]
 jc .close_position_failed
 mov [cs:get_recovery_backup_position_lo],ax
 mov [cs:get_recovery_backup_position_hi],dx
.close_position_failed:
 mov bx,[cs:get_recovery_closed_handle]
 mov ah,0x3e
 pushf
 call far [cs:old21]
 jnc .real_closed
 mov word [cs:get_recovery_unsafe],1
.real_closed:
 inc word [cs:get_recovery_close_calls]
 mov bx,[cs:get_recovery_closed_handle]
 mov ah,0x45
 pushf
 call far [cs:old21]
 jc .close_probed
 mov bx,ax
 mov ah,0x3e
 pushf
 call far [cs:old21]
 xor ax,ax
.close_probed:
 mov [cs:get_recovery_close_probe_error],ax
%elif RECOVERY_KIND >= 5
 mov bx,[ss:bp+14]
 xor cx,cx
 xor dx,dx
 mov ax,0x4201 ; Current-position query: no seek or file mutation.
 pushf
 call far [cs:old21]
 jc .position_failed
 mov [cs:get_recovery_backup_position_lo],ax
 mov [cs:get_recovery_backup_position_hi],dx
.position_failed:
%endif
 mov ax,[cs:parent_psp]
 add ax,16+RECOVERY_KERNEL
 mov es,ax
 mov si,RECOVERY_STATE
 mov di,get_recovery_prefix
 mov cx,14
.cleanup_prefix:
 mov ax,[es:si]
 mov [cs:di],ax
 add si,2
 add di,2
 loop .cleanup_prefix
 mov ax,[es:RECOVERY_STATE+8]
 add ax,16+RECOVERY_CHILD_GROUP
 mov [cs:get_recovery_child_ds],ax
 mov es,ax
 mov ax,[es:RECOVERY_PAUSE]
 mov [cs:get_recovery_paused],ax
 mov ax,[es:RECOVERY_SCOPE]
 mov [cs:get_recovery_scope],ax
 mov ax,[es:RECOVERY_SERIAL]
 mov [cs:get_recovery_serial],ax
 mov ah,0x51
 pushf
 call far [cs:old21]
 mov [cs:get_recovery_current_psp],bx
 mov ax,[cs:parent_ds]
 mov es,ax
 mov ax,[es:RECOVERY_ACTIVE]
 mov [cs:get_recovery_program_active],ax
 mov ax,[cs:parent_psp]
 dec ax
 mov es,ax
 mov ax,[es:3]
 mov [cs:get_recovery_parent_extent],ax
%endif
 call get_recovery_cells
 mov [cs:get_recovery_captured_cells],ax
 mov word [cs:get_recovery_injected],1
%if RECOVERY_KIND < 3
 ; Remove only this owned fixture's early return-prompt key. No user keyboard.
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x1c]
 mov [es:0x1a],ax
%endif
%if RECOVERY_KIND == 6
 mov word [ss:bp+16],4095 ; Synthetic short count, no second write performed.
 and word [ss:bp+24],0xfffe
%else
%if RECOVERY_KIND == 1
 mov word [ss:bp+16],8
%else
 mov word [ss:bp+16],5
%endif
 or word [ss:bp+24],1
%endif ; CF in original INT21 IRET frame, not saved PUSHF.
 restore
 stc
 ret
.no:
 restore
 clc
 ret

; Scope0 restores INT0 after the bridge completes, before serial resume/rendering.
; At that boundary compare EVERY captured character/attribute and BIOS cursor.
get_recovery_display:
 save
 cmp word [cs:exec_done],0
 jne .done
 cmp word [cs:get_recovery_injected],1
 jne .done
%if RECOVERY_KIND < 3
 cmp word [cs:get_recovery_retry_key],1
 jne .done
%endif
 cmp word [cs:get_recovery_display_checked],0
 jne .done
 cmp word [ss:bp+16],0x2500
 jne .done
 ; SETVECT temporarily uses the ISR code segment as DS; authenticate SS/PSP.
 mov ax,ss
 sub ax,RECOVERY_CHILD_GROUP+16
 mov es,ax
 cmp word [es:0],0x20cd
 jne .done
 mov ax,[cs:parent_psp]
 cmp [es:0x16],ax
 jne .done
 mov ax,ss
 mov es,ax
 cmp word [es:RECOVERY_SCOPE],1
 jne .done
 cmp word [es:RECOVERY_PAUSE],1
 jne .done
 mov word [cs:get_recovery_display_checked],1
 mov ax,[cs:parent_psp]
 add ax,16+RECOVERY_KERNEL
 mov es,ax
 cmp word [es:RECOVERY_STATE+22],1
 jne .done
 mov word [cs:get_recovery_display_valid],1
 mov ax,[es:RECOVERY_STATE+12]
 mov [cs:get_recovery_retired_phase],ax
 mov ax,[es:RECOVERY_STATE+18]
 mov [cs:get_recovery_retired_dos_error],ax
 mov ax,[es:RECOVERY_STATE+26]
 mov [cs:get_recovery_retired_busy],ax
 mov ax,[es:RECOVERY_STATE+14]
 mov [cs:get_recovery_retired_handle],ax
 call get_recovery_cells
 mov [cs:get_recovery_display_cells],ax
 cmp ax,2000
 jne .done
 mov ah,3
 xor bh,bh
 int 0x10
 mov ax,[cs:parent_psp]
 add ax,16+RECOVERY_SCREEN
 mov es,ax
 cmp dx,[es:RECOVERY_FRAME_META+4]
 jne .shape
 mov word [cs:get_recovery_display_cursor_ok],1
.shape:
 cmp cx,[es:RECOVERY_FRAME_META+2]
 jne .done
 mov word [cs:get_recovery_display_shape_ok],1
.done:
 restore
 ret

; Compare the independently observed physical frame before failure and after
; repair against the retained capture. AX=count matched; never read lent tail.
get_recovery_cells:
 mov ax,[cs:parent_psp]
 add ax,16+RECOVERY_SCREEN
 mov es,ax
 xor bx,bx
 mov cx,[es:RECOVERY_FRAME_META]
 cmp cx,2000
 jne .done
 mov di,RECOVERY_FRAME
 mov ax,0xb800
 mov ds,ax
 xor si,si
.cells:
 mov ax,[si]
 cmp ax,[es:di]
 jne .done
 inc bx
 add si,2
 add di,2
 loop .cells
.done:
 mov ax,bx
 ret

get_recovery_tick:
%if RECOVERY_KIND >= 3
 ret ; Valid-memory preparation/cleanup failure must not enter quarantine.
%endif
 save
 cmp word [cs:get_recovery_injected],1
 jne .done
 cmp word [cs:get_recovery_retry_key],0
 jne .done
 cmp word [cs:exec_done],0
 je .live
 mov word [cs:get_recovery_unsafe],1
 jmp .done
.live:
 mov ax,ss
 sub ax,RECOVERY_CHILD_GROUP+16
 mov es,ax
 cmp word [es:0],0x20cd
 jne .done
 mov ax,[cs:parent_psp]
 cmp [es:0x16],ax
 jne .done
 les bx,[cs:get_watch_indos]
 cmp byte [es:bx],0
 jne .done
 ; Require the actual BIOS-only recovery notice, not merely lack of progress.
 mov ax,0xb800
 mov es,ax
 xor bx,bx
.scan:
 mov di,bx
 mov si,get_recovery_notice
 mov cx,32
.compare:
 mov al,[es:di]
 cmp al,[cs:si]
 jne .next
 inc si
 add di,2
 loop .compare
 jmp .found
.next:
 add bx,2
 cmp bx,4000-64
 jbe .scan
 jmp .done
.found:
 mov ax,ss
 mov es,ax
 cmp word [cs:get_recovery_prompt_seen],0
 jne .held
 mov word [cs:get_recovery_prompt_seen],1
 mov [cs:get_recovery_child_ds],ax
 mov ax,[es:RECOVERY_STEPS]
 mov [cs:get_recovery_steps],ax
 mov ax,[es:RECOVERY_PAUSE]
 mov [cs:get_recovery_paused],ax
 mov ax,[es:RECOVERY_SCOPE]
 mov [cs:get_recovery_scope],ax
 mov ax,[es:RECOVERY_SERIAL]
 mov [cs:get_recovery_serial],ax
 mov ah,0x51
 pushf
 call far [cs:old21]
 mov [cs:get_recovery_current_psp],bx
 mov ax,[cs:parent_ds]
 mov es,ax
 mov ax,[es:RECOVERY_ACTIVE]
 mov [cs:get_recovery_program_active],ax
 mov ax,[cs:parent_psp]
 dec ax
 mov es,ax
 mov ax,[es:3]
 mov [cs:get_recovery_parent_extent],ax
 mov ax,[cs:parent_psp]
 add ax,16+RECOVERY_KERNEL
 mov es,ax
 mov si,RECOVERY_STATE
 mov di,get_recovery_prefix
 mov cx,14
.capture:
 mov ax,[es:si]
 mov [cs:di],ax
 add si,2
 add di,2
 loop .capture
.held:
 mov ax,ss
 mov es,ax
 mov ax,[es:RECOVERY_STEPS]
 cmp ax,[cs:get_recovery_steps]
 jne .unsafe
 cmp word [es:RECOVERY_PAUSE],1
 jne .unsafe
 cmp word [es:RECOVERY_SCOPE],1
 jne .unsafe
 cmp word [es:RECOVERY_SERIAL],1
 jne .unsafe
 mov ax,[cs:parent_psp]
 add ax,16+RECOVERY_KERNEL
 mov es,ax
 mov si,RECOVERY_STATE
 mov di,get_recovery_prefix
 mov cx,14
.stable:
 mov ax,[es:si]
 cmp ax,[cs:di]
 jne .unsafe
 add si,2
 add di,2
 loop .stable
 inc word [cs:get_recovery_hold_ticks]
 cmp word [cs:get_recovery_hold_ticks],5
 jb .done
 mov dx,0x1c0d
 call get_finish_key
 jc .done
 mov word [cs:get_recovery_retry_key],1
 jmp .done
.unsafe:
 mov word [cs:get_recovery_unsafe],1
.done:
 restore
 ret
get_recovery_notice: db 'ASPECT memory restore incomplete.'
'''
