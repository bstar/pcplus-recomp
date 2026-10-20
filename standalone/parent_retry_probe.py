"""Observe a second real CLI/PROGRAM lifetime without repairing the first."""
import re

WORDS=('seen returned status carry psp child_function child_code nested_calls nested_carry '
       'nested_lease resources_equal final_lease vector_before_off vector_before_seg '
       'vector_after_off vector_after_seg retained_owner retained_paras callback_before '
       'callback_after extra_owner extra_paras extra_word jft_equal owners_equal exec_error largest_free observer_segment nested_status nested_kernel_flags nested_caller_flags').split()
BYTES=len(WORDS)*2+872+400

def instrument(source,map_path,child_map,offsets):
    symbols=lambda path:{n:(int(s,16),int(o,16)) for s,o,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',path.read_text(),re.M|re.I)}
    parent=symbols(map_path);child=symbols(child_map)
    lease_seg,lease=parent['render_program_owned'];data_seg,hits=child['_aspect_exit_hits']
    values=dict(KIND=offsets['terminal_program_kind'],ACTIVE=offsets['terminal_program_active'],
        LEASE_SEG=lease_seg,LEASE=lease,DATA_SEG=data_seg,HITS=hits)
    old=' cmp bx,[cs:parent_psp]\n jne .chain\n restore\n pushf'
    assert source.count(old)==1
    source=source.replace(old,old.replace('jne .chain','jne retry_status'))
    # Do not let the observer's redundant snapshots prevent the very retry it
    # observes. Keep one exact pre-EXEC image and compare each live byte after
    # EXEC; omit unrelated renderer admission telemetry in this dedicated mode.
    timer_start=source.index('timer:\n save\n cld')
    timer_end=source.index('\n.done:\n restore\n jmp far [cs:old1c]',timer_start)+len('\n.done:\n restore\n jmp far [cs:old1c]')
    source=source[:timer_start]+'timer:\n save\n cld\n'+(' call mouse_probe_tick\n' if 'mouse_probe_tick:' in source else '')+' restore\n jmp far [cs:old1c]'+source[timer_end:]
    source=re.sub(r'^admit_snapshots: times \d+ db 0\n|^admit_bda: times 256 db 0\n|^admit_words: times \d+ dw 0\n', '', source, flags=re.M)
    source=re.sub(r'^resource_after: times \d+ db 0$', 'resource_after:', source, flags=re.M)
    old=''' mov di,resource_after
 call copy_resources
 push cs
 pop es
 mov si,resource_before
 mov di,resource_after
 mov cx,'''
    start=source.index(old);end=source.index(' repe cmpsb',start)+len(' repe cmpsb')
    source=source[:start]+' call retry_compare_resources\n or ax,ax'+source[end:]
    table=re.search(r'^resource_table: dw (.*)$',source,re.M)[1].split(',')
    values['RESOURCE_COUNT']=len(table)//2
    old='nested_exec:\n cmp word [cs:exec_done],0\n jne handler.chain'
    assert source.count(old)==1;source=source.replace(old,old.replace('jne handler.chain','jne retry_dispatch'))
    old=' mov [cs:retained_raw_status],ax'
    new=''' cmp word [cs:rp_returned],1
 jne .first_status
 mov [cs:rp_status],ax
 jmp short .status_done
.first_status:
 mov [cs:retained_raw_status],ax
.status_done:'''
    assert source.count(old)==1;source=source.replace(old,new)
    old='.exit_check:\n'
    new='''.exit_check:
 cmp word [cs:rp_seen],1
 jne .retry_exit_done
 cmp word [cs:rp_returned],0
 jne .retry_exit_done
 cmp byte [ss:bp+17],0x4c
 je .retry_exit_psp
 cmp byte [ss:bp+17],0x31
 jne .retry_exit_done
.retry_exit_psp:
 mov ah,0x62
 int 0x21
 mov es,bx
 mov ax,[es:0x16]
 cmp ax,[cs:parent_psp]
 jne .retry_exit_done
 mov [cs:rp_psp],bx
 xor ax,ax
 mov al,[ss:bp+17]
 mov [cs:rp_child_function],ax
 mov al,[ss:bp+16]
 mov [cs:rp_child_code],ax
 push cs
 pop ds
 mov ax,0xb800
 mov es,ax
 xor si,si
 mov di,retry_exit_screen
 mov cx,400
.retry_video:
 mov al,[es:si]
 mov [di],al
 add si,2
 inc di
 loop .retry_video
.retry_exit_done:
'''
    assert source.count(old)==1;source=source.replace(old,new)
    if 'mouse_probe_tick:' in source:
        old='.menu:\n cmp word [cs:mp_resume_mask],0x0b'
        new='.menu:\n cmp word [cs:rp_returned],1\n jne .done\n cmp word [cs:mp_resume_mask],0x0b'
        assert source.count(old)==1;source=source.replace(old,new)
    code=r'''
retry_status:
 cmp word [cs:rp_seen],1
 jne handler.chain
 cmp word [cs:rp_returned],0
 jne handler.chain
 mov es,bx
 mov ax,[es:0x16]
 cmp ax,[cs:parent_psp]
 jne handler.chain
 restore
 pushf
 call far [cs:old21]
 save
 mov bp,sp
 mov ax,[ss:bp+16]
 mov [cs:rp_nested_status],ax
 mov ax,[ss:bp+18]
 mov [cs:rp_nested_kernel_flags],ax
 mov ax,[ss:bp+24]
 mov [cs:rp_nested_caller_flags],ax
 mov ax,[ss:bp+18]
 mov [ss:bp+24],ax
 restore
 iret
retry_dispatch:
 cmp word [cs:exec_done],1
 jne handler.chain
 mov ah,0x62
 int 0x21
 cmp bx,[cs:parent_psp]
 jne retry_nested
 mov ax,ds
 cmp ax,[cs:parent_ds]
 jne handler.chain
 cmp word [KIND],4
 jne handler.chain
 cmp word [ACTIVE],1
 jne handler.chain
 push cs
 pop ds
 inc word [rp_seen]
 mov ax,cs
 mov [rp_observer_segment],ax
 cmp word [rp_seen],1
 jne handler.chain
 mov bx,0xffff
 mov ah,0x48
 int 0x21
 mov [rp_largest_free],bx
 mov di,retry_before_jft
 call copy_jft
 mov di,retry_before_owners
 call copy_owners
 xor ax,ax
 mov es,ax
 mov ax,[es:0x1b*4]
 mov [rp_vector_before_off],ax
 mov ax,[es:0x1b*4+2]
 mov [rp_vector_before_seg],ax
 mov ax,[retained_psp]
 add ax,0x10+DATA_SEG
 mov es,ax
 mov ax,[es:HITS]
 mov [rp_callback_before],ax
 restore
 pushf
 call far [cs:old21]
 save
 push cs
 pop ds
 mov word [rp_returned],1
 mov bp,sp
 mov ax,[ss:bp+16]
 mov [rp_exec_error],ax
 mov ax,[ss:bp+18]
 and ax,1
 mov [rp_carry],ax
 mov di,retry_after_jft
 call copy_jft
 mov di,retry_after_owners
 call copy_owners
 push cs
 pop es
 mov si,retry_before_jft
 mov di,retry_after_jft
 mov cx,20
 repe cmpsb
 jne .owners
 mov word [rp_jft_equal],1
.owners:
 mov si,retry_before_owners
 mov di,retry_after_owners
 mov cx,416
 repe cmpsb
 jne .vector
 mov word [rp_owners_equal],1
.vector:
 xor ax,ax
 mov es,ax
 mov ax,[es:0x1b*4]
 mov [rp_vector_after_off],ax
 mov ax,[es:0x1b*4+2]
 mov [rp_vector_after_seg],ax
 ; Invoke only the known retained test ISR, after checking its exact address.
 cmp ax,[retained_vector_seg]
 jne .retained
 mov ax,[es:0x1b*4]
 cmp ax,[retained_vector_off]
 jne .retained
 int 0x1b
.retained:
 mov ax,[retained_psp]
 add ax,0x10+DATA_SEG
 mov es,ax
 mov ax,[es:HITS]
 mov [rp_callback_after],ax
 mov ax,[retained_psp]
 dec ax
 mov es,ax
 mov ax,[es:1]
 mov [rp_retained_owner],ax
 mov ax,[es:3]
 mov [rp_retained_paras],ax
 mov ax,[retained_extra]
 dec ax
 mov es,ax
 mov ax,[es:1]
 mov [rp_extra_owner],ax
 mov ax,[es:3]
 mov [rp_extra_paras],ax
 mov ax,[retained_extra]
 mov es,ax
 mov ax,[es:0]
 mov [rp_extra_word],ax
 mov ax,[parent_psp]
 add ax,0x10+LEASE_SEG
 mov es,ax
 mov ax,[es:LEASE]
 mov [rp_final_lease],ax
 mov bp,sp
 mov ax,[ss:bp+18]
 mov [ss:bp+24],ax
 restore
 iret
retry_nested:
 mov es,bx
 mov ax,[es:0x16]
 cmp ax,[cs:parent_psp]
 jne handler.chain
 cmp word [cs:rp_seen],1
 jne handler.chain
 cmp word [cs:rp_returned],0
 jne handler.chain
 push cs
 pop ds
 inc word [rp_nested_calls]
 mov ax,[parent_psp]
 add ax,0x10+LEASE_SEG
 mov es,ax
 mov ax,[es:LEASE]
 mov [rp_nested_lease],ax
 mov di,resource_before
 call copy_resources
 restore
 pushf
 call far [cs:old21]
 save
 push cs
 pop ds
 mov bp,sp
 mov ax,[ss:bp+18]
 and ax,1
 mov [rp_nested_carry],ax
 call retry_compare_resources
 or ax,ax
 jne .done
 mov word [rp_resources_equal],1
.done:
 mov bp,sp
 mov ax,[ss:bp+18]
 mov [ss:bp+24],ax
 restore
 iret
retry_compare_resources:
 mov es,[parent_ds]
 mov si,resource_table
 mov di,resource_before
 mov bp,RESOURCE_COUNT
 xor dx,dx
.region:
 lodsw
 mov bx,ax
 lodsw
 mov cx,ax
.byte:
 mov al,[es:bx]
 cmp al,[di]
 je .equal
 mov dx,1
.equal:
 inc bx
 inc di
 loop .byte
 dec bp
 jnz .region
 mov ax,dx
 ret
'''
    for name,value in values.items():code=re.sub(r'\b'+name+r'\b',str(value),code)
    source=source.replace('resident_end:',code+'\nresident_end:')
    # DOS4B returns carry, DOS4D returns AX. The inner far interrupt call has
    # entered with IF cleared by the observer's own interrupt entry. Forward
    # its carry without replacing the real caller's IF/DF/other FLAGS bits.
    old=' mov ax,[ss:bp+18]\n mov [ss:bp+24],ax'
    assert source.count(old)>=4
    source=source.replace(old,' mov ax,[ss:bp+18]\n and ax,1\n and word [ss:bp+24],0xfffe\n or [ss:bp+24],ax')
    data=''.join('rp_'+n+': dw 0\n' for n in WORDS)
    data+='retry_before_jft: times 20 db 0\nretry_after_jft: times 20 db 0\nretry_before_owners: times 416 db 0\nretry_after_owners: times 416 db 0\n'
    data+='retry_exit_screen: times 400 db 0\n'
    target='mp_seen: dw 0' if 'mp_seen: dw 0' in source else 'retained_function: dw 0'
    assert source.count(target)==1
    return source.replace(target,data+target)
