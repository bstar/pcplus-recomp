"""Owned DOS test disables/restores INT33 and seeds a BIOS key at the popup."""
import re
WORDS=['old_off','old_seg','after_off','after_seg','seen','child_psp','bios','seed_status',
    'exit_seen','notice_status','notice_cause','notice_key','notice_service','exit_vector_zero']
BYTES=len(WORDS)*2
def instrument(source,child_map):
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',child_map.read_text(),re.M|re.I)}
    data,bios=symbols['_runtime_keyboard_mode'];result=symbols['_program_notice_result'][1]
    assert symbols['_program_notice_result'][0]==data
    before=' jne collect\n mov [old21],bx';assert source.count(before)==1
    source=source.replace(before,' jne collect\n call no_driver_install\n mov [old21],bx')
    before='timer:\n save\n';assert source.count(before)==1;source=source.replace(before,before+' call no_driver_tick\n')
    before=' inc word [child_exits]\n';assert source.count(before)==1;source=source.replace(before,before+' call no_driver_exit\n')
    before=' mov dx,filename\n xor cx,cx\n mov ah,0x3c\n';assert source.count(before)==1;source=source.replace(before,' call no_driver_restore\n'+before)
    code=r'''
no_driver_install:
 save
 mov ax,0x3533
 int 0x21
 mov [cs:nd_old_off],bx
 mov [cs:nd_old_seg],es
 xor ax,ax
 mov ds,ax
 xor dx,dx
 mov ax,0x2533
 int 0x21
 restore
 ret
no_driver_restore:
 push ds
 mov dx,[buffer+nd_old_off-sample]
 mov ds,[buffer+nd_old_seg-sample]
 mov ax,0x2533
 int 0x21
 pop ds
 mov ax,0x3533
 int 0x21
 mov [buffer+nd_after_off-sample],bx
 mov [buffer+nd_after_seg-sample],es
 ret
no_driver_tick:
 cmp word [cs:exec_seen],1
 jne .done
 cmp word [cs:exec_done],0
 jne .done
 cmp word [cs:nd_seen],0
 jne .done
 xor ax,ax
 mov es,ax
 mov ax,[es:0xcc]
 or ax,[es:0xce]
 jnz .done
 mov ax,0xb800
 mov es,ax
 cmp word [es:1662],0x7050
 jne .done
 cmp word [es:1664],0x7072
 jne .done
 cmp word [es:1696],0x702e
 jne .done
 mov ah,0x62
 int 0x21
 mov es,bx
 cmp word [es:0],0x20cd
 jne .done
 mov ax,[cs:parent_psp]
 cmp [es:0x16],ax
 jne .done
 mov [cs:nd_child_psp],bx
 add bx,CHILD_DATA+0x10
 mov es,bx
 mov ax,[es:CHILD_BIOS]
 mov [cs:nd_bios],ax
 mov word [cs:nd_seen],1
 mov ax,0x0500
 mov cx,0x1c0d
 int 0x16
 xor ah,ah
 mov [cs:nd_seed_status],ax
.done:
 ret
no_driver_exit:
 cmp word [cs:nd_seen],1
 jne .done
 xor ax,ax
 mov es,ax
 mov ax,[es:0xcc]
 or ax,[es:0xce]
 jnz .vector_done
 mov word [cs:nd_exit_vector_zero],1
.vector_done:
 mov ax,[cs:nd_child_psp]
 add ax,CHILD_DATA+0x10
 mov es,ax
 inc word [cs:nd_exit_seen]
 mov ax,[es:CHILD_RESULT]
 mov [cs:nd_notice_status],ax
 mov ax,[es:CHILD_RESULT+2]
 mov [cs:nd_notice_cause],ax
 mov ax,[es:CHILD_RESULT+4]
 mov [cs:nd_notice_key],ax
 mov ax,[es:CHILD_RESULT+6]
 mov [cs:nd_notice_service],ax
.done:
 ret
'''
    for key,value in [('CHILD_DATA',data),('CHILD_BIOS',bios),('CHILD_RESULT',result)]:code=code.replace(key,str(value))
    return source.replace('resident_end:',code+'\nresident_end:').replace('sample_end:',''.join('nd_'+x+': dw 0\n' for x in WORDS)+'sample_end:')
