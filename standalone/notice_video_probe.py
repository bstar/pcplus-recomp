"""Passive entry-only INT10 witness for the owned Help DOS fixture."""
import re,struct
FIELDS=['ax','bx','cx','dx','si','di','bp','ds','es','ss','sp','ip','cs','flags','stage']
CAPACITY=64
BYTES=4+CAPACITY*len(FIELDS)*2+322


def instrument(source,child_map,no_driver=False):
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(
  r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',child_map.read_text(),re.M|re.I)}
 code=r'''
vw_install:
 save
 mov ax,0x3510
 int 0x21
 mov [cs:vw_old10],bx
 mov [cs:vw_old10+2],es
 push cs
 pop ds
 mov dx,vw_handler
 mov ax,0x2510
 int 0x21
 restore
 ret
vw_handler:
 save
 cld
 mov bp,sp
 cmp word [cs:nip_seen],1
 jne .done
 cmp word [cs:exec_done],0
 jne .done
 cmp word [cs:hp_stage],1
 jb .done
 mov ax,[cs:nip_child_psp]
 add ax,0x10+CHILD_DATA
 mov dx,ss
 cmp ax,dx
 jne .done
 cmp word [cs:vw_count],64
 jb .record
 inc word [cs:vw_overflow]
 jmp .done
.record:
 mov ax,[cs:vw_count]
 mov cx,30
 mul cx
 mov di,vw_records
 add di,ax
 inc word [cs:vw_count]
'''
 offsets=[16,14,12,10,8,6,4,2,0]
 for i,offset in enumerate(offsets):code+=' mov ax,[ss:bp+'+str(offset)+']\n mov [cs:di+'+str(i*2)+'],ax\n'
 code+=' mov ax,ss\n mov [cs:di+18],ax\n lea ax,[bp+20]\n mov [cs:di+20],ax\n'
 for dest,offset in [(22,20),(24,22),(26,24)]:code+=' mov ax,[ss:bp+'+str(offset)+']\n mov [cs:di+'+str(dest)+'],ax\n'
 code+=' mov ax,[cs:hp_stage]\n mov [cs:di+28],ax\n.done:\n restore\n jmp far [cs:vw_old10]\nvw_old10: dw 0,0\nvw_descriptor: db "VWX1"\n dw vw_count,vw_overflow,vw_records\n'
 code+=r'''
vw_parent_tick:
 cmp word [cs:exec_done],1
 jne .done
 mov ax,0xb800
 mov es,ax
 xor bx,bx
 mov di,vw_parent_rows
 mov cx,160
.top:
 mov al,[es:bx]
 mov [cs:di],al
 inc bx
 inc di
 loop .top
 mov bx,1120
 mov cx,160
.selected:
 mov al,[es:bx]
 mov [cs:di],al
 inc bx
 inc di
 loop .selected
 mov word [cs:vw_parent_seen],1
.done:
 ret
'''
 code=code.replace('CHILD_DATA',str(symbols['_runtime_error'][0]))
 if no_driver:code=code.replace('nip_seen','nd_seen').replace('nip_child_psp','nd_child_psp')
 marker=' mov [old21],bx\n';assert source.count(marker)==1
 source=source.replace(marker,' call vw_install\n'+marker)
 marker='timer:\n save\n';assert source.count(marker)==1
 source=source.replace(marker,marker+' call vw_parent_tick\n')
 marker=' mov dx,filename\n xor cx,cx\n mov ah,0x3c\n';assert source.count(marker)==1
 restore=' push ds\n mov es,[cs:report_source]\n mov dx,[es:vw_old10]\n mov ds,[es:vw_old10+2]\n mov ax,0x2510\n int 0x21\n pop ds\n'
 source=source.replace(marker,restore+marker)
 source=source.replace('resident_end:',code+'\nresident_end:')
 return source.replace('sample_end:','vw_count: dw 0\nvw_overflow: dw 0\nvw_records: times 64*30 db 0\nvw_parent_seen: dw 0\nvw_parent_rows: times 320 db 0\nsample_end:')


def read(raw):
 assert len(raw)==BYTES
 count,overflow=struct.unpack_from('<2H',raw);assert count<=CAPACITY
 return dict(overflow=overflow,records=[dict(zip(FIELDS,struct.unpack_from('<15H',raw,4+i*30))) for i in range(count)],
  parent_seen=struct.unpack_from('<H',raw,BYTES-322)[0],parent_rows_hex=raw[-320:].hex(),
  parent_rows=[raw[-320:-160:2].decode('cp437'),raw[-160::2].decode('cp437')])
