#!/usr/bin/env python3
"""Independent actual terminal/ASPECT renderer tests with an owned modem peer.
Expected peer bytes are frozen before execution. No parser or reply substitutes.
"""
import argparse,hashlib,json,re,struct,sys,types,subprocess,shutil
from pathlib import Path
import test_connection_dos as connection
from directory_fixtures import directory,prm
ROOT=connection.ROOT;OUT=ROOT/'build/aspect-renderer-dos'
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
ESC=b'\x1b';QUERY=ESC+b'[6n';DA=ESC+b'[0c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def definitions():
 header=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+QUERY+DA
 source='proc main\nwaitfor "LOGIN:" 5\nif waitfor\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendif\nendproc\n'
 # Edit outside the later scroll region. CSI M explicitly uses NETWORK policy.
 advanced=(ESC+b'[2J'+ESC+b'[10;1HABCDE'+ESC+b'[10;2H'+ESC+b'[@'+ESC+b'[P'+
  ESC+b'[10;4H'+ESC+b'[KZ'+ESC+b'[11;1HLINE4'+ESC+b'[11;1H'+ESC+b'[L'+ESC+b'[M'+
  ESC+b'[7;1H'+ESC+b'[31mCOLOR'+ESC+b'[0m'+ESC+b'[2;5r'+ESC+b'[?6h'+ESC+b'[2;7H'+QUERY+
  ESC+b'[?6l'+ESC+b'[2;1HAAAA'+ESC+b'[3;1HBBBB'+ESC+b'[4;1HCCCC'+ESC+b'[5;1HDDDD\n'+
  ESC+b'[r'+ESC+b'[1;1H'+ESC+b'[KFIRST BYTE SAFE'+QUERY+DA)
 return [
  dict(name='queries-before-login',source=source,banner=header+b'LOGIN:',success=True,post=QUERY,post_reply=ESC+b'[1;22R',screen=[(0,0,'FIRST BYTE SAFE')]),
  dict(name='original-control-N-wait',source=source,banner=header+ESC+b'[Mdiscard-me\x0eLOGIN:',success=True,ansi_policy='ORIGINAL',post=QUERY,post_reply=ESC+b'[1;22R',screen=[(0,0,'FIRST BYTE SAFE')]),
  dict(name='native-edits-origin-scroll',source=source,banner=advanced+b'LOGIN:',success=True,post=QUERY,post_reply=ESC+b'[1;22R',extra_reply=ESC+b'[2;7R',screen=[(0,0,'FIRST BYTE SAFE'),(1,0,'BBBB'),(2,0,'CCCC'),(3,0,'DDDD'),(9,0,'ABCZ'),(10,0,'LINE4'),(6,0,'COLOR')],red=(6,0,5)),
  dict(name='nested-CSI-control',source=source,banner=header+ESC+b'[1;\x072H'+QUERY+ESC+b'[1;1H'+ESC+b'[KFIRST BYTE SAFE'+QUERY+DA+b'LOGIN:',success=True,post=QUERY,post_reply=ESC+b'[1;22R',extra_reply=ESC+b'[1;2R',screen=[(0,0,'FIRST BYTE SAFE')]),
  dict(name='native-RIS',source=source,banner=ESC+b'[5;6H'+ESC+b'[31mOLD'+ESC+b'c'+b'FIRST BYTE SAFE'+QUERY+DA+b'LOGIN:',success=True,post=QUERY,post_reply=ESC+b'[1;22R',screen=[(0,0,'FIRST BYTE SAFE')],blank=(4,5,3)),
  dict(name='XLT-lead-raw-continuations',source=source,banner=header.replace(ESC,b'z')+b'LOGIN:',success=True,post=QUERY.replace(ESC,b'z'),post_reply=ESC+b'[1;22R',screen=[(0,0,'FIRST BYTE SAFE')],xlt=True),
  dict(name='seven-bit-raw-continuations',source=source,banner=bytes(x|128 for x in header+b'LOGIN:'),success=True,post=bytes(x|128 for x in QUERY),post_reply=ESC+b'[1;22R',screen=[(0,0,'FIRST BYTE SAFE')],seven=True),
  dict(name='media-copy-rejected',source=source,banner=header+ESC+b'[0;5iLOGIN:',success=False,screen=[],mode_expected=dict(terminal_sink_3988_enabled=0,terminal_sink_398a_enabled=0)),
  dict(name='whole-mode-list-atomic',source=source,banner=header+ESC+b'[2;5r'+ESC+b'[?6;3hLOGIN:',success=False,screen=[],mode_expected=dict(csi_origin_mode=0,terminal_mode_372c=0)),
  dict(name='fragment-timeout-local-unwind',source=source,banner=header+ESC+b'[',success=False,screen=[(0,0,'FIRST BYTE SAFE')],timeout=True,clean_timeout=True),
  dict(name='fragment-Escape-local-unwind',source=source,banner=header+ESC+b'[',success=False,screen=[(0,0,'FIRST BYTE SAFE')],cancel=True)]

def map_offsets(path):
 global GROUP_REL
 text=path.read_text();group=re.search(r'DGROUP\s+([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})',text);GROUP_REL=int(group[1],16);base=GROUP_REL*16+int(group[2],16);symbols={}
 for line in text.splitlines():
  m=re.match(r'^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4,8})[*+]?\s+(\w+)',line)
  if m:symbols[m[3]]=int(m[1],16)*16+int(m[2],16)-base
 return symbols

def observer(offsets):
 policy_words=re.findall(r'X\((\w+)\)',(ROOT/'src/aspect/renderer_policy.h').read_text())+['terminal_program_status']
 policy_pairs=[(n,offsets[n]) for n in policy_words]+[(n,offsets['_'+n]) for n in ['redisplay_active','command_menu_active','capture_session_buffered']]
 policy_table=','.join(str(v) for n,v in policy_pairs)
 snapshots=[('screen_attribute_cells',2000),('screen_line_flags',25),('terminal_keymap',948),('terminal_history_pointer',4),('terminal_history_pending',1),('_capture_file_result',96),('_snapshot_file_result',96),('_monitor_file_result',96),('_history_file_result',96),('_printer_device_result',32),('_transfer_download_result',16),('_upload_source_result',20),('_batch_download_result',108)]
 snapshot_table=','.join(str(v) for n,size in snapshots for v in (offsets[n],size))
 snapshot_size=sum(v for n,v in snapshots)
 owners=[('_capture_file_result',96),('_snapshot_file_result',96),('_monitor_file_result',96),('_history_file_result',96),('_printer_device_result',32)]
 modes=['csi_origin_mode','cursor_state_value_1d20','terminal_mode_372c','modes_value_3980','modes_value_1d1a','csi_terminal_id','screen_cursor_row','screen_cursor_column','terminal_sink_3988_enabled','terminal_sink_398a_enabled']
 owner_table=','.join(str(x) for n,size in owners for x in (offsets[n],size));mode_table=','.join(str(offsets[n]) for n in modes)
 asm=r'''
BITS 16
CPU 8086
ORG 100h
jmp start
old21: dw 0,0
old1c: dw 0,0
sample:
magic: dw 0x524e
exec_seen: dw 0
exec_done: dw 0
child_exits: dw 0
parent_ds: dw 0
parent_psp: dw 0
exit_code: dw 0xffff
before_jft: times 20 db 0
after_jft: times 20 db 0
before_owners: times 416 db 0
after_owners: times 416 db 0
exit_modes: times 10 dw 0
any_execs: dw 0
last_exec_ds: dw 0
last_exec_kind: dw 0
last_exec_active: dw 0
admit_seen: dw 0
admit_words: times POLICY_COUNT dw 0
admit_snapshots: times SNAPSHOT_SIZE db 0
admit_bda: times 256 db 0
exec_names: times 8*64 db 0
before_history: times 72 db 0
exit_history: times 72 db 0
after_history: times 72 db 0
sample_end:
owner_table: dw OWNER_TABLE
mode_table: dw MODE_TABLE
policy_table: dw POLICY_TABLE
snapshot_table: dw SNAPSHOT_TABLE
%macro save 0
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
%endmacro
%macro restore 0
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
%endmacro
handler:
 save
 cld
 mov bp,sp
 cmp byte [ss:bp+17],0x4b
 jne .exit_check
 cmp byte [ss:bp+16],0
 jne .chain
 inc word [cs:any_execs]
 mov ax,ds
 mov [cs:last_exec_ds],ax
 mov ax,[PROGRAM_KIND]
 mov [cs:last_exec_kind],ax
 mov ax,[PROGRAM_ACTIVE]
 mov [cs:last_exec_active],ax
 cmp word [cs:any_execs],8
 ja .debug_done
 mov ax,ds
 mov es,ax
 mov si,dx
 push cs
 pop ds
 mov ax,[any_execs]
 dec ax
 mov cx,64
 mul cx
 mov di,exec_names
 add di,ax
 mov cx,63
.debug_name:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 or al,al
 jz .debug_end
 loop .debug_name
.debug_end:
 mov ax,[last_exec_ds]
 mov ds,ax
.debug_done:
 cmp word [cs:exec_seen],0
 jne .chain
 cmp word [PROGRAM_KIND],4
 jne .chain
 cmp word [PROGRAM_ACTIVE],1
 jne .chain
 mov ax,[PROCESS_PSP]
 mov es,ax
 cmp word [es:0],0x20cd
 jne .chain
 mov [cs:parent_psp],ax
 mov ax,ds
 mov [cs:parent_ds],ax
 push cs
 pop ds
 inc word [exec_seen]
 mov di,before_jft
 call copy_jft
 mov di,before_owners
 call copy_owners
 mov di,before_history
 call copy_history
 restore
 pushf
 call far [cs:old21]
 save
 push cs
 pop ds
 mov di,after_jft
 call copy_jft
 mov di,after_owners
 call copy_owners
 mov di,after_history
 call copy_history
 inc word [exec_done]
 ; Preserve DOS's returned carry/FLAGS in the outer interrupt frame.
 mov bp,sp
 mov ax,[ss:bp+18]
 mov [ss:bp+24],ax
 restore
 iret
.exit_check:
 cmp byte [ss:bp+17],0x4c
 jne .chain
 cmp word [cs:exec_seen],1
 jne .chain
 cmp word [cs:exec_done],0
 jne .chain
 mov al,[ss:bp+16]
 xor ah,ah
 mov [cs:exit_code],ax
 push cs
 pop ds
 inc word [child_exits]
 mov es,[parent_ds]
 mov si,mode_table
 mov di,exit_modes
 mov cx,10
.mode:
 lodsw
 mov bx,ax
 mov ax,[es:bx]
 mov [di],ax
 add di,2
 loop .mode
 mov di,exit_history
 call copy_history
.chain:
 restore
 jmp far [cs:old21]
copy_history:
 mov es,[parent_ds]
 mov ax,[es:HISTORY_START]
 mov [di],ax
 add di,2
 mov si,ax
 mov ax,[es:HISTORY_END]
 mov [di],ax
 add di,2
 mov ax,[es:HISTORY_POINTER]
 mov [di],ax
 add di,2
 mov ax,[es:HISTORY_POINTER+2]
 mov [di],ax
 add di,2
 mov es,ax
 mov cx,64
.byte:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .byte
 ret
copy_jft:
 mov es,[parent_psp]
 mov si,0x18
 mov cx,20
.loop:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .loop
 ret
copy_owners:
 mov es,[parent_ds]
 mov si,owner_table
 mov bp,5
.owner:
 lodsw
 mov bx,ax
 lodsw
 mov cx,ax
.byte:
 mov al,[es:bx]
 mov [di],al
 inc bx
 inc di
 loop .byte
 dec bp
 jnz .owner
 ret
timer:
 save
 cld
 mov ax,ss
 mov es,ax
 cmp ax,DGROUP_REL+0x10
 jb .done
 sub ax,DGROUP_REL+0x10
 cmp ax,[es:PROCESS_PSP]
 jne .done
 push es
 mov es,ax
 cmp word [es:0],0x20cd
 pop es
 jne .done
 cmp word [es:PROGRAM_KIND],4
 jne .done
 cmp word [es:PROGRAM_ACTIVE],1
 jne .done
 cmp word [es:PROGRAM_STATUS],5
 jne .done
 cmp word [cs:admit_seen],0
 jne .done
 push cs
 pop ds
 inc word [admit_seen]
 mov ax,es
 mov [parent_ds],ax
 mov ax,[es:PROCESS_PSP]
 mov [parent_psp],ax
 mov si,policy_table
 mov di,admit_words
 mov cx,POLICY_COUNT
.words:
 lodsw
 mov bx,ax
 mov ax,[es:bx]
 mov [di],ax
 add di,2
 loop .words
 mov si,snapshot_table
 mov di,admit_snapshots
 mov bp,SNAPSHOT_COUNT
.chunk:
 lodsw
 mov bx,ax
 lodsw
 mov cx,ax
.byte:
 mov al,[es:bx]
 mov [di],al
 inc bx
 inc di
 loop .byte
 dec bp
 jnz .chunk
 mov ax,0x40
 mov es,ax
 xor si,si
 mov di,admit_bda
 mov cx,256
.bda:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .bda
.done:
 restore
 jmp far [cs:old1c]
resident_end:
start:
 mov ax,0x3521
 int 0x21
 cmp byte [0x82],'T'
 jne collect
 mov [old21],bx
 mov [old21+2],es
 mov dx,handler
 mov ax,0x2521
 int 0x21
 mov ax,0x351c
 int 0x21
 mov [old1c],bx
 mov [old1c+2],es
 mov dx,timer
 mov ax,0x251c
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,handler
 jne failed
 cmp word [es:magic],0x524e
 jne failed
 mov ax,[es:old1c]
 mov [saved1c],ax
 mov ax,[es:old1c+2]
 mov [saved1c+2],ax
 pushf
 cli
 push ds
 mov ax,es
 mov ds,ax
 push cs
 pop es
 mov si,sample
 mov di,buffer
 mov cx,sample_end-sample
 cld
 rep movsb
 pop ds
 popf
 ; Unhook before writing the observer's owned report.
 push ds
 mov ax,0x3521
 int 0x21
 mov dx,[es:old21]
 mov ds,[es:old21+2]
 mov ax,0x2521
 int 0x21
 pop ds
 push ds
 mov dx,[saved1c]
 mov ds,[saved1c+2]
 mov ax,0x251c
 int 0x21
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,sample_end-sample
 mov ah,0x40
 int 0x21
 jc failed
 mov ah,0x3e
 int 0x21
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
saved1c: dw 0,0
filename: db 'D:\RENDER.BIN',0
buffer: times sample_end-sample db 0
'''
 for token,value in [('HISTORY_START',offsets['terminal_history_start']),('HISTORY_END',offsets['terminal_history_end']),('HISTORY_POINTER',offsets['terminal_history_pointer']),('POLICY_COUNT',len(policy_pairs)),('SNAPSHOT_COUNT',len(snapshots)),('SNAPSHOT_SIZE',snapshot_size),('POLICY_TABLE',policy_table),('SNAPSHOT_TABLE',snapshot_table),('DGROUP_REL',GROUP_REL),('PROGRAM_STATUS',offsets['terminal_program_status']),('OWNER_TABLE',owner_table),('MODE_TABLE',mode_table),('PROGRAM_KIND',offsets['terminal_program_kind']),('PROGRAM_ACTIVE',offsets['terminal_program_active']),('PROCESS_PSP',offsets['process_psp'])]:asm=asm.replace(token,str(value))
 (OUT/'observer.asm').write_text(asm);subprocess.run(['nasm','-fbin',str(OUT/'observer.asm'),'-o',str(OUT/'RENDER.COM')],check=True)
 return (OUT/'RENDER.COM').read_bytes(),modes,policy_pairs,snapshots

def adapter():
 path=ROOT/'standalone/test_connection_dos.py';source=path.read_text()
 replacements={"out=ROOT/'build/connection-dos'/name":"out=RENDER_OUT/name",
 "checks['immediate_banner_not_dropped']=len(screen)==4000 and screen[:30:2]==b'FIRST BYTE SAFE'":"checks['actual_screen_snapshot']=len(screen)==4000",
 "if online:\n       line.append(byte)":"if online:\n       line.append(byte)\n       if RENDER_POST and not checks.get('renderer_post_sent') and RENDER_TRIGGER in line:\n        conn.sendall(RENDER_POST);checks['renderer_post_sent']=True"}
 for old,new in replacements.items():assert source.count(old)==1;source=source.replace(old,new)
 module=types.ModuleType('renderer_connection_adapter');module.__file__=str(path);module.RENDER_OUT=OUT;module.RENDER_POST=b'';module.RENDER_TRIGGER=b'Synth42\r'
 exec(compile(source,str(path),'exec'),module.__dict__);return module

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True);parser.add_argument('--terminal-sha256',required=True);parser.add_argument('--runner-sha256',required=True);parser.add_argument('--case',action='append');args=parser.parse_args()
 assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
 global OUT
 OUT=OUT/args.label
 terminal=ROOT/'build/terminal/TERMINAL.EXE';runner=ROOT/'build/aspect-runner/ASPECT.EXE';assert sha(terminal)==args.terminal_sha256;assert sha(runner)==args.runner_sha256
 parent_manifest=json.loads((terminal.parent/'manifest.json').read_text());assert parent_manifest['binary_sha256']==args.terminal_sha256
 maps=list(terminal.parent.glob('*.map'));assert len(maps)==1,maps
 cases=definitions()
 if args.case:cases=[c for c in cases if c['name'] in args.case];assert {c['name'] for c in cases}==set(args.case)
 OUT.mkdir(parents=True,exist_ok=True)
 expectations=[{k:(v.hex() if isinstance(v,bytes) else v) for k,v in c.items()} for c in cases]
 expectation=OUT/('expectations-'+sha(terminal)[:8]+'-'+sha(runner)[:8]+'-'+str(len(cases))+'.json');encoded=json.dumps(expectations,indent=2)+'\n'
 if expectation.exists():assert expectation.read_text()==encoded
 else:expectation.write_text(encoded)
 compiled_observer,modes,policy_pairs,snapshots=observer(map_offsets(maps[0]));harness=adapter();results=[]
 for case in cases:
  name=case['name'];folder=OUT/name;assert not folder.exists(),f'Preserve/archive prior case before rerun: {folder}';folder.mkdir()
  shutil.copyfile(OUT/'observer.asm',folder/'observer.asm');shutil.copyfile(terminal,folder/'TERMINAL.EXE');shutil.copyfile(runner,folder/'ASPECT.EXE');harness.BINARY=folder/'TERMINAL.EXE';harness.RENDER_POST=case.get('post',b'')
  payload=bytearray(directory());payload[302:311]=b'LOGIN\0\0\0\0';payload[325:336]=b'Synth42\0\0\0\0'
  files={'LOGIN.ASP':case['source'].encode('cp437'),'LOGIN.ASX':compile_source(case['source']),'RENDER.COM':compiled_observer}
  settings=bytearray(prm());extra=' /A:NETWORK'
  if case.get('ansi_policy')=='ORIGINAL':extra=' /A:ORIGINAL'
  if case.get('seven'):struct.pack_into('<H',settings,0x1d64-0x1b84,2)
  if case.get('xlt'):
   table=bytearray(range(256));table[ord('z')]=27;table[27]=ord('!');table[ord('[')]=ord('{');files['TEST.XLT']=bytes(table);extra+=' /X:D:\\TEST.XLT'
  keys=('p1400 escape p3200 space p700 r e a d y p700 a-x' if case.get('cancel') else 'p8500 space p700 r e a d y p700 a-x' if case.get('clean_timeout') else 'p5000 space p700 r e a d y p700 a-x')
  result=harness.run(name,'success',keys,directory=bytes(payload),prm=bytes(settings),arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1'+extra,
    files=files,banner=case['banner'],working_drive='d',observer='RENDER')
  wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes();raw=(folder/'RENDER.BIN').read_bytes();header=struct.unpack_from('<7H',raw)
  checks=result['checks'];checks.update(passive_EXEC_observed=header[:4]==(0x524e,1,1,1),child_exit_expected=(header[6]==0)==(case['success'] or case.get('clean_timeout',False)),
   parent_JFT_unchanged=raw[14:34]==raw[34:54],all_parent_sink_owners_unchanged=raw[54:470]==raw[470:886],
   explicit_password_only=wire.count(b'Synth42\r')==int(case['success']),ordinary_parent_keyboard_resumes=b'ready' in wire,
   initial_CPR_before_password=not case['success'] or wire.find(ESC+b'[1;16R')<wire.find(b'Synth42\r'),
   no_automatic_redial=result['commands']==['ATZ','ATDCaseTest:23'],frozen_inputs=sha(terminal)==args.terminal_sha256 and sha(runner)==args.runner_sha256)
  if case['success']:
   checks['post_query_sent_after_password']=bool(checks.get('renderer_post_sent'))
   checks['post_return_cursor_coherent']=case['post_reply'] in wire and wire.find(b'Synth42\r')<wire.rfind(case['post_reply'])
  if case.get('extra_reply'):checks['origin_relative_report']=case['extra_reply'] in wire
  for row,col,text in case['screen']:checks[f'video_{row}_{col}']=screen[row*160+col*2:row*160+(col+len(text))*2:2]==text.encode()
  if case.get('red'):
   row,col,count=case['red'];checks['native_SGR_red']=all((x&7)==4 for x in screen[row*160+col*2+1:row*160+(col+count)*2:2])
  if case.get('blank'):
   row,col,count=case['blank'];checks['RIS_cleared_old_view']=screen[row*160+col*2:row*160+(col+count)*2:2]==b' '*count
  state=dict(zip(modes,struct.unpack_from('<10H',raw,886)))
  for field,value in case.get('mode_expected',{}).items():checks['atomic_'+field]=state[field]==value
  if not case['success'] and not case.get('clean_timeout'):checks['typed_error_stays_in_parent']=b'ASPECT returned an error.' in screen[::2] or b'Program could not run.' in screen[::2]
  admit_seen=struct.unpack_from('<H',raw,914)[0]
  admission={}
  if admit_seen:
   values=struct.unpack_from('<'+str(len(policy_pairs))+'H',raw,916);admission=dict(zip([n for n,v in policy_pairs],values))
   at=916+len(policy_pairs)*2;chunks={}
   for n,size in snapshots:chunks[n]=raw[at:at+size].hex();at+=size
   admission.update(snapshot_hex=chunks,BDA_hex=raw[at:at+256].hex())
  names_at=916+len(policy_pairs)*2+sum(v for n,v in snapshots)+256
  exec_names=[raw[names_at+i*64:names_at+(i+1)*64].split(b'\0',1)[0].decode('cp437') for i in range(8)]
  history_at=names_at+512;history=[raw[history_at+i*72:history_at+(i+1)*72] for i in range(3)];history_states=[struct.unpack_from('<4H',h) for h in history]
  checks['far_history_retained_across_EXEC_return']=history[1]==history[2]
  checks['far_history_bounds']=all(start<=pointer<end and segment for start,end,pointer,segment in history_states)
  if case['success']:checks['native_renderer_updated_far_history']=history[0]!=history[1]
  result.update(history_states=history_states,history_prefix_hex=[h[8:].hex() for h in history],observed_EXEC_names=exec_names,admission_failure_observed=admit_seen,admission_state=admission,passive_all_EXEC_debug=struct.unpack_from('<4H',raw,906),passed=all(checks.values()),passive_observer_header=header,child_exit_parent_state=state,runner_sha256=args.runner_sha256,expectations_sha256=sha(expectation),observer_sha256=sha(OUT/'RENDER.COM'))
  (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);print(name,'FINAL PASS' if result['passed'] else 'FINAL FAIL',flush=True)
 report=dict(passed=all(r['passed'] for r in results),cases=results,terminal_sha256=args.terminal_sha256,runner_sha256=args.runner_sha256,checker_sha256=sha(Path(__file__)),expectations_sha256=sha(expectation),parent_map_sha256=sha(maps[0]),observer_source_sha256=sha(OUT/'observer.asm'),original_inputs=[],scope='Actual product terminal+ASPECT child and passive source-owned EXEC/JFT/owner/mode observer, emulatedUART/BIOSvideo, ownedmodempeer. No parser or query-reply substitute. Sharedservice MCB/callback/stackmechanics delegate to independentclient/child/mechanicalproofs; physicalUART,CTSstall/cancel-unboundedinput and completeapplication remain separate.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
