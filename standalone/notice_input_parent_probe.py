"""Active INT33 probe of the ordinary ASPECT child's actual native callback."""
import re
WORDS=['seen','callback_off','callback_seg','child_psp','scale_x','scale_y','bios','event',
    'returned_ds','queued_count','queued_code','exit_seen','notice_status','notice_cause','notice_key','notice_service',
    'exit_mask','exit_off','exit_seg']
BYTES=len(WORDS)*2
def instrument(source,child_map,event):
    assert event in (2,8)
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',child_map.read_text(),re.M|re.I)}
    code,callback=symbols['mouse_callback'];data,scale=symbols['_mouse_scale_x']
    fields={n:symbols[n][1] for n in ['_mouse_scale_y','_runtime_keyboard_mode','_mouse_count','_mouse_code','_program_notice_result']}
    assert all(symbols[n][0]==data for n in fields)
    timer='timer:\n save\n';assert source.count(timer)==1
    source=source.replace(timer,timer+' call child_input_tick\n')
    exit=' inc word [child_exits]\n';assert source.count(exit)==1
    source=source.replace(exit,exit+' call child_input_exit\n')
    code_source=r'''
child_input_tick:
 cmp word [cs:exec_seen],1
 jne .done
 cmp word [cs:exec_done],0
 jne .done
 cmp word [cs:nip_seen],0
 jne .done
 call mouse_query
 cmp cx,11
 jne .done
 cmp dx,CHILD_CALLBACK
 jne .done
 cmp word [es:CHILD_CALLBACK-2],0xffff
 jne .done
 mov ax,es
 sub ax,CHILD_CODE+0x10
 jc .done
 mov bx,ax
 mov es,ax
 cmp word [es:0],0x20cd
 jne .done
 mov ax,[cs:parent_psp]
 cmp [es:0x16],ax
 jne .done
 mov [cs:nip_child_psp],bx
 mov [cs:nip_callback_off],dx
 mov ax,bx
 add ax,CHILD_CODE+0x10
 mov [cs:nip_callback_seg],ax
 mov ax,bx
 add ax,CHILD_DATA+0x10
 mov es,ax
 mov ax,[es:CHILD_SCALE_X]
 mov [cs:nip_scale_x],ax
 mov ax,[es:CHILD_SCALE_Y]
 mov [cs:nip_scale_y],ax
 mov ax,[es:CHILD_BIOS]
 mov [cs:nip_bios],ax
 mov word [cs:nip_seen],1
 mov word [cs:nip_event],CHILD_EVENT
 push ds
 mov bx,0x40
 mov ds,bx
 mov ax,CHILD_EVENT
 xor si,si
 xor di,di
 cli
 call far [cs:nip_callback_off]
 mov ax,ds
 mov [cs:nip_returned_ds],ax
 pop ds
 mov ax,[cs:nip_child_psp]
 add ax,CHILD_DATA+0x10
 mov es,ax
 mov ax,[es:CHILD_COUNT]
 mov [cs:nip_queued_count],ax
 mov ax,[es:CHILD_EVENT_CODE]
 mov [cs:nip_queued_code],ax
.done:
 ret
child_input_exit:
 cmp word [cs:nip_seen],1
 jne .done
 call mouse_query
 mov [cs:nip_exit_mask],cx
 mov [cs:nip_exit_off],dx
 mov [cs:nip_exit_seg],es
 mov ax,[cs:nip_child_psp]
 add ax,CHILD_DATA+0x10
 mov es,ax
 inc word [cs:nip_exit_seen]
 mov ax,[es:CHILD_RESULT]
 mov [cs:nip_notice_status],ax
 mov ax,[es:CHILD_RESULT+2]
 mov [cs:nip_notice_cause],ax
 mov ax,[es:CHILD_RESULT+4]
 mov [cs:nip_notice_key],ax
 mov ax,[es:CHILD_RESULT+6]
 mov [cs:nip_notice_service],ax
.done:
 ret
'''
    values=dict(CHILD_CALLBACK=callback,CHILD_CODE=code,CHILD_DATA=data,CHILD_SCALE_X=scale,
        CHILD_SCALE_Y=fields['_mouse_scale_y'],CHILD_BIOS=fields['_runtime_keyboard_mode'],
        CHILD_COUNT=fields['_mouse_count'],CHILD_EVENT_CODE=fields['_mouse_code'],CHILD_RESULT=fields['_program_notice_result'],CHILD_EVENT=event)
    for key in sorted(values,key=len,reverse=True):code_source=code_source.replace(key,str(values[key]))
    source=source.replace('resident_end:',code_source+'\nresident_end:')
    source=source.replace('sample_end:',''.join('nip_'+n+': dw 0\n' for n in WORDS)+'sample_end:')
    return source
