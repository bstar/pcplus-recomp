"""Observe child callback admission/retirement without injecting a key event."""
from notice_input_parent_probe import instrument as active,WORDS,BYTES

def instrument(source,child_map):
    source=active(source,child_map,2)
    begin=' mov word [cs:nip_event],2\n push ds\n'
    end=' pop ds\n mov ax,[cs:nip_child_psp]\n'
    assert source.count(begin)==source.count(end)==1
    start=source.index(begin);finish=source.index(end,start)+len(' pop ds\n')
    source=source[:start]+' mov word [cs:nip_event],0\n'+source[finish:]
    assert 'call far [cs:nip_callback_off]' not in source
    return source
