"""Passive key-consumption/owner diagnostic with the existing TSR footprint.

Eight video notice slots replace sixteen; sixteen owner records share the
freed diagnostic space. Product capacities, recipe and keyboard producer stay
unchanged. The observer chains INT16 without consuming or changing a key.
"""
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
from product_inputs import ROOT, sha
sys.path.insert(0,str(ROOT/'standalone'))
from carrier_notice_watch import SAMPLER

FIELDS=['tick','key','caller_ip','caller_cs','read_ax','parent_ds',
        'terminal_parser_active','terminal_transfer_active','terminal_transfer_pending',
        'terminal_program_active','terminal_program_pending','_redisplay_active',
        'connection_state','terminal_ansi_wait_active','terminal_menu_pending','_command_menu_active']


def build(binary,out):
    binary=binary.resolve();out.mkdir(parents=True,exist_ok=False)
    m=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==m['binary_sha256']
    for name,digest in m['sources'].items():assert sha(ROOT/name)==digest,name
    listing=binary.with_name('terminal.map').read_text()
    symbols={n:(int(o,16),int(s,16)) for s,o,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    ds=int(re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I)[1],16)
    assert all(symbols[n][1]==ds for n in FIELDS[6:])
    irq,irqseg=symbols['uart_receive_interrupt'];assert irqseg==0
    raw=binary.read_bytes();head=struct.unpack_from('<14H',raw);signature=raw[head[4]*16+irq:head[4]*16+irq+4]
    for i in range(head[3]):
        off,seg=struct.unpack_from('<HH',raw,head[12]+i*4)
        assert not irq-1<=seg*16+off<irq+4
    base=SAMPLER.replace('mov cx,4000','mov cx,8000')
    for off in (0,1,3,4):base=base.replace(hex(0x3f8+off),hex(0x3e8+off))
    (out/'baseline.asm').write_text(base+"\ndb 'FOOTBASE'\ndw resident_end\n")
    subprocess.run(['nasm','-fbin',str(out/'baseline.asm'),'-o',str(out/'baseline.com')],check=True)
    baseline=(out/'baseline.com').read_bytes();assert baseline[-10:-2]==b'FOOTBASE'
    retained_end=struct.unpack('<H',baseline[-2:])[0]
    source=base.replace('old_vector: dw 0,0','old_vector: dw 0,0\nold_keyboard_vector: dd 0')
    source=source.replace('frames: times 16*160 db 0','frames: times 8*160 db 0\ntrace_meta: dw 0x4b54,0,0,0\ntrace_records: times 16*32 db 0')
    assert source.count(' cmp bx,16\n')==1
    source=source.replace(' cmp bx,16\n',' cmp bx,8\n')
    source=source.replace('.observed:\n','.observed:\n'+r'''
 cmp byte [es:3842],'R'
 jne .trace_carrier
 cmp byte [es:3850],'a'
 je .trace_on
 jmp .trace_ready
.trace_carrier:
 cmp byte [es:3858],'l'
 jne .trace_ready
.trace_on:
 mov word [trace_meta+4],1
.trace_ready:
''')
    reads=''.join(f' mov ax,[es:{symbols[n][0]}]\n stosw\n' for n in FIELDS[6:])
    # STOSW targets our own CS data; ES instead addresses parent data for reads,
    # so emit explicit DS:[DI] writes rather than changing caller ownership.
    reads=reads.replace(' stosw\n',' mov [di],ax\n add di,2\n')
    sig0,sig1=struct.unpack('<2H',signature)
    keys=r'''
key_handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 mov bp,sp
 cmp ah,0
 je .read
 cmp ah,0x10
 jne .done
.read:
 push cs
 pop ds
 cmp word [trace_meta+4],1
 jne .done
 cmp word [trace_meta+2],16
 jb .room
 inc word [trace_meta+6]
 jmp .done
.room:
 xor ax,ax
 mov es,ax
 cmp word [es:0x34],IRQ_OFF
 jne .done
 mov ax,[es:0x36]
 mov es,ax
 cmp word [es:IRQ_OFF],SIG0
 jne .done
 cmp word [es:IRQ_OFF+2],SIG1
 jne .done
 add ax,PARENT_DS
 cmp ax,0xa000
 jae .done
 cmp ax,[ss:bp+2]
 jne .done
 mov dx,ax
 xor ax,ax
 mov es,ax
 mov bx,[es:0x41a]
 cmp bx,[es:0x41c]
 je .done
 cmp bx,0x1e
 jb .done
 cmp bx,0x3c
 ja .done
 test bl,1
 jnz .done
 mov cx,[es:bx+0x400]
 mov di,[trace_meta+2]
 shl di,1
 shl di,1
 shl di,1
 shl di,1
 shl di,1
 add di,trace_records
 mov ax,[es:0x46c]
 mov [di],ax
 mov [di+2],cx
 mov ax,[ss:bp+20]
 mov [di+4],ax
 mov ax,[ss:bp+22]
 mov [di+6],ax
 mov ax,[ss:bp+16]
 mov [di+8],ax
 mov [di+10],dx
 add di,12
 mov es,dx
OWNER_READS
 inc word [trace_meta+2]
.done:
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 jmp far [cs:old_keyboard_vector]
'''.replace('OWNER_READS',reads)
    for name,value in [('IRQ_OFF',irq),('SIG0',sig0),('SIG1',sig1),('PARENT_DS',ds)]:
        keys=keys.replace(name,str(value))
    source=source.replace('resident_end:\n',keys+f'\ntimes {retained_end}-($-$$+0x100) db 0\nresident_end:\n')
    source=source.replace('install:\n',r'''install:
 mov ax,0x3516
 int 0x21
 mov [old_keyboard_vector],bx
 mov [old_keyboard_vector+2],es
 mov dx,key_handler
 mov ax,0x2516
 int 0x21
''')
    source=source.replace(' mov dx,[es:old_vector]\n',r'''
 push es
 mov dx,[es:old_keyboard_vector]
 mov ax,[es:old_keyboard_vector+2]
 push ds
 mov ds,ax
 mov ax,0x2516
 int 0x21
 pop ds
 mov ax,0x3516
 int 0x21
 mov dx,es
 mov bp,sp
 mov ax,[ss:bp]
 mov es,ax
 cmp bx,[es:old_keyboard_vector]
 jne .keyboard_restore_bad
 cmp dx,[es:old_keyboard_vector+2]
 jne .keyboard_restore_bad
 or word [buffer+1286+4],0x8000
 pop es
 jmp .keyboard_restored
.keyboard_restore_bad:
 pop es
 jmp failed
.keyboard_restored:
 mov dx,[es:old_vector]
''')
    source=source.replace(' cmp word [es:sample],0x4e5a\n jne failed\n',r''' cmp word [es:sample],0x4e5a
 jne failed
 push es
 mov ax,0x3516
 int 0x21
 cmp bx,key_handler
 jne .keyboard_bad
 mov ax,es
 pop es
 mov dx,es
 cmp ax,dx
 jne failed
 jmp .keyboard_ok
.keyboard_bad:
 pop es
 jmp failed
.keyboard_ok:
''')
    source+="\ndb 'KEYOBS00'\ndw resident_end,handler,key_handler,sample,trace_meta,trace_records,old_keyboard_vector,old_vector\n"
    (out/'observer.asm').write_text(source)
    subprocess.run(['nasm','-fbin',str(out/'observer.asm'),'-o',str(out/'observer.com')],check=True)
    actual=(out/'observer.com').read_bytes();assert actual[-24:-16]==b'KEYOBS00'
    offsets=dict(zip(['resident_end','handler','key_handler','sample','trace_meta','trace_records','old_keyboard_vector','old_vector'],struct.unpack('<8H',actual[-16:])))
    assert offsets['resident_end']==retained_end
    report=dict(passed=True,binary_sha256=sha(binary),observer_sha256=sha(out/'observer.com'),
                retained_bytes=retained_end,retained_paragraphs=(retained_end+15)//16,
                baseline_retained_bytes=retained_end,offsets=offsets,fields=FIELDS,
                parent_ds=ds,uart_entry_offset=irq,uart_signature=signature.hex(),
                field_offsets={n:symbols[n][0] for n in FIELDS[6:]},
                source_sha256=sha(Path(__file__)),video_capacity=8,key_capacity=16,
                scope=__doc__+' Exact original resident end is padded, not merely a smaller measurement. No IRQ callback calls DOS/BIOS, reads UART registers or consumes keys. Transparency tests required separately.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    return source,report


def decode(path):
    raw=path.read_bytes();assert len(raw)==2566
    magic,count,enabled,overflow=struct.unpack_from('<4H',raw,1286)
    assert magic==0x4b54 and count<=16
    return dict(enabled=enabled&0x7fff,int16_restored=bool(enabled&0x8000),overflow=overflow,
                records=[dict(zip(FIELDS,struct.unpack_from('<16H',raw,1294+i*32))) for i in range(count)])
