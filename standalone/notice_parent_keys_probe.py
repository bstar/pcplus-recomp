"""Deliver fixture BIOS keys only after the observed child returns to its parent."""
import re

def instrument(source,parent_map,no_driver=False,reference=False):
 symbols={n:int(o,16) for _,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',parent_map.read_text(),re.M|re.I)}
 code=r'''
pk_tick:
 cmp word [cs:exec_done],1
 jne .done
 mov ax,ss
 cmp ax,[cs:parent_ds]
 jne .done
 mov es,ax
 cmp word [cs:pk_stage],0
 jne .returned
 ; Automatic LOGIN returns without a PROGRAM acknowledgement prompt.
 ; Wait for its owner to release; never send an extra Space to the BBS.
 cmp word [es:PROGRAM_ACTIVE],0
 jne .done
 inc word [cs:pk_stage]
 jmp .done
.returned:
 cmp word [es:PROGRAM_ACTIVE],0
 jne .done
 cmp word [cs:pk_stage],1
 jne .browser
 mov cx,BROWSER_KEY
 call pk_seed
 jc .done
 inc word [cs:pk_stage]
 jmp .done
.browser:
 cmp word [cs:pk_stage],2
 jne .type
BROWSER_COMPLETE
 inc word [cs:pk_stage]
 jmp .done
.type:
 cmp word [es:MENU_ACTIVE],0
 jne .done
 cmp word [es:REDISPLAY_ACTIVE],0
 jne .done
 inc word [cs:pk_ticks]
 cmp word [cs:pk_ticks],4
 jb .done
 mov word [cs:pk_ticks],0
 mov bx,[cs:pk_index]
 cmp bx,10
 jae .exit
 mov cx,[cs:pk_keys+bx]
 call pk_seed
 jc .done
 add word [cs:pk_index],2
 jmp .done
.exit:
 cmp bx,26
 jae .done
 add word [cs:pk_index],2
 cmp bx,24
 jne .done
 mov cx,0x2d00
 call pk_seed
.done:
 ret
pk_seed:
 ; Never replace queued input or bypass the actual BIOS reader.
 push es
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x1a]
 cmp ax,[es:0x1c]
 pop es
 jne .busy
 push es
 mov ax,0x0500
 int 0x16
 pop es
 or al,al
 jnz .busy
 clc
 ret
.busy:
 stc
 ret
pk_stage: dw 0
pk_ticks: dw 0
pk_index: dw 0
pk_keys: dw 0x1372,0x1265,0x1e61,0x2064,0x1579
'''
 if no_driver:
  browser=' cmp word [es:MENU_ACTIVE],1\n jne .done\n mov cx,0x011b\n call pk_seed\n jc .done\n'
 else:browser=' cmp word [cs:mp_menu_stage],2\n jne .done\n'
 code=code.replace('BROWSER_COMPLETE',browser)
 for token,name in [('PROGRAM_ACTIVE','terminal_program_active'),('MENU_ACTIVE','_command_menu_active'),('REDISPLAY_ACTIVE','_redisplay_active')]:code=code.replace(token,str(symbols[name]))
 code=code.replace('BROWSER_KEY','0x2960' if reference else '0x2c00')
 marker='timer:\n save\n';assert source.count(marker)==1
 return source.replace(marker,marker+' call pk_tick\n').replace('resident_end:',code+'\nresident_end:')
