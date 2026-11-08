"""Read-only timer evidence of the parent Help-frame loan and its guards."""
import re,struct
WORDS=['visible_samples','guard_samples','snapshot_samples','released_during_child','parent_retired','errors','view_offset','view_segment','parent_psp','mcb_owner','mcb_paragraphs']
BYTES=2*len(WORDS)
def instrument(source,parent_map,child_map,no_driver=False):
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',parent_map.read_text(),re.M|re.I)}
 seg,owned=symbols['render_snapshot_owned'];assert symbols['render_program_owned'][0]==seg
 child={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',child_map.read_text(),re.M|re.I)}
 child_seg,display_owned=child['_native_display_owned']
 view_seg,view=symbols['redisplay_live']

 code=r'''
lf_tick:
 cmp word [cs:exec_seen],1
 jne .done
 mov ax,[cs:parent_psp]
 or ax,ax
 jz .done
 mov [cs:lf_parent_psp],ax
 add ax,16+LOAN_SEG
 mov es,ax
 cmp word [cs:lf_visible_samples],0
 je .visible
 cmp word [cs:exec_done],0
 jne .returned
 cmp word [cs:hp_stage],4
 jne .visible
 cmp word [es:LOAN_OWNED],0
 jne .visible
 mov word [cs:lf_released_during_child],1
 jmp .visible
.returned:
 mov ax,[es:LOAN_OWNED]
 or ax,[es:SNAPSHOT_OWNED]
 or ax,[es:PROGRAM_OWNED]
 jnz .visible
 mov word [cs:lf_parent_retired],1
.visible:
 cmp word [cs:exec_done],0
 jne .done
 mov ax,0xb800
 mov es,ax
 cmp word [es:166],0x1f50
 jne .done
 cmp word [es:176],0x1f73
 jne .done
 inc word [cs:lf_visible_samples]
 mov ax,[cs:parent_psp]
 add ax,16+LOAN_SEG
 mov es,ax
 cmp word [es:LOAN_OWNED],1
 jne .bad
 cmp word [es:PROGRAM_OWNED],2
 jne .bad
 mov ax,[cs:nip_child_psp]
 add ax,16+CHILD_SEG
 mov es,ax
 cmp word [es:CHILD_DISPLAY_OWNED],0
 jne .bad
 inc word [cs:lf_snapshot_samples]
 mov ax,[cs:parent_psp]
 add ax,16+VIEW_SEG
 mov [cs:lf_view_segment],ax
 mov word [cs:lf_view_offset],VIEW_OFF
 mov es,ax
 mov bx,VIEW_OFF
 mov cx,16
.guards:
 cmp byte [es:bx],0xa5
 jne .bad
 cmp byte [es:bx+4016],0x5a
 jne .bad
 inc bx
 loop .guards
 inc word [cs:lf_guard_samples]
 mov ax,[cs:parent_psp]
 dec ax
 mov es,ax
 mov ax,[es:1]
 mov [cs:lf_mcb_owner],ax
 mov ax,[es:3]
 mov [cs:lf_mcb_paragraphs],ax
 jmp .done
.bad:
 inc word [cs:lf_errors]
.done:
 ret
'''
 if no_driver:code=code.replace('nip_child_psp','nd_child_psp')
 for n,v in dict(LOAN_SEG=seg,LOAN_OWNED=owned,SNAPSHOT_OWNED=symbols['render_snapshot_owned'][1],PROGRAM_OWNED=symbols['render_program_owned'][1],VIEW_SEG=view_seg,VIEW_OFF=view,CHILD_SEG=child_seg,CHILD_DISPLAY_OWNED=display_owned).items():code=code.replace(n,str(v))
 marker='timer:\n save\n';assert source.count(marker)==1
 source=source.replace(marker,marker+' call lf_tick\n').replace('resident_end:',code+'\nresident_end:')
 return source.replace('sample_end:',''.join('lf_'+name+': dw 0\n' for name in WORDS)+'sample_end:')
def read(raw):
 assert len(raw)==BYTES
 return dict(zip(WORDS,struct.unpack('<'+str(len(WORDS))+'H',raw)))
