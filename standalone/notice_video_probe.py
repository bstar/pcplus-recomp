"""Passive entry-only INT10 witness for the owned Help DOS fixture."""
import re,struct
FIELDS=['ax','bx','cx','dx','si','di','bp','ds','es','ss','sp','ip','cs','flags','stage']
CAPACITY=64
PARENT_FIELDS=['connection_state','terminal_program_pending','terminal_program_active','terminal_menu_pending',
 'terminal_macro_active','terminal_deferred_count','terminal_quit','terminal_ansi_wait_active',
 '_redisplay_active','_command_menu_active','uart_rx_count','uart_tx_paused','_terminal_chat_buffered']
KEY_FIELDS=['function','key','ticks_low','ticks_high','exec_done','caller_ip','caller_cs','caller_flags']
KEY_BYTES=4+64*len(KEY_FIELDS)*2
BIOS_FIELDS=['key_head','key_tail','key_word','ticks_low','ticks_high','pic1_mask','ss','sp']
ROWS=4+CAPACITY*len(FIELDS)*2+2
STATE_END=ROWS+320+2*(len(PARENT_FIELDS)+len(BIOS_FIELDS))
BYTES=STATE_END+KEY_BYTES


def instrument(source,child_map,no_driver=False,parent_map=None):
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(
  r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',child_map.read_text(),re.M|re.I)}
 code=r'''
vw_install:
 save
 mov ax,0x3516
 int 0x21
 mov [cs:vw_old16],bx
 mov [cs:vw_old16+2],es
 push cs
 pop ds
 mov dx,vw_key_handler
 mov ax,0x2516
 int 0x21
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
vw_key_handler:
 save
 cld
 mov bp,sp
 cmp word [cs:exec_seen],1
 jne .done
 mov ax,[ss:bp+16]
 and ax,0xff00
 cmp ax,0
 je .read
 cmp ax,0x1000
 jne .done
.read:
 mov dx,ax
 mov ax,0x40
 mov es,ax
 mov bx,[es:0x1a]
 cmp bx,[es:0x1c]
 je .done
 cmp bx,0x1e
 jb .done
 cmp bx,0x3e
 jae .done
 cmp word [cs:vw_key_count],64
 jb .record
 inc word [cs:vw_key_overflow]
 jmp .done
.record:
 mov ax,[cs:vw_key_count]
 mov cx,16
 mul cx
 mov di,vw_keys
 add di,ax
 inc word [cs:vw_key_count]
 mov dx,[ss:bp+16]
 and dx,0xff00
 mov [cs:di],dx
 mov ax,[es:bx]
 mov [cs:di+2],ax
 mov ax,[es:0x6c]
 mov [cs:di+4],ax
 mov ax,[es:0x6e]
 mov [cs:di+6],ax
 mov ax,[cs:exec_done]
 mov [cs:di+8],ax
 mov ax,[ss:bp+20]
 mov [cs:di+10],ax
 mov ax,[ss:bp+22]
 mov [cs:di+12],ax
 mov ax,[ss:bp+24]
 mov [cs:di+14],ax
.done:
 restore
 jmp far [cs:vw_old16]
vw_old16: dw 0,0
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
 mov ax,[cs:parent_ds]
 mov es,ax
PARENT_STATE_READS
 mov ax,0x40
 mov es,ax
 mov bx,[es:0x1a]
 mov [cs:vw_bios],bx
 mov ax,[es:0x1c]
 mov [cs:vw_bios+2],ax
 mov ax,0xffff
 cmp bx,0x1e
 jb .no_key
 cmp bx,0x3e
 jae .no_key
 mov ax,[es:bx]
.no_key:
 mov [cs:vw_bios+4],ax
 mov ax,[es:0x6c]
 mov [cs:vw_bios+6],ax
 mov ax,[es:0x6e]
 mov [cs:vw_bios+8],ax
 xor ax,ax
 in al,0x21
 mov [cs:vw_bios+10],ax
 mov ax,ss
 mov [cs:vw_bios+12],ax
 mov [cs:vw_bios+14],sp
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
 assert parent_map is not None
 parent={n:(int(s,16),int(o,16)) for s,o,n in re.findall(
  r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',parent_map.read_text(),re.M|re.I)}
 assert all(parent[n][0]==parent['terminal_program_active'][0] for n in PARENT_FIELDS)
 reads=''.join(' mov ax,[es:'+str(parent[n][1])+']\n mov [cs:vw_parent_state+'+str(i*2)+'],ax\n' for i,n in enumerate(PARENT_FIELDS))
 code=code.replace('PARENT_STATE_READS',reads)
 code=code.replace('CHILD_DATA',str(symbols['_runtime_error'][0]))
 if no_driver:code=code.replace('nip_seen','nd_seen').replace('nip_child_psp','nd_child_psp')
 marker=' mov [old21],bx\n';assert source.count(marker)==1
 source=source.replace(marker,' call vw_install\n'+marker)
 marker='timer:\n save\n';assert source.count(marker)==1
 source=source.replace(marker,marker+' call vw_parent_tick\n')
 marker=' mov dx,filename\n xor cx,cx\n mov ah,0x3c\n';assert source.count(marker)==1
 restore=' push ds\n mov es,[cs:report_source]\n mov dx,[es:vw_old16]\n mov ds,[es:vw_old16+2]\n mov ax,0x2516\n int 0x21\n pop ds\n push ds\n mov es,[cs:report_source]\n mov dx,[es:vw_old10]\n mov ds,[es:vw_old10+2]\n mov ax,0x2510\n int 0x21\n pop ds\n'
 source=source.replace(marker,restore+marker)
 source=source.replace('resident_end:',code+'\nresident_end:')
 return source.replace('sample_end:','vw_count: dw 0\nvw_overflow: dw 0\nvw_records: times 64*30 db 0\nvw_parent_seen: dw 0\nvw_parent_rows: times 320 db 0\nvw_parent_state: times '+str(len(PARENT_FIELDS))+' dw 0\nvw_bios: times 8 dw 0\nvw_key_count: dw 0\nvw_key_overflow: dw 0\nvw_keys: times 64*16 db 0\nsample_end:')


def read(raw):
 assert len(raw)==BYTES
 key_count,key_overflow=struct.unpack_from('<2H',raw,STATE_END);assert key_count<=64
 count,overflow=struct.unpack_from('<2H',raw);assert count<=CAPACITY
 return dict(key_overflow=key_overflow,keys=[dict(zip(KEY_FIELDS,struct.unpack_from('<8H',raw,STATE_END+4+i*16))) for i in range(key_count)],overflow=overflow,records=[dict(zip(FIELDS,struct.unpack_from('<15H',raw,4+i*30))) for i in range(count)],
  parent_seen=struct.unpack_from('<H',raw,ROWS-2)[0],parent_rows_hex=raw[ROWS:ROWS+320].hex(),
  parent_rows=[raw[ROWS:ROWS+160:2].decode('cp437'),raw[ROWS+160:ROWS+320:2].decode('cp437')],
  parent_state=dict(zip(PARENT_FIELDS,struct.unpack_from('<'+str(len(PARENT_FIELDS))+'H',raw,ROWS+320))),
  bios=dict(zip(BIOS_FIELDS,struct.unpack_from('<8H',raw,ROWS+320+len(PARENT_FIELDS)*2))))
