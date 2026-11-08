"""Capture each real nested compiler EXEC's retained kernel/MCB ownership."""
import re
from compiler_bridge_recovery_observer import PREFIX

FIELDS=['parent_extent','parent_mcb_owner','current_psp','child_ss','child_ds']
WORDS=len(FIELDS)+len(PREFIX)

def attach(source, *, count, listing, parent):
 assert count in (2,3)
 match=re.search(r'^([0-9a-f]+):([0-9a-f]+)\s+_compiler_lease_storage\b',listing,re.M);assert match
 segment,offset=(int(n,16) for n in match.groups())
 assert (segment*16+offset+28+15)//16+16<=parent['experimental_compiler_lease_module']['keep_paragraphs']
 marker='get_compiler_largest: dw 0';assert source.count(marker)==1
 source=source.replace(marker,'get_repeat_samples: times '+str(count*WORDS)+' dw 0\n'+marker)
 marker=' inc word [cs:get_compiler_attempts]\n mov ah,0x48';assert source.count(marker)==1
 source=source.replace(marker,' inc word [cs:get_compiler_attempts]\n call get_repeat_capture\n mov ah,0x48')
 body=ASM.replace('REPEAT_COUNT',str(count)).replace('REPEAT_BYTES',str(WORDS*2)).replace('REPEAT_KERNEL',str(segment)).replace('REPEAT_STATE',str(offset))
 marker='resident_end:\nstart:';assert source.count(marker)==1
 return source.replace(marker,body+'\n'+marker)

ASM=r'''
get_repeat_capture:
 save
 mov ax,[cs:get_compiler_attempts]
 dec ax
 cmp ax,REPEAT_COUNT
 jae .done
 mov bx,REPEAT_BYTES
 mul bx
 mov di,get_repeat_samples
 add di,ax
 mov ax,[cs:parent_psp]
 dec ax
 mov es,ax
 mov ax,[es:3]
 mov [cs:di],ax
 mov ax,[es:1]
 mov [cs:di+2],ax
 mov ax,ss
 mov [cs:di+6],ax
 mov ax,ds
 mov [cs:di+8],ax
 mov ah,0x51
 pushf
 call far [cs:old21]
 mov [cs:di+4],bx
 add di,10
 mov ax,[cs:parent_psp]
 add ax,16+REPEAT_KERNEL
 mov es,ax
 mov si,REPEAT_STATE
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
'''
