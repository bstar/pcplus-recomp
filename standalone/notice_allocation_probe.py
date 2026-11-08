"""Passive INT21 allocation telemetry after a notice's Help key admission."""
import re,struct
FIELDS=['stage','request_ah','request_bx','target_es','caller_ip','caller_cs',
        'ds','curbrk','nheapbeg','return_ax','return_bx','carry','owner_psp']
CAPACITY=32
BYTES=4+CAPACITY*len(FIELDS)*2+12


def instrument(source,child_map,no_driver=False):
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(
  r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',child_map.read_text(),re.M|re.I)}
 data=symbols['_runtime_error'][0]
 assert symbols['__curbrk'][0]==symbols['___nheapbeg'][0]==data
 marker='handler:\n save\n cld\n mov bp,sp\n';assert source.count(marker)==1
 code=r'''
 cmp word [cs:nip_seen],1
 jne .alloc_done
 cmp word [cs:exec_done],0
 jne .alloc_done
 cmp word [cs:hp_stage],1
 jb .alloc_done
 cmp byte [ss:bp+17],0x48
 je .alloc_candidate
 cmp byte [ss:bp+17],0x4a
 jne .alloc_done
.alloc_candidate:
 mov ah,0x62
 int 0x21
 cmp bx,[cs:nip_child_psp]
 jne .alloc_done
 cmp word [cs:aw_count],32
 jb .alloc_record
 inc word [cs:aw_overflow]
 jmp .alloc_done
.alloc_record:
 mov ax,[cs:aw_count]
 mov cx,26
 mul cx
 mov di,aw_records
 add di,ax
 mov [cs:aw_pending],di
 inc word [cs:aw_count]
 mov ax,[cs:hp_stage]
 mov [cs:di],ax
 xor ax,ax
 mov al,[ss:bp+17]
 mov [cs:di+2],ax
 mov ax,[ss:bp+14]
 mov [cs:di+4],ax
 mov ax,[ss:bp]
 mov [cs:di+6],ax
 mov ax,[ss:bp+20]
 mov [cs:di+8],ax
 mov ax,[ss:bp+22]
 mov [cs:di+10],ax
 mov ax,[ss:bp+2]
 mov [cs:di+12],ax
 mov ax,bx
 mov [cs:di+24],ax
 add ax,0x10+CHILD_DATA
 mov es,ax
 mov ax,[es:CHILD_CURBRK]
 mov [cs:di+14],ax
 mov ax,[es:CHILD_NHEAP]
 mov [cs:di+16],ax
 restore
 pushf
 call far [cs:old21]
 save
 mov bp,sp
 mov di,[cs:aw_pending]
 mov ax,[ss:bp+16]
 mov [cs:di+18],ax
 mov ax,[ss:bp+14]
 mov [cs:di+20],ax
 mov ax,[ss:bp+18]
 mov [ss:bp+24],ax
 and ax,1
 mov [cs:di+22],ax
 restore
 iret
.alloc_done:
'''
 for n,v in dict(CHILD_DATA=data,CHILD_CURBRK=symbols['__curbrk'][1],CHILD_NHEAP=symbols['___nheapbeg'][1]).items():
  code=code.replace(n,str(v))
 if no_driver:code=code.replace('nip_seen','nd_seen').replace('nip_child_psp','nd_child_psp')
 source=source.replace(marker,marker+code)
 assert source.count('sample_end:')==1
 source=source.replace('sample_end:','aw_count: dw 0\naw_overflow: dw 0\naw_records: times 32*26 db 0\naw_service: times 6 dw 0\nsample_end:\naw_pending: dw 0')
 if '_notice_service_probe' in symbols:
  assert symbols['_notice_service_probe'][0]==data
  marker=' inc word [cs:'+('nd_exit_seen' if no_driver else 'nip_exit_seen')+']\n';assert source.count(marker)==1
  code=''.join(' mov ax,[es:'+str(symbols['_notice_service_probe'][1]+i*2)+']\n mov [cs:aw_service+'+str(i*2)+'],ax\n' for i in range(6))
  source=source.replace(marker,marker+code)
 return source


def read(raw):
 count,overflow=struct.unpack_from('<2H',raw)
 assert len(raw)==BYTES and count<=CAPACITY
 return dict(overflow=overflow,records=[dict(zip(FIELDS,struct.unpack_from('<13H',raw,4+i*26))) for i in range(count)],
  service=dict(zip(('origin','status','ds','ss','flags','uart_status'),struct.unpack_from('<6H',raw,BYTES-12))))
