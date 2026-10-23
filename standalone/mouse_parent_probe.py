"""Independent INT33 registration/state and native-menu probe for DOS parents."""
import re
WORDS=['seen','before_mask','before_off','before_seg','resume_mask','resume_off','resume_seg',
 'depth_before','depth_after','returned_ds','scale_x','scale_y','count_before','count_after',
 'menu_stage','menu_count','menu_code','button_count','button_code',
 'after_mask','after_off','after_seg','state_bytes','state_equal',
 'suspended_mask','suspended_off','suspended_seg']
BUFFER=2048
BYTES=len(WORDS)*2+BUFFER*2

def instrument(source,map_path,offsets):
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',map_path.read_text(),re.M|re.I)}
    code_seg,callback=symbols['mouse_callback'];depth_seg,depth=symbols['mouse_depth']
    assert code_seg==depth_seg
    data_seg,scale_x=symbols['mouse_scale_x']
    fields={n:symbols[n][1] for n in ['mouse_scale_y','mouse_count','mouse_code','mouse_base_x','mouse_base_y']}
    assert all(symbols[n][0]==data_seg for n in fields)
    values=dict(CODE_SEG=code_seg,CALLBACK=callback,DEPTH=depth,DATA_SEG=data_seg,SCALE_X=scale_x,
        SCALE_Y=fields['mouse_scale_y'],COUNT=fields['mouse_count'],EVENT=fields['mouse_code'],
        BASE_X=fields['mouse_base_x'],BASE_Y=fields['mouse_base_y'],ACTIVE=offsets['terminal_program_active'])
    before=' inc word [exec_seen]\n mov di,before_jft'
    assert source.count(before)==1;source=source.replace(before,' inc word [exec_seen]\n call mouse_probe_suspended\n mov di,before_jft')
    startup=' jne collect\n mov [old21],bx'
    assert source.count(startup)==1
    source=source.replace(startup,' jne collect\n call mouse_probe_before\n mov [old21],bx')
    old='timer:\n save\n cld';assert source.count(old)==1
    source=source.replace(old,old+'\n call mouse_probe_tick')
    old='.exit_check:\n';assert source.count(old)==1
    source=source.replace(old,old+''' cmp byte [ss:bp+17],0x4c
 jne .mouse_exit_done
 cmp word [cs:exec_done],1
 jne .mouse_exit_done
 mov ah,0x62
 int 0x21
 cmp bx,[cs:parent_psp]
 jne .mouse_exit_done
 call mouse_probe_end
.mouse_exit_done:
''')
    code=r'''
; Exchange/restore the actual registration, without supplying an expected one.
mouse_query:
 xor cx,cx
 xor dx,dx
 mov es,dx
 mov ax,0x14
 int 0x33
 push cx
 push dx
 push es
 mov ax,0x14
 int 0x33
 pop es
 pop dx
 pop cx
 ret
mouse_probe_suspended:
 save
 call mouse_query
 mov [cs:mp_suspended_mask],cx
 mov [cs:mp_suspended_off],dx
 mov [cs:mp_suspended_seg],es
 restore
 ret
mouse_probe_before:
 save
 call mouse_query
 mov [cs:mp_before_mask],cx
 mov [cs:mp_before_off],dx
 mov [cs:mp_before_seg],es
 xor bx,bx
 mov ax,0x15
 int 0x33
 cmp bx,0
 je .done
 cmp bx,2048
 ja .done
 mov [cs:mp_state_bytes],bx
 push cs
 pop es
 mov dx,mouse_before
 mov ax,0x16
 int 0x33
.done:
 restore
 ret
mouse_probe_tick:
 cmp word [cs:exec_done],1
 jne .done
 mov ax,ss
 cmp ax,[cs:parent_ds]
 jne .done
 mov es,ax
 cmp word [es:ACTIVE],0
 jne .done
 cmp word [cs:mp_seen],0
 jne .menu
 mov word [cs:mp_seen],1
 call mouse_query
 mov [cs:mp_resume_mask],cx
 mov [cs:mp_resume_off],dx
 mov [cs:mp_resume_seg],es
 cmp cx,0x0b
 jne .done
 mov ax,[cs:parent_psp]
 add ax,0x10+CODE_SEG
 mov es,ax
 cmp [cs:mp_resume_seg],ax
 jne .done
 cmp word [cs:mp_resume_off],CALLBACK
 jne .done
 mov ax,[es:DEPTH]
 mov [cs:mp_depth_before],ax
 mov ax,[cs:parent_psp]
 add ax,0x10+DATA_SEG
 mov es,ax
 mov ax,[es:SCALE_X]
 mov [cs:mp_scale_x],ax
 mov ax,[es:SCALE_Y]
 mov [cs:mp_scale_y],ax
 mov ax,[es:COUNT]
 mov [cs:mp_count_before],ax
 mov si,[es:BASE_X]
 mov di,[es:BASE_Y]
 xor ax,ax
 call mouse_invoke
 mov ax,[cs:parent_psp]
 add ax,0x10+CODE_SEG
 mov es,ax
 mov ax,[es:DEPTH]
 mov [cs:mp_depth_after],ax
 mov ax,[cs:parent_psp]
 add ax,0x10+DATA_SEG
 mov es,ax
 mov ax,[es:COUNT]
 mov [cs:mp_count_after],ax
.menu:
 cmp word [cs:mp_resume_mask],0x0b
 jne .done
 cmp word [cs:mp_menu_stage],2
 jae .done
 mov ax,0xb800
 mov es,ax
 cmp word [es:2],0x1f50
 jne .done
 cmp word [es:4],0x1f43
 jne .done
 cmp word [es:20],0x1f6f
 jne .done
 cmp word [cs:mp_menu_stage],0
 jne .select
 mov ax,1
 xor si,si
 mov di,[cs:mp_scale_y]
 shl di,1
 call mouse_invoke
 mov ax,[cs:parent_psp]
 add ax,0x10+DATA_SEG
 mov es,ax
 mov ax,[es:COUNT]
 mov [cs:mp_menu_count],ax
 mov ax,[es:EVENT]
 mov [cs:mp_menu_code],ax
 inc word [cs:mp_menu_stage]
 jmp short .done
.select:
 cmp word [es:1130],0x7057
 jne .done
 mov ax,2
 xor si,si
 mov di,[cs:mp_scale_y]
 shl di,1
 call mouse_invoke
 mov ax,[cs:parent_psp]
 add ax,0x10+DATA_SEG
 mov es,ax
 mov ax,[es:COUNT]
 mov [cs:mp_button_count],ax
 mov ax,[es:EVENT]
 mov [cs:mp_button_code],ax
 inc word [cs:mp_menu_stage]
.done:
 ret
mouse_invoke:
 ; Never invoke an unrecognized callback, even if registration is broken.
 push ax
 mov ax,[cs:parent_psp]
 add ax,0x10+CODE_SEG
 cmp [cs:mp_resume_seg],ax
 jne .rejected
 cmp word [cs:mp_resume_off],CALLBACK
 jne .rejected
 pop ax
 push ds
 mov bx,0x40
 mov ds,bx
 cli
 call far [cs:mp_resume_off]
 mov bx,ds
 mov [cs:mp_returned_ds],bx
 pop ds
 ret
.rejected:
 pop ax
 ret
mouse_probe_end:
 save
 call mouse_query
 mov [cs:mp_after_mask],cx
 mov [cs:mp_after_off],dx
 mov [cs:mp_after_seg],es
 cmp word [cs:mp_state_bytes],0
 je .done
 push cs
 pop es
 mov dx,mouse_after
 mov ax,0x16
 int 0x33
 push cs
 pop ds
 push cs
 pop es
 mov si,mouse_before
 mov di,mouse_after
 mov cx,[cs:mp_state_bytes]
 cld
 repe cmpsb
 jne .done
 mov word [cs:mp_state_equal],1
.done:
 restore
 ret
'''
    for name,value in values.items():code=re.sub(r'\b'+name+r'\b',str(value),code)
    assert source.count('resident_end:')==1;source=source.replace('resident_end:',code+'\nresident_end:')
    data=''.join('mp_'+n+': dw 0\n' for n in WORDS)+'mouse_before: times 2048 db 0\nmouse_after: times 2048 db 0\n'
    target='retained_function: dw 0' if 'retained_function: dw 0' in source else 'nested_count: dw 0'
    assert source.count(target)==1
    source=source.replace(target,data+target)
    # The baseline collector duplicates the full sample in its COM image.
    # Keep the resident snapshots, but allocate the collector's copy through
    # DOS48 after moving its stack inside a correctly resized PSP block.
    old=''' pushf
 cli
 push ds
 mov ax,es
 mov ds,ax
 push cs
 pop es
 mov si,sample
 mov di,buffer
 mov cx,sample_end-sample
 cld
 rep movsb
 pop ds
 popf'''
    new=''' mov [cs:report_source],es
 cli
 mov ax,cs
 mov ss,ax
 mov sp,report_stack_top
 sti
 push cs
 pop es
 mov bx,(report_stack_top-$$+0x100+15)/16
 mov ah,0x4a
 int 0x21
 jc failed
 mov bx,(sample_end-sample+15)/16
 mov ah,0x48
 int 0x21
 jc failed
 mov [cs:report_segment],ax
 pushf
 cli
 push ds
 mov es,ax
 mov ds,[cs:report_source]
 mov si,sample
 xor di,di
 mov cx,sample_end-sample
 cld
 rep movsb
 pop ds
 popf'''
    assert source.count(old)==1;source=source.replace(old,new)
    old=' mov dx,buffer\n mov cx,sample_end-sample\n mov ah,0x40\n int 0x21\n jc failed'
    new=' push ds\n mov ds,[cs:report_segment]\n xor dx,dx\n mov cx,sample_end-sample\n mov ah,0x40\n int 0x21\n pop ds\n jc failed\n cmp ax,sample_end-sample\n jne failed'
    assert source.count(old)==1;source=source.replace(old,new)
    old='buffer: times sample_end-sample db 0';assert source.count(old)==1
    return source.replace(old,'report_source: dw 0\nreport_segment: dw 0\nreport_stack: times 2048 db 0\nreport_stack_top:\n')
