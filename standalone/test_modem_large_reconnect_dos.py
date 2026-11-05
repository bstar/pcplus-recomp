#!/usr/bin/env python3
"""Actual DOS larger-height carrier loss, XOFF cleanup and same-process redial.
An owned TCP peer closes the DOSBox-X modem's socket; DCD/results are generated
by that modem. The observer reads state and supplies ordinary BIOS keys only.
No physical Boca/SPA2102, real BBS or transfer acceptance is implied.
"""
import argparse,json,re,shutil,struct,subprocess
from pathlib import Path
import test_modem_reconnect_dos as reconnect
import test_aspect_renderer_dos as renderer
import test_aspect_script_window_dos as window
from directory_fixtures import directory,prm
ROOT=renderer.ROOT;sha=renderer.sha;ESC=b'\x1b'
WORDS=['second_execs','second_done','second_exits','second_exit_code',
 'disconnected_ticks','stale_pause_seen','reconnected_ticks','final_ticks',
 'redial_key_sent','ready_keys_sent','exit_key_sent','child_pause_seen',
 'cleanup_seen','cleanup_state','cleanup_status','cleanup_program','cleanup_parser',
 'cleanup_aspect','cleanup_wait','cleanup_rows','cleanup_flow','cleanup_logical',
 'cleanup_bios_rows','cleanup_font']
EXTRA_BYTES=2*len(WORDS)+40+832

def observer(out,terminal):
 renderer.OUT=out;renderer.observer(renderer.map_offsets(terminal.parent/'terminal.map'))
 symbols=window.symbols(terminal.parent/'terminal.map');path=out/'observer.asm';text=path.read_text()
 fields=''.join(n+': dw '+('0xffff' if n=='second_exit_code' else '0')+'\n' for n in WORDS)
 fields+='second_before_jft: times 20 db 0\nsecond_after_jft: times 20 db 0\nsecond_before_owners: times 416 db 0\nsecond_after_owners: times 416 db 0\n'
 assert text.count('sample_end:\nowner_table:')==1;text=text.replace('sample_end:\nowner_table:',fields+'sample_end:\nowner_table:')
 branch='''.debug_done:
 cmp word [cs:exec_done],1
 jne .first_exec
 cmp word [cs:second_execs],0
 jne .chain
 cmp word [PROGRAM_KIND],4
 jne .chain
 cmp word [PROGRAM_ACTIVE],1
 jne .chain
 mov ax,ds
 cmp ax,[cs:parent_ds]
 jne .chain
 jmp .second_exec
.first_exec:
'''
 assert text.count('.debug_done:\n')==1;text=text.replace('.debug_done:\n',branch)
 second='''.second_exec:
 push cs
 pop ds
 inc word [second_execs]
 mov di,second_before_jft
 call copy_jft
 mov di,second_before_owners
 call copy_owners
 restore
 pushf
 call far [cs:old21]
 save
 push cs
 pop ds
 mov di,second_after_jft
 call copy_jft
 mov di,second_after_owners
 call copy_owners
 inc word [second_done]
 mov bp,sp
 mov ax,[ss:bp+18]
 mov [ss:bp+24],ax
 restore
 iret
'''
 assert text.count('.exit_check:\n')==1;text=text.replace('.exit_check:\n',second+'.exit_check:\n')
 second_exit=''' cmp byte [ss:bp+17],0x4c
 jne .chain
 cmp word [cs:exec_done],1
 jne .first_exit
 cmp word [cs:second_execs],1
 jne .chain
 cmp word [cs:second_done],0
 jne .chain
 mov al,[ss:bp+16]
 xor ah,ah
 mov [cs:second_exit_code],ax
 inc word [cs:second_exits]
 jmp .chain
.first_exit:
'''
 old=' cmp byte [ss:bp+17],0x4c\n jne .chain\n';assert text.count(old)==1;text=text.replace(old,second_exit)
 timer='''timer:
 save
 cld
 cmp word [cs:exec_seen],1
 jne .reconnect_done
 cmp word [cs:exec_done],0
 jne .parent
 mov ax,[cs:parent_psp]
 add ax,RENDER_CS+0x10
 mov es,ax
 mov ax,[es:CHILD_DS]
 or ax,ax
 jz .reconnect_done
 mov es,ax
 cmp word [es:CHILD_PAUSED],0
 je .reconnect_done
 mov word [cs:child_pause_seen],1
 jmp .reconnect_done
.parent:
 mov ax,[cs:parent_ds]
 mov dx,ss
 cmp ax,dx
 jne .reconnect_done
 mov es,ax
 cmp word [cs:second_done],1
 je .after_second
 cmp word [es:STATE],0
 jne .reconnect_done
 cmp word [es:STATUS],6
 jne .reconnect_done
 inc word [cs:disconnected_ticks]
 cmp word [es:PAUSED],0
 je .redial
 mov word [cs:stale_pause_seen],1
.redial:
 cmp word [cs:redial_key_sent],0
 jne .reconnect_done
 cmp word [cs:disconnected_ticks],36
 jb .reconnect_done
 mov si,redial_keys
 mov di,4
.redial_queue:
 mov cx,[cs:si]
 mov ah,5
 int 0x16
 add si,2
 dec di
 jnz .redial_queue
 mov word [cs:redial_key_sent],1
 jmp .reconnect_done
.after_second:
 cmp word [es:STATE],6
 jne .offline
 inc word [cs:reconnected_ticks]
 cmp word [cs:ready_keys_sent],0
 jne .reconnect_done
 cmp word [cs:reconnected_ticks],36
 jb .reconnect_done
 mov si,ready_keys
 mov di,5
.ready:
 mov cx,[cs:si]
 mov ah,5
 int 0x16
 add si,2
 dec di
 jnz .ready
 mov word [cs:ready_keys_sent],1
 jmp .reconnect_done
.offline:
 cmp word [es:STATE],0
 jne .reconnect_done
 cmp word [es:STATUS],6
 jne .reconnect_done
 inc word [cs:final_ticks]
 mov word [cs:cleanup_seen],1
 mov si,cleanup_offsets
 mov di,cleanup_state
 mov cx,9
.cleanup:
 mov bx,[cs:si]
 mov ax,[es:bx]
 mov [cs:di],ax
 add si,2
 add di,2
 loop .cleanup
 push es
 mov ax,0x40
 mov es,ax
 xor ax,ax
 mov al,[es:0x84]
 inc ax
 mov [cs:cleanup_bios_rows],ax
 mov ax,[es:0x85]
 mov [cs:cleanup_font],ax
 pop es
 cmp word [cs:exit_key_sent],0
 jne .reconnect_done
 cmp word [cs:final_ticks],36
 jb .reconnect_done
 mov cx,0x2d00
 mov ah,5
 int 0x16
 or al,al
 jnz .reconnect_done
 mov word [cs:exit_key_sent],1
.reconnect_done:
'''
 # Use the selected child map; never infer a DS-relative child field from the
 # parent's layout or write modem/renderer state to manufacture a transition.
 child=window.symbols(observer.runner.parent/'ASPECT.map')
 for token,value in [('RENDER_CS',symbols['render_child_ds'][0]),('CHILD_DS',symbols['render_child_ds'][1]),('CHILD_PAUSED',child['uart_tx_paused'][1]),('STATE',symbols['connection_state'][1]),('STATUS',symbols['connection_status'][1]),('PAUSED',symbols['uart_tx_paused'][1])]:timer=timer.replace(token,str(value))
 assert text.count('timer:\n save\n cld\n')==1;text=text.replace('timer:\n save\n cld\n',timer)
 cleanup=['connection_state','connection_status','terminal_program_active','terminal_parser_active','terminal_aspect_active','terminal_ansi_wait_active','ui_window_rows','ui_flow_suppressed','csi_row_count']
 # Original Alt-D is the directory viewer. Use real user keys through the
 # reference, its backtick command browser, Connection and Dial selected target.
 data='redial_keys: dw 0x2c00,0x2960,0x4d00,0x2064\nready_keys: dw 0x1372,0x1265,0x1e61,0x2064,0x1579\ncleanup_offsets: dw '+','.join(str(symbols[n][1]) for n in cleanup)+'\n'
 text=text.replace('resident_end:\nstart:',data+'resident_end:\nstart:')
 for token,name in [('PROGRAM_KIND','terminal_program_kind'),('PROGRAM_ACTIVE','terminal_program_active')]:text=text.replace(token,str(symbols[name][1]))
 path.write_text(text);subprocess.run(['nasm','-fbin',str(path),'-o',str(out/'RENDER.COM')],check=True)
 return (out/'RENDER.COM').read_bytes()

def main():
 p=argparse.ArgumentParser(description=__doc__);selection=p.add_mutually_exclusive_group(required=True);selection.add_argument('--build',type=Path);selection.add_argument('--terminal',type=Path,help='Normal source-built parent with explicit saved display preferences');p.add_argument('--runner',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--rows',type=int,choices=[25,28,43,50],required=True);p.add_argument('--profile',type=int,choices=[4,6],required=True);p.add_argument('--flow',choices=['soft','both'],default='both');a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 terminal=(a.terminal if a.terminal else a.build/str(a.rows)/'TERMINAL.EXE').resolve();runner=a.runner.resolve();inputs={}
 tm=json.loads((terminal.parent/'manifest.json').read_text());assert tm['experimental_row_notices']
 if a.terminal:assert not tm['diagnostic_session_rows_probe'] and tm['experimental_display_startup']
 else:assert tm['diagnostic_session_rows_probe']==a.rows
 for binary in [terminal,runner]:
  manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256'] and not manifest.get('original_inputs',[])
  for name,h in manifest['sources'].items():
   rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] not in ('build','analysis','original','originals') and rel.suffix.lower() not in ('.exe','.com','.img','.prm','.dir')
   assert sha(ROOT/name)==h,name
  inputs[str(binary.relative_to(ROOT))]=sha(binary);inputs[str((binary.parent/'manifest.json').relative_to(ROOT))]=sha(binary.parent/'manifest.json')
 observer.runner=runner;compiled=observer(out,terminal)
 app=out/'application';app.mkdir();shutil.copyfile(terminal,app/'TERMINAL.EXE');shutil.copyfile(runner,app/'ASPECT.EXE')
 events=[];peer=reconnect.adapter(out,events,False,snapshot_bytes=8000,cycles=12000);peer.BINARY=app/'TERMINAL.EXE'
 script='proc main\nwaitfor "LOGIN:" 5\nset duplex full\nwhen disconnect transmit "^MAT^M"\ntransmit "KEYREADY"\nwaitfor "END" 30\nif waitfor\ntransmit "SECONDOK"\nfopen 5 "SECOND.OK" "wb"\nfputs 5 "RECONNECTED"\nfclose 5\nendif\nendproc\n'
 payload=bytearray(directory(profile=a.profile));payload[302:311]=b'LOGIN\0\0\0\0'
 settings=bytearray(prm(port=3,soft=1,hard=int(a.flow=='both')));struct.pack_into('<H',settings,0x188,5);struct.pack_into('<HH',settings,0x4e4,8,4);struct.pack_into('<H',settings,0x196,0);struct.pack_into('<HH',settings,0x1bc,0,0);struct.pack_into('<H',settings,0x1e4,0)
 if a.terminal:
  for at,value in [(0x1c2,0),(0x1c8,2),(0x1ca,a.rows),(0x4ec,0)]:struct.pack_into('<H',settings,at,value)
 settings[0x79:0x79+25]=b'ATH^M'.ljust(25,b'\0')
 logical=a.rows-1;lower=f'LOWER-{a.rows}'.encode()
 banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0c'+ESC+f'[{logical};1H'.encode()+lower+ESC+b'[6n'+ESC+b'[1;1H'+ESC+b'[KFIRST BYTE SAFE'+ESC+b'[6nLOGIN:'
 files={'LOGIN.ASP':script.encode(),'LOGIN.ASX':renderer.compile_source(script),'ASPECT.EXE':runner.read_bytes(),'RENDER.COM':compiled}
 try:
  r=peer.run('run','success','p45000 a-x',directory=bytes(payload),prm=bytes(settings),profile=a.profile,files=files,com=3,irq=5,cpu='8086',timeout=75,emulated_modem=True,
   arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /I:3 /A:NETWORK',working_drive='d',observer='RENDER',accounting_delta=2,environment={'PCPLUS_TXWAIT':'2'},banner=banner)
 finally:
  folder=out/'run';(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
 raw=(folder/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw);extra=raw[-EXTRA_BYTES:];state=dict(zip(WORDS,struct.unpack_from('<'+str(len(WORDS))+'H',extra)))
 at=2*len(WORDS);second_jft=extra[at:at+20]==extra[at+20:at+40];at+=40;second_owners=extra[at:at+416]==extra[at+416:at+832]
 second=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive' and e['session']==2);clean=bytes(c for c in second if c not in (17,19));screen=(folder/'SCREEN.BIN').read_bytes()
 expected=bytearray(b' \x07'*(logical*80))
 for offset,text in [(0,b'FIRST BYTE SAFELOGIN:END'),(160,b'NO CARRIER'),((logical-1)*160,lower)]:
  for i,value in enumerate(text):expected[offset+2*i]=value
 checks=dict(r['checks'],first_child_exit=head[:4]==(0x524e,1,1,1) and head[6]==14,
  first_JFT=raw[14:34]==raw[34:54],first_owners=raw[54:470]==raw[470:886],second_JFT=second_jft,second_owners=second_owners,
  second_child_success=(state['second_execs'],state['second_done'],state['second_exits'],state['second_exit_code'])==(1,1,1,0),
  first_carrier_dropped=sum(e['kind']=='first-hangup' for e in events)==1,second_connection=sum(e['kind']=='connected' for e in events)==2,
  child_was_paused=state['child_pause_seen']==1,paused_parent_cleared=state['stale_pause_seen']==0,disconnected_observed=state['disconnected_ticks']>=36,
  redial_observed=state['redial_key_sent']==1,reconnected_observed=state['reconnected_ticks']>=36,ready_and_exit_keys=state['ready_keys_sent']==state['exit_key_sent']==1,
  second_script=(folder/'SECOND.OK').read_bytes()==b'RECONNECTED' if (folder/'SECOND.OK').exists() else False,
  manual_query=b'SECONDOKready'+ESC+b'[1;25R' in clean,second_lower_row_query=ESC+f'[{logical};{len(lower)+1}R'.encode() in second,
  full_logical_frame=screen[:logical*160]==expected,physical_status=screen[logical*160:(logical+1)*160:2].startswith(b' Carrier lost'),
  final_peer_closed=sum(e['kind']=='completed-hangup' for e in events)==1,
  final_owners=[state[n] for n in WORDS[12:]]==[1,0,6,0,0,0,0,a.rows,0,logical,a.rows,14 if a.rows==28 else 8 if a.rows in (43,50) else 16])
 log=(folder/'dosbox.log').read_text();commands=re.findall(r'Command sent to modem: ->(.*?)<-',log);dial=(folder/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode()
 # The controller may terminate the retired command with one bare CR before
 # reinitializing. An empty Hayes line is harmless; no flow/data prefix is.
 checks.update(clean_modem_commands=commands in (['ATZ','ATD'+dial,'ATZ','ATD'+dial],['ATZ','ATD'+dial,'','ATZ','ATD'+dial]),no_modem_ERROR='Modem response: ERROR' not in log)
 for name,h in inputs.items():assert sha(ROOT/name)==h,name
 sources=[str(Path(__file__).relative_to(ROOT)),'standalone/test_modem_reconnect_dos.py','standalone/test_connection_dos.py','standalone/test_aspect_renderer_dos.py','standalone/test_aspect_script_window_dos.py','standalone/directory_fixtures.py']
 report=dict(passed=all(checks.values()),normal_display_startup=bool(a.terminal),checks=checks,physical_rows=a.rows,profile=a.profile,flow=a.flow,observations=state,modem_commands=commands,inputs=inputs,sources={n:sha(ROOT/n) for n in sources},captures={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()},observer_sha256=sha(out/'RENDER.COM'),observer_source_sha256=sha(out/'observer.asm'),scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('FINAL PASS' if report['passed'] else 'FINAL FAIL '+str([n for n,v in checks.items() if not v]),flush=True);assert report['passed']
if __name__=='__main__':main()
