#!/usr/bin/env python3
"""Actual full parent/GET interpreter DOS execution with an owned modem peer.

Raw mode authors GET at a linear PAUSE0 boundary. Compiler mode verifies real
host/DOS GET compilation; the malformed EOF case remains an authored raw input.
"""
import argparse,hashlib,inspect,json,os,re,shutil,struct,subprocess,sys,types
from pathlib import Path
import test_aspect_renderer_dos as renderer
ROOT=renderer.ROOT
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
PAUSE=bytes.fromhex('88b500')

STREAM_PROBE=False

def definitions():
 header=renderer.ESC+b'[2J'+renderer.ESC+b'[HFIRST BYTE SAFE'+renderer.QUERY+renderer.DA+b'LOGIN:'
 rows=[]
 for kind,operand,typed,value,success,error in [
  ('string','8c00',[0x264c,0x186f,0x2e43,0x0534,0x0332,0x1c0d],b'LoC42',True,0),
  ('integer','8d00',[0x0c2d,0x0231,0x0332,0x0433,0x1c0d],b'-123',True,0),
  ('long','8e00',[0x0736,0x0635,0x0635,0x0433,0x0736,0x1c0d],b'65536',True,0),
  ('cancel','8c00',[0x011b,0x1579],b'',False,13),
  ('float','8f00',[],b'',False,4),
  ('truncated','8d',[],b'',False,5)]:
  source='; GET VM '+kind+'\n'+('long' if kind=='long' else 'integer')+' number\nstring value\nproc main\nwaitfor "LOGIN:" 5\ntransmit "GETREADY"\npause 0\n'
  if kind=='string' and STREAM_PROBE:source=source.replace('pause 0\n','fopen 0 \"OWNED.TXT\" \"w+b\"\nfputs 0 \"BEFORE|\"\npause 0\nfputs 0 value\nfclose 0\n')
  if kind in ('integer','long'):source+=('ltoa' if kind=='long' else 'itoa')+' number value\n'
  source+='transmit value\ntransmit "^M"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n'
  get=bytes.fromhex('49'+operand+('01ab0a00' if kind!='truncated' else ''))
  rows.append(dict(name='get-vm-'+kind,source=source,GET_hex=get.hex(),banner=header,success=success,expected_exit=error,
   expected_value_hex=value.hex(),field_BIOS_words=typed,keys='p500 space',
   post=renderer.QUERY,post_reply=renderer.ESC+(b'[1;27R' if kind in ('string','long') else b'[1;26R'),screen=[(0,0,'FIRST BYTE SAFE')]))
 return rows

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--parent-dir',required=True,type=Path);p.add_argument('--child-dir',required=True,type=Path)
 p.add_argument('--output',required=True,type=Path);p.add_argument('--case',action='append')
 p.add_argument('--cpu',choices=('8086','386'),default='386')
 p.add_argument('--get-compiler-dir',type=Path,help='Use actual opt-in DOS/Python GET compilation for ordinary cases; malformed EOF stays raw')
 p.add_argument('--disabled-control',action='store_true',help='Compare GET-disabled child: expect explicit unsupported after GETREADY')
 p.add_argument('--stream-probe',action='store_true',help='Keep a real owned FOPEN stream across GET')
 p.add_argument('--allocation-probe',action='store_true',help='Passively capture file/global/CRT heap metadata at child exit')
 p.add_argument('--watchdog',action='store_true',help='Write a passive late GET state/video sample from the owned DOS test')
 a=p.parse_args();global STREAM_PROBE;STREAM_PROBE=a.stream_probe
 parent=a.parent_dir.resolve();child=a.child_dir.resolve();out=a.output.resolve()
 assert all(x.is_relative_to(ROOT/'build') for x in (parent,child,out)) and not out.exists()
 for folder,binary in ((parent,'TERMINAL.EXE'),(child,'ASPECT.EXE')):
  manifest=json.loads((folder/'manifest.json').read_text());assert manifest['binary_sha256']==sha(folder/binary)
  for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 get_enabled=json.loads((child/'manifest.json').read_text()).get('experimental_get_VM',False)
 assert get_enabled!=a.disabled_control
 child_map=(child/'ASPECT.map').read_text();group=re.search(r'DGROUP\s+([0-9a-f]+):([0-9a-f]+)',child_map,re.I)
 child_base=int(group[1],16)*16+int(group[2],16)
 child_symbols={n:int(s,16)*16+int(o,16)-child_base for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',child_map,re.M|re.I)}
 rows=definitions()
 if a.disabled_control:
  rows=[dict(r,success=False,expected_exit=3) for r in rows if r['name']=='get-vm-string']
 if a.case:rows=[r for r in rows if r['name'] in a.case];assert {r['name'] for r in rows}==set(a.case)
 dos_compiled={};get_compiler_manifest=None
 if a.get_compiler_dir:
  assert get_enabled and not a.disabled_control
  folder=a.get_compiler_dir.resolve();get_compiler_manifest=json.loads((folder/'manifest.json').read_text())
  assert get_compiler_manifest['experimental_get_compiler'] and get_compiler_manifest['original_inputs']==[]
  assert sha(folder/'ASPCOMP.EXE')==get_compiler_manifest['binary_sha256']
  for n,h in get_compiler_manifest['sources'].items():assert sha(ROOT/n)==h,n
  compile_folder=out/'compiled';compile_folder.mkdir(parents=True)
  shutil.copyfile(folder/'ASPCOMP.EXE',compile_folder/'ASPCOMP.EXE');batch=['@echo off'];stage=[]
  for i,row in enumerate(rows):
   if row['name']=='get-vm-truncated':continue
   target='value' if row['name'] in ('get-vm-string','get-vm-cancel') else 'number'
   if row['name']=='get-vm-float':row['source']=row['source'].replace('integer number','float number',1)
   row['source']=row['source'].replace('pause 0\n','get '+target+' 10\n')
   code=bytes.fromhex('49'+dict(string='8c00',cancel='8c00',integer='8d00',long='8e00',float='8f00')[row['name'][7:]]+'01b50a')
   expected=renderer.compile_source(row['source'],enable_get=True);assert expected.count(code)==1
   row['GET_hex']=code.hex();name='G'+str(i).zfill(3)
   (compile_folder/(name+'.ASP')).write_bytes(row['source'].encode('cp437'));stage.append((row,name,expected))
   batch+=['ASPCOMP '+name+'.ASP '+name+'.ASX >'+name+'.LOG','if errorlevel 1 goto failed']
  batch+=['echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done','exit']
  (compile_folder/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode())
  (compile_folder/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(compile_folder)+'"\nc:\nRUN\n')
  with (compile_folder/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(compile_folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
  assert (compile_folder/'PASS.TXT').exists() and not (compile_folder/'FAIL.TXT').exists()
  for row,name,expected in stage:
   wire=(compile_folder/(name+'.ASX')).read_bytes();assert wire==expected,row['name'];dos_compiled[row['name']]=wire
   row['compiled_source_sha256']=sha(compile_folder/(name+'.ASP'));row['compiled_ASX_sha256']=sha(compile_folder/(name+'.ASX'))
 original_compile=renderer.compile_source
 def compiled(source):
  case=next(r for r in rows if r['source']==source)
  if case['name'] in dos_compiled:return dos_compiled[case['name']]
  wire=original_compile(source);assert wire.count(PAUSE)==1
  if case['name'].endswith('-truncated'):return wire[:wire.index(PAUSE)]+bytes.fromhex(case['GET_hex'])
  return wire.replace(PAUSE,bytes.fromhex(case['GET_hex']))
 source=inspect.getsource(renderer.main)
 replacements={"ROOT/'build/terminal/TERMINAL.EXE'":'PARENT_BINARY',"ROOT/'build/aspect-runner/ASPECT.EXE'":'CHILD_BINARY',
  "maps=list(terminal.parent.glob('*.map'))":"maps=[terminal.parent/'terminal.map']",
  "'LOGIN.ASX':compile_source(case['source'])":"'LOGIN.ASX':get_compile(case['source'])",
  "observer='RENDER'":"observer='RENDER',observer_high=True"}
 for old,new in replacements.items():assert source.count(old)==1,old;source=source.replace(old,new)
 start=source.index('  keys=(');end=source.index('\n  result=harness.run',start)
 source=source[:start]+"  keys=case['keys']"+source[end:]
 # The reused passive observer's header identifies all DOS EXEC outcomes.
 def settings():
  data=bytearray(renderer.prm())
  for offset,value in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,4),(0x1e6,0),(0x1e4,0)]:struct.pack_into('<H',data,offset,value)
  return bytes(data)
 scope=dict(renderer.__dict__);scope.update(OUT=out.parent,definitions=lambda:rows,get_compile=compiled,
  prm=settings,directory=lambda:renderer.directory(profile=4),
  PARENT_BINARY=parent/'TERMINAL.EXE',CHILD_BINARY=child/'ASPECT.EXE')
 allocation_fields=[('_runtime_script_file_open_calls',0),('_runtime_script_file_live',0),('_runtime_script_file_last',0),('_runtime_native_error_code',0),('_runtime_steps',0),('_runtime_live',0),('_runtime_alloc_calls',0),('___nheapbeg',0),('__curbrk',0),('__STACKLOW',0),('__STACKTOP',0)]
 allocation_names=[n for n,d in allocation_fields]+['PSP_allocation_paragraphs','environment_paragraphs','environment_string_bytes']
 active_case=[None]
 def adapter():
  path=ROOT/'standalone/test_connection_dos.py';peer=path.read_text()
  changes={"out=ROOT/'build/connection-dos'/name":"out=RENDER_OUT/name",
   '       line.append(byte)':"       line.append(byte)\n       if RENDER_POST and not checks.get('renderer_post_sent') and RENDER_TRIGGER in line:\n        conn.sendall(RENDER_POST);checks['renderer_post_sent']=True"}
  for old,new in changes.items():assert peer.count(old)==1,old;peer=peer.replace(old,new)
  module=types.ModuleType('get_vm_modem_peer');module.__file__=str(path)
  module.RENDER_OUT=scope['OUT'];module.RENDER_POST=b'';module.RENDER_TRIGGER=b'Synth42\r'
  exec(compile(peer,str(path),'exec'),module.__dict__);run=module.run
  def configured(*args,**kwargs):return run(*args,**dict(kwargs,cpu=a.cpu,profile=4,timeout=45))
  module.run=configured;return module
 def observer(offsets):
  previous=renderer.OUT;renderer.OUT=scope['OUT']
  try:
   observer_source=inspect.getsource(renderer.observer)
   input_words=active_case[0]['field_BIOS_words'] if active_case[0] is not None and get_enabled else []
   old=" call far [cs:old21]\n save\n push cs"
   new=" call far [cs:old21]\n save\n mov bp,sp\n test word [ss:bp+18],1\n jz .get_exec_return\n mov ax,[ss:bp+16]\n mov [cs:exit_code],ax\n.get_exec_return:\n push cs"
   assert observer_source.count(old)==1;observer_source=observer_source.replace(old,new)
   old='sample_end:\nowner_table:';assert observer_source.count(old)==1
   observer_source=observer_source.replace(old,'get_input_injected: dw 0\nget_largest_free: dw 0\nget_observer_segment: dw 0\nget_conventional_kb: dw 0\nget_child_ds: dw 0\nget_child_errno: dw 0\nget_child_error: dw 0\nget_child_opcode: dw 0\nget_child_compiles: dw 0\nget_child_file_status: dw 0\nsample_end:\nowner_table:')
   old=' mov [cs:exit_code],ax\n push cs';assert observer_source.count(old)==1
   probe=' mov [cs:exit_code],ax\n mov ah,0x62\n pushf\n call far [cs:old21]\n mov ax,bx\n add ax,'+str(int(group[1],16)+16)+'\n mov es,ax\n mov [cs:get_child_ds],ax\n'
   for label,symbol,delta in [('errno','_errno',0),('error','_runtime_error',0),('opcode','_runtime_last_opcode',0),('compiles','_runtime_compiler_calls',0),('file_status','_runtime_file',14)]:
    probe+=' mov ax,[es:'+str(child_symbols[symbol]+delta)+']\n mov [cs:get_child_'+label+'],ax\n'
   if a.allocation_probe:
    marker='get_input_injected: dw 0';assert observer_source.count(marker)==1
    observer_source=observer_source.replace(marker,'get_allocation_probe: times '+str(len(allocation_names))+' dw 0\n'+marker)
    for index,(symbol,delta) in enumerate(allocation_fields):
     probe+=' mov ax,[es:'+str(child_symbols[symbol]+delta)+']\n mov [cs:get_allocation_probe+'+str(index*2)+'],ax\n'
    probe+=' mov ax,[cs:get_child_ds]\n sub ax,'+str(int(group[1],16)+16)+'\n mov es,ax\n mov dx,[es:0x2c]\n dec ax\n mov es,ax\n mov ax,[es:3]\n mov [cs:get_allocation_probe+22],ax\n mov ax,dx\n dec ax\n mov es,ax\n mov cx,[es:3]\n mov [cs:get_allocation_probe+24],cx\n mov word [cs:get_allocation_probe+26],0xffff\n cmp cx,1\n jb .get_env_done\n cmp cx,2048\n ja .get_env_done\n shl cx,1\n shl cx,1\n shl cx,1\n shl cx,1\n dec cx\n mov es,dx\n xor bx,bx\n.get_env_scan:\n cmp bx,cx\n jae .get_env_done\n cmp word [es:bx],0\n je .get_env_found\n inc bx\n jmp .get_env_scan\n.get_env_found:\n add bx,2\n mov [cs:get_allocation_probe+26],bx\n.get_env_done:\n'
   observer_source=observer_source.replace(old,probe+' push cs')
   old=' mov di,before_history\n call copy_history\n restore';assert observer_source.count(old)==1
   new=' mov di,before_history\n call copy_history\n mov ax,cs\n mov [cs:get_observer_segment],ax\n mov ax,0x40\n mov es,ax\n mov ax,[es:0x13]\n mov [cs:get_conventional_kb],ax\n mov ah,0x48\n mov bx,0xffff\n pushf\n call far [cs:old21]\n mov [cs:get_largest_free],bx\n restore'
   observer_source=observer_source.replace(old,new)
   old='timer:\n save\n cld';assert observer_source.count(old)==1
   observer_source=observer_source.replace(old,old+'\n call get_finish_tick')
   finish="""
get_finish_tick:
 cmp word [cs:exec_done],1
 jne .done
 cmp word [cs:get_finish_phase],3
 jae .done
 mov ax,[cs:parent_ds]
 or ax,ax
 jz .done
 mov es,ax
 cmp word [es:PROGRAM_ACTIVE],0
 je .terminal
 cmp word [cs:get_finish_phase],0
 jne .done
 mov dx,0x3920
 call get_finish_key
 jc .done
 mov word [cs:get_finish_phase],1
 jmp .done
.terminal:
 cmp word [es:PENDING_OFFSET],0
 jne .done
 inc word [cs:get_finish_ticks]
 cmp word [cs:get_finish_ticks],4
 jb .done
 cmp word [cs:get_finish_phase],2
 je .quit
 push cs
 pop ds
 mov si,get_finish_words
 mov cx,5
.next:
 lodsw
 mov dx,ax
 call get_finish_key
 jc .done
 loop .next
 mov word [cs:get_finish_phase],2
 mov word [cs:get_finish_ticks],0
 jmp .done
.quit:
 cmp word [cs:get_finish_ticks],18
 jb .done
 mov dx,0x2d00
 call get_finish_key
 jc .done
 mov word [cs:get_finish_phase],3
.done:
 ret
get_finish_key:
 mov ax,0x40
 mov es,ax
 mov bx,[es:0x1c]
 mov ax,bx
 add ax,2
 cmp ax,0x3e
 jb .nowrap
 mov ax,0x1e
.nowrap:
 cmp ax,[es:0x1a]
 je .full
 mov [es:bx],dx
 mov [es:0x1c],ax
 clc
 ret
.full:
 stc
 ret
get_finish_phase: dw 0
get_finish_ticks: dw 0
get_finish_words: dw 0x1372,0x1265,0x1e61,0x2064,0x1579
""".replace('PENDING_OFFSET',str(offsets['terminal_program_pending']))
   old='resident_end:\nstart:';assert observer_source.count(old)==1
   observer_source=observer_source.replace(old,finish+'\n'+old)
   if input_words:
    old='timer:\n save\n cld';assert observer_source.count(old)==1
    observer_source=observer_source.replace(old,old+'\n call get_input_tick')
    storage=child_symbols['_runtime_get_field_storage']
    injector='''
get_input_tick:
 cmp word [cs:get_input_injected],0
 jne .done
 mov ax,ss
 sub ax,CHILD_GROUP+16
 mov es,ax
 cmp word [es:0],0x20cd
 jne .done
 mov ax,[cs:parent_psp]
 cmp [es:0x16],ax
 jne .done
 mov ax,ss
 add ax,STORAGE_SEG
 mov es,ax
 mov si,STORAGE_OFFSET
 cmp word [es:si],1
 jne .done
 cmp word [es:si+18],1
 jne .done
 cmp word [es:si+20],0x4746
 jne .done
 cmp word [es:si+22],0
 jne .done
 mov ax,0x40
 mov es,ax
 mov bx,[es:0x1c]
 cmp bx,[es:0x1a]
 jne .done
 test bl,1
 jnz .done
 cmp bx,0x1e
 jb .done
 cmp bx,0x3e
 jae .done
'''.replace('CHILD_GROUP',str(int(group[1],16))).replace('STORAGE_SEG',str(storage//16)).replace('STORAGE_OFFSET',str(storage%16))
    assert 0<len(input_words)<15
    for i,word in enumerate(input_words):
     injector+=' mov word [es:bx],'+str(word)+'\n add bx,2\n cmp bx,0x3e\n jb .key'+str(i)+'\n mov bx,0x1e\n.key'+str(i)+':\n'
    injector+=' mov [es:0x1c],bx\n mov word [cs:get_input_injected],'+str(len(input_words))+'\n.done:\n ret\n'
    old='resident_end:\nstart:';assert observer_source.count(old)==1
    observer_source=observer_source.replace(old,injector+'\n'+old)
   if a.watchdog:
    old='timer:\n save\n cld';assert observer_source.count(old)==1
    observer_source=observer_source.replace(old,old+'\n call get_watch_tick')
    old=' mov [old21+2],es\n';assert observer_source.count(old)==1
    observer_source=observer_source.replace(old,old+' mov ah,0x34\n int 0x21\n mov [cs:get_watch_indos],bx\n mov [cs:get_watch_indos+2],es\n')
    storage=child_symbols['_runtime_get_field_storage']
    watch='''
get_watch_tick:
 mov ax,ss
 sub ax,CHILD_GROUP+16
 mov es,ax
 cmp word [es:0],0x20cd
 jne .done
 mov ax,[cs:parent_psp]
 cmp [es:0x16],ax
 jne .done
 cmp word [cs:exec_done],0
 jne .done
 inc word [cs:get_watch_ticks]
 mov ax,ss
 mov es,ax
 mov [cs:get_watch_data+6],ax
 mov ax,[cs:get_watch_ticks]
 mov [cs:get_watch_data+4],ax
'''.replace('CHILD_GROUP',str(int(group[1],16)))
    for i,symbol in enumerate(['_runtime_error','_runtime_steps','_runtime_last_opcode','_runtime_when_last_key','_runtime_keyboard_mode']):
     watch+=' mov ax,[es:'+str(child_symbols[symbol])+']\n mov [cs:get_watch_data+'+str(8+i*2)+'],ax\n'
    watch+=' mov ax,0x40\n mov es,ax\n mov ax,[es:0x1a]\n mov [cs:get_watch_data+18],ax\n mov ax,[es:0x1c]\n mov [cs:get_watch_data+20],ax\n'
    watch+=' mov ax,ss\n add ax,'+str(storage//16)+'\n mov es,ax\n mov si,'+str(storage%16)+'\n xor di,di\n mov cx,103\n.copy:\n mov ax,[es:si]\n mov [cs:get_watch_data+22+di],ax\n add si,2\n add di,2\n loop .copy\n'
    watch+='''
 cmp word [cs:get_watch_ticks],180
 jb .done
 cmp word [cs:get_watch_dumped],0
 jne .done
 les bx,[cs:get_watch_indos]
 cmp byte [es:bx],0
 jne .done
 mov word [cs:get_watch_dumped],1
 mov ax,[cs:get_input_injected]
 mov [cs:get_watch_data+228],ax
 push cs
 pop ds
 mov dx,get_watch_name
 xor cx,cx
 mov ah,0x3c
 pushf
 call far [cs:old21]
 jc .done
 mov bx,ax
 mov dx,get_watch_data
 mov cx,230
 mov ah,0x40
 pushf
 call far [cs:old21]
 mov ax,0xb800
 mov ds,ax
 xor dx,dx
 mov cx,4000
 mov ah,0x40
 pushf
 call far [cs:old21]
 mov ah,0x3e
 pushf
 call far [cs:old21]
.done:
 ret
get_watch_ticks: dw 0
get_watch_dumped: dw 0
get_watch_indos: dw 0,0
get_watch_name: db 'D:\\GETWATCH.BIN',0
get_watch_data: dw 0x4757,2
 times 226 db 0
'''
    old='resident_end:\nstart:';assert observer_source.count(old)==1
    observer_source=observer_source.replace(old,watch+'\n'+old)
   # A high-loaded TSR still inherits a conventional environment block.
   # The passive observer never reads it after installation; release that
   # unused fixture block rather than making the product fund test tooling.
   old=' mov dx,handler\n mov ax,0x2521';assert observer_source.count(old)==1
   new=' mov ax,[0x2c]\n or ax,ax\n jz .get_no_environment\n mov es,ax\n mov ah,0x49\n int 0x21\n jc failed\n mov word [0x2c],0\n.get_no_environment:\n mov dx,handler\n mov ax,0x2521'
   observer_source=observer_source.replace(old,new)
   temporary=dict(renderer.__dict__);exec(compile(observer_source,__file__,'exec'),temporary)
   return temporary['observer'](offsets)
  finally:renderer.OUT=previous
 scope.update(adapter=adapter,observer=observer)
 def case_observer(case,offsets):active_case[0]=case;return observer(offsets)
 scope['case_observer']=case_observer
 old="  shutil.copyfile(OUT/'observer.asm',folder/'observer.asm')";assert source.count(old)==1
 source=source.replace(old,"  compiled_observer,modes,policy_pairs,snapshots=case_observer(case,map_offsets(maps[0]))\n"+old)
 sys.argv=[sys.argv[0],'--label',out.name,'--terminal-sha256',sha(parent/'TERMINAL.EXE'),'--runner-sha256',sha(child/'ASPECT.EXE')]
 exec(compile(source,__file__,'exec'),scope);scope['main']()
 report=json.loads((out/'checks.json').read_text())
 for result in report['cases']:
  case=next(c for c in rows if c['name']==result['case']);folder=out/case['name'];wire=(folder/'serial.bin').read_bytes()
  free,segment,kb,child_ds,child_errno,child_error,child_opcode,child_compiles,child_file_status=struct.unpack('<9H',(folder/'RENDER.BIN').read_bytes()[-18:])
  injected=struct.unpack('<H',(folder/'RENDER.BIN').read_bytes()[-20:-18])[0]
  result['observer_sha256']=sha(folder/'RENDER.COM')
  result['observer_source_sha256']=sha(folder/'observer.asm')
  result['memory_before_EXEC']=dict(largest_free_bytes=free*16,observer_segment=segment,conventional_kb=kb)
  if a.allocation_probe:
   result['allocation_probe']=dict(zip(allocation_names,struct.unpack('<'+str(len(allocation_names))+'H',(folder/'RENDER.BIN').read_bytes()[-20-2*len(allocation_names):-20])))
  result['child_exit_probe']=dict(DS=child_ds,errno=child_errno,error=child_error,opcode=child_opcode,compiler_calls=child_compiles,file_status=child_file_status)
  if a.cpu=='386':result['checks']['passive_observer_in_UMB']=segment>=0xa000
  result['checks']['GET_typed_exit']=result['passive_observer_header'][6]==case['expected_exit']
  result['checks']['script_reached_GET_boundary']=b'GETREADY' in wire
  if get_enabled:result['checks']['BIOS_keys_after_field_admission']=injected==len(case['field_BIOS_words'])
  if case['success']:
   value=bytes.fromhex(case['expected_value_hex'])
   result['checks']['GET_edited_value_reaches_peer']=b'GETREADY'+value+b'\rSynth42\r' in wire
  else:result['checks']['no_post_GET_execution']=b'Synth42\r' not in wire
  if case['name']=='get-vm-string' and get_enabled and a.stream_probe:result['checks']['shared_FOPEN_GET_scratch_and_stream_retained']=(folder/'OWNED.TXT').is_file() and (folder/'OWNED.TXT').read_bytes()==b'BEFORE|LoC42'
  result['passed']=all(result['checks'].values());(folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 report.update(passed=all(r['passed'] for r in report['cases']),GET_VM=get_enabled,allocation_probe=a.allocation_probe,stream_probe=a.stream_probe,disabled_control=a.disabled_control,compiler_GET_enabled=bool(a.get_compiler_dir),compiled_GET_cases=len(dos_compiled),GET_compiler_sha256=get_compiler_manifest['binary_sha256'] if get_compiler_manifest else None,emulated_cpu=a.cpu,
  checker_sha256=sha(__file__),scope=__doc__+(' Five ordinary cases can use real DOS/Python GET compilation; malformed EOF remains an explicitly authored input.' if a.get_compiler_dir else '')+' Actual parent, child, native dispatcher, GET bank, typed operands, DOS files/heap, UART/parser, BIOS keys and passive return observer. Synthetic modem peer; not physical Boca/ATA/SynthModem/BBS acceptance.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('GET full VM:',len(report['cases']),'cases',report['passed'])
 return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
