"""Passive BIOS-tick speaker gate sampling and child exit-state observation."""


def instrument(source, symbols):
    old = 'sample_end:\nowner_table:'
    assert source.count(old) == 1
    source = source.replace(old, '''speaker_on_ticks: dw 0
speaker_edges: dw 0
speaker_last: dw 0
speaker_at_exit: dw 0xffff
speaker_owned_at_exit: dw 0xffff
alarm_duration_at_exit: dw 0xffff
speaker_exit_abi: dw 0
sample_end:
owner_table:''')
    old = 'timer:\n save\n cld\n'
    assert source.count(old) == 1
    source = source.replace(old, old + ''' cmp word [cs:exec_seen],1
 jne .speaker_sample_done
 cmp word [cs:exec_done],0
 jne .speaker_sample_done
 in al,0x61
 xor ah,ah
 and ax,3
 cmp ax,3
 jne .speaker_not_on
 inc word [cs:speaker_on_ticks]
.speaker_not_on:
 cmp ax,[cs:speaker_last]
 je .speaker_sample_done
 inc word [cs:speaker_edges]
 mov [cs:speaker_last],ax
.speaker_sample_done:
''')
    old = ' push cs\n pop ds\n inc word [child_exits]'
    assert source.count(old) == 1
    sample = ''' in al,0x61
 xor ah,ah
 and ax,3
 mov [cs:speaker_at_exit],ax
 mov ax,[ss:SPEAKER_OWNED]
 mov [cs:speaker_owned_at_exit],ax
 mov ax,[ss:ALARM_DURATION]
 mov [cs:alarm_duration_at_exit],ax
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne .speaker_exit_sampled
 mov word [cs:speaker_exit_abi],1
.speaker_exit_sampled:
'''
    for token, name in (('SPEAKER_OWNED', '_speaker_owned'),
                        ('ALARM_DURATION', 'alarm_duration')):
        sample = sample.replace(token, str(symbols[name][1]))
    return source.replace(old, sample + old)
