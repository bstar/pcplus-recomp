"""Owned BIOS-key probe: actual popup, two help pages, paused timer and restore."""
from notice_input_fault_probe import instrument as child_input
WORDS=['stage','seed_failures','help_seen','serial_seen','held_ticks','frame_equal','cursor_equal']
BYTES=len(WORDS)*2+12000
def instrument(source,child_map,fault=False,no_driver=False):
    if no_driver:
        assert not fault
        from notice_input_no_driver_probe import instrument as absent
        source=absent(source,child_map)
        old=' mov ax,0x0500\n mov cx,0x1c0d\n int 0x16\n xor ah,ah\n mov [cs:nd_seed_status],ax\n'
        assert source.count(old)==1
        source=source.replace(old,' mov word [cs:nd_seed_status],0\n')
    else:source=child_input(source,child_map)
    marker=' call no_driver_tick\n' if no_driver else ' call child_input_tick\n';assert source.count(marker)==1
    source=source.replace(marker,marker+' call help_tick\n')
    code=r'''
help_seed:
 mov ax,0x0500
 int 0x16
 or al,al
 jz .done
 inc word [cs:hp_seed_failures]
.done:
 ret
help_copy:
 push cs
 pop ds
 mov ax,0xb800
 mov es,ax
 xor si,si
 mov cx,4000
.byte:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .byte
 ret
help_tick:
 push ds
 cmp word [cs:nip_seen],1
 jne .done
 cmp word [cs:exec_done],0
 jne .done
 mov ax,0xb800
 mov es,ax
 mov ax,[cs:hp_stage]
 cmp ax,0
 je .popup
 cmp ax,1
 je .help
 cmp ax,2
 je .serial
 cmp ax,3
 je .restored
 jmp .done
.popup:
 cmp word [es:1662],0x7050
 jne .done
 cmp word [es:1696],0x702e
 jne .done
 mov di,hp_before
 call help_copy
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x50]
 mov [cs:hp_cursor],ax
 mov ax,[es:0x60]
 mov [cs:hp_shape],ax
 mov cx,0x2c00
 call help_seed
 inc word [cs:hp_stage]
 jmp .done
.help:
 cmp word [es:166],0x1f50
 jne .done
 cmp word [es:176],0x1f73
 jne .done
 cmp word [es:486],0x1e45
 jne .done
 cmp word [es:3686],0x1f4c
 jne .done
 inc word [cs:hp_held_ticks]
 cmp word [cs:hp_held_ticks],90
 jb .done
 inc word [cs:hp_help_seen]
 mov di,hp_help
 call help_copy
 mov cx,0x4d00
 call help_seed
 inc word [cs:hp_stage]
 jmp .done
.serial:
 cmp word [es:486],0x1e53
 jne .done
 cmp word [es:488],0x1e45
 jne .done
 inc word [cs:hp_serial_seen]
 mov di,hp_serial
 call help_copy
 mov cx,0x011b
 call help_seed
 inc word [cs:hp_stage]
 jmp .done
.restored:
 cmp word [es:1662],0x7050
 jne .done
 cmp word [es:1696],0x702e
 jne .done
 push cs
 pop ds
 xor si,si
 mov di,hp_before
 mov cx,4000
.compare:
 mov al,[es:si]
 cmp al,[di]
 jne .done
 inc si
 inc di
 loop .compare
 inc word [cs:hp_frame_equal]
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x50]
 cmp ax,[cs:hp_cursor]
 jne .dismiss
 mov ax,[es:0x60]
 cmp ax,[cs:hp_shape]
 jne .dismiss
 inc word [cs:hp_cursor_equal]
.dismiss:
 mov cx,0x1c0d
 call help_seed
 inc word [cs:hp_stage]
.done:
 pop ds
 ret
hp_cursor: dw 0
hp_shape: dw 0
'''
    if fault:
        old=' mov cx,0x4d00\n call help_seed\n inc word [cs:hp_stage]\n'
        assert code.count(old)==1
        code=code.replace(old,' mov word [cs:hp_stage],5\n')
    if no_driver:code=code.replace('nip_seen','nd_seen')
    data=''.join('hp_'+n+': dw 0\n' for n in WORDS)+'hp_before: times 4000 db 0\nhp_help: times 4000 db 0\nhp_serial: times 4000 db 0\n'
    return source.replace('resident_end:',code+'\nresident_end:').replace('sample_end:',data+'sample_end:')
