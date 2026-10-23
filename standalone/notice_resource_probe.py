"""Owned BIOS sequence verifies live resource search, F3, no-match and cancel."""
from notice_help_probe import instrument as basic
WORDS=['find_seen','next_line_seen','next_topic_seen','not_found_seen','canceled_seen']
BYTES=len(WORDS)*2+8000
def instrument(source,child_map,no_driver=False,bad=False):
    source=basic(source,child_map,no_driver=no_driver)
    if bad:
        source=source.replace('cmp word [es:486],0x1e45','cmp word [es:486],0x1e48').replace('cmp word [es:3686],0x1f4c','cmp word [es:3686],0x1f45')
        old=' mov cx,0x4d00\n call help_seed\n inc word [cs:hp_stage]\n'
        assert source.count(old)==1
        return source.replace(old,' mov cx,0x011b\n call help_seed\n mov word [cs:hp_stage],3\n')
    old=' cmp ax,3\n je .restored\n jmp .done';assert source.count(old)==1
    source=source.replace(old,''' cmp ax,3
 je .restored
 cmp ax,6
 je .resource_find
 cmp ax,7
 je .resource_line
 cmp ax,8
 je .resource_topic
 cmp ax,9
 je .resource_none
 cmp ax,10
 je .resource_cancel
 jmp .done''')
    old=' mov cx,0x011b\n call help_seed\n inc word [cs:hp_stage]\n jmp .done\n.restored:'
    assert source.count(old)==1
    emit=''.join(' mov cx,'+str(key)+'\n call help_seed\n' for key in [0x352f,0x2d78,0x326d,0x186f,0x2064,0x1265,0x326d,0x1c0d])
    source=source.replace(old,emit+' mov word [cs:hp_stage],6\n jmp .done\n'+'''
.resource_find:
 cmp word [es:486],0x1e52
 jne .done
 cmp word [es:806],0x1752
 jne .done
 inc word [cs:rp_find_seen]
 mov di,rp_first
 call help_copy
 mov cx,0x3d00
 call help_seed
 mov word [cs:hp_stage],7
 jmp .done
.resource_line:
 cmp word [es:806],0x1764
 jne .done
 cmp word [es:808],0x176f
 jne .done
 inc word [cs:rp_next_line_seen]
 mov cx,0x3d00
 call help_seed
 mov word [cs:hp_stage],8
 jmp .done
.resource_topic:
 cmp word [es:486],0x1e53
 jne .done
 cmp word [es:806],0x1743
 jne .done
 inc word [cs:rp_next_topic_seen]
 mov di,rp_second
 call help_copy
'''+''.join(' mov cx,'+str(key)+'\n call help_seed\n' for key in [0x352f]+[0x2c7a]*7+[0x1c0d])+'''
 mov word [cs:hp_stage],9
 jmp .done
.resource_none:
 cmp word [es:3686],0x1f4e
 jne .done
 cmp word [es:3688],0x1f6f
 jne .done
 inc word [cs:rp_not_found_seen]
'''+''.join(' mov cx,'+str(key)+'\n call help_seed\n' for key in [0x352f,0x326d,0x1c0d,0x011b])+'''
 mov word [cs:hp_stage],10
 jmp .done
.resource_cancel:
 cmp word [es:3686],0x1f4c
 jne .done
 inc word [cs:rp_canceled_seen]
 mov cx,0x011b
 call help_seed
 mov word [cs:hp_stage],3
 jmp .done
.restored:''')
    data=''.join('rp_'+n+': dw 0\n' for n in WORDS)+'rp_first: times 4000 db 0\nrp_second: times 4000 db 0\n'
    return source.replace('sample_end:',data+'sample_end:')
