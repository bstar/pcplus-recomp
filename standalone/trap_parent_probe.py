"""Observe caller trap handoff and invoke a map-validated retained test ISR."""
import re

MARKER = b'TRAPOBS1'

def instrument(source, parent_map, child_map, offsets, retry):
    symbols = {n:(int(s,16),int(o,16)) for s,o,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',child_map.read_text(),re.M|re.I)}
    code_seg, code_off = symbols['_aspect_exit_foreign']
    data_seg, hits = symbols['_aspect_exit_hits']
    # This prefix leaves the existing end-relative retry/mouse record layouts
    # intact, and does not change the fixed JFT/owner records at the front.
    old = 'before_history: times 72 db 0'
    assert source.count(old) == 1
    source = source.replace(old,"trap_marker: db 'TRAPOBS1'\ntrap_snapshot: times 16 dw 0\n"+old)
    old = ' mov di,before_history\n call copy_history'
    assert source.count(old) == 1
    source = source.replace(old,old+'\n call trap_snapshot_caller')
    old = ' ; This known source-owned callback is the only active probe operation.\n int 0x1b'
    assert source.count(old) == 1
    source = source.replace(old,' call trap_invoke_known')
    if retry:
        old = ''' ; Invoke only the known retained test ISR, after checking its exact address.
 cmp ax,[retained_vector_seg]
 jne .retained
 mov ax,[es:0x1b*4]
 cmp ax,[retained_vector_off]
 jne .retained
 int 0x1b'''
        assert source.count(old) == 1
        source = source.replace(old,' call trap_invoke_known')
    code = r'''
trap_snapshot_caller:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov es,[parent_ds]
 mov ax,[es:PHASE]
 mov [trap_snapshot],ax
 mov si,ORIGINALS
 mov di,trap_snapshot+2
 mov cx,6
.originals:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .originals
 mov ax,[es:FLAG]
 mov [di],ax
 add di,2
 mov ax,[es:CHILD]
 mov [trap_snapshot+30],ax
 xor ax,ax
 mov es,ax
 mov si,trap_indices
 mov cx,3
.vectors:
 lodsw
 mov bx,ax
 mov ax,[es:bx]
 mov [di],ax
 mov ax,[es:bx+2]
 mov [di+2],ax
 add di,4
 loop .vectors
 mov ax,0x3300
 int 0x21
 xor dh,dh
 mov [di],dx
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 ret
; This test observer neither changes IVT entries nor repairs product state.
; It calls only the captured exact linked test ISR in an owned retained MCB.
trap_invoke_known:
 pushf
 push ax
 push bx
 push dx
 push es
 mov ax,[cs:retained_psp]
 cmp ax,0x10
 jb .done
 mov bx,ax
 dec ax
 mov es,ax
 cmp byte [es:0],'M'
 je .owner
 cmp byte [es:0],'Z'
 jne .done
.owner:
 cmp [es:1],bx
 jne .done
 mov dx,[es:3]
 cmp dx,[cs:retained_paras_before]
 jne .done
 add dx,bx
 jc .done
 add bx,0x10+CODE_SEG
 jc .done
 cmp bx,[cs:retained_vector_seg]
 jne .done
 cmp word [cs:retained_vector_off],CODE_OFF
 jne .done
 add bx,CODE_OFF/16
 jc .done
 cmp bx,dx
 jae .done
 mov bx,[cs:retained_psp]
 add bx,0x10+DATA_SEG+HITS/16
 jc .done
 cmp bx,dx
 jae .done
 pushf
 call far [cs:retained_vector_off]
.done:
 pop es
 pop dx
 pop bx
 pop ax
 popf
 ret
trap_indices: dw 0x1b*4,0x23*4,0x24*4
'''
    values = dict(PHASE=offsets['terminal_trap_phase'], ORIGINALS=offsets['terminal_trap_originals'],
        FLAG=offsets['terminal_trap_flag'], CHILD=offsets['terminal_trap_child'],
        CODE_SEG=code_seg,CODE_OFF=code_off,DATA_SEG=data_seg,HITS=hits)
    for name,value in values.items():
        code = re.sub(r'\b'+name+r'\b',str(value),code)
    return source.replace('resident_end:',code+'\nresident_end:')
