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

def lifetime_definitions():
 base=definitions()[0]
 header='integer number,saved\nlong wide\nstring value,temp\n'
 start='proc main\nwaitfor "LOGIN:" 5\ntransmit "GETREADY"\n'
 finish='transmit "^M"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n'
 batches=[[0x1e41,0x1c0d],[0x3042,0x1c0d],[0x0c2d,0x0332,0x1c0d],[0x0736,0x0635,0x0635,0x0433,0x0736,0x1c0d]]
 repeat=header+start+'get value 10\nget value 10\nget number 10\nget wide 10\ntransmit value\ntransmit "/"\nitoa number temp\ntransmit temp\ntransmit "/"\nltoa wide temp\ntransmit temp\n'+finish
 chain=header+start+'get value 10\nget number 10\nset break 1234\nexecute "NEXT"\ntransmit "BADRETURN"\nendproc\n'
 target=header+'proc main\nfetch break saved\nif saved != 1234\ntransmit "BADPOLICY"\nendif\nif number != -2\ntransmit "BADNUMBER"\nendif\ntransmit "<"\ntransmit value\ntransmit ">"\nget value 10\ntransmit value\n'+finish
 return [dict(base,name='get-vm-repeat',source=repeat,direct_GET=True,field_batches=batches,field_BIOS_words=sum(batches,[]),expected_value_hex=b'B/-2/65536'.hex(),post_reply=renderer.ESC+b'[1;31R'),
  dict(base,name='get-vm-execute',source=chain,direct_GET=True,scripts={'NEXT':target},field_batches=[batches[0],batches[2],batches[1]],field_BIOS_words=sum([batches[0],batches[2],batches[1]],[]),expected_value_hex=b'<>B'.hex(),post_reply=renderer.ESC+b'[1;26R')]

def when_definitions():
 base=definitions()[0]
 rows=[]
 for framed in (False,True):
  source=('integer hits\nstring value\nproc main\n'
   'waitfor "LOGIN:" 5\nwhen 0 "PING" transmit "INLINE"\nwhen 1 "PONG" call worker\n'
   'transmit "GETREADY"\nget value 10\nif hits != 1\ntransmit "BADCOUNT"\nendif\n'
   'transmit value\ntransmit "^M"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\nproc worker\n'
   +('integer local_value\nlocal_value=37\nif local_value != 37\ntransmit "BADLOCAL"\nendif\n' if framed else '')
   +'hits=hits+1\ntransmit "WORKER"\nendproc\n')
  rows.append(dict(base,name='get-vm-when-'+('framed' if framed else 'plain'),source=source,direct_GET=True,when_action=True,
   expected_value_hex=b'INLINEWORKERLoC42'.hex(),peer_triggers=[('GETREADY',[(0.25,'PINGPONG')])]))
 return rows

def when_error_definitions():
 rows=when_definitions()
 divide=dict(rows[1],name='get-vm-when-divide',success=False,expected_exit=11,when_worker_expected=1,
  expected_owned_hex=b'BEFORE|WORKER|'.hex())
 divide['source']=divide['source'].replace('integer hits\n','integer hits,zero,quotient\n',1).replace('transmit "WORKER"\n','transmit "WORKER"\nfputs 0 "WORKER|"\nquotient=1/zero\ntransmit "BADAFTER"\n')
 cancel=dict(rows[0],name='get-vm-when-cancel',success=False,expected_exit=13,when_worker_expected=0,
  field_BIOS_words=[0x011b,0x1579],expected_owned_hex=b'BEFORE|'.hex())
 for row in (divide,cancel):
  row['source']=row['source'].replace('transmit "GETREADY"\n','fopen 0 "OWNED.TXT" "w+b"\nfputs 0 "BEFORE|"\ntransmit "GETREADY"\n')
  row['when_error']=True
 return [divide,cancel]

def storage_definitions():
 rows=[]
 for scope,kind in [('local',k) for k in ('string','integer','long')]+[('parameter',k) for k in ('string','integer','long')]+[('builtin','string')]:
  seed={'string':'"SEED"','integer':'17','long':'70000L'}[kind]
  base=next(r for r in definitions() if r['name']=='get-vm-'+kind)
  name='s0' if scope=='builtin' else 'target'
  declaration=({'string':'strparm','integer':'intparm','long':'longparm'}[kind]+' target\n' if scope=='parameter' else '')
  declaration+='integer left_guard,right_guard\n'
  if scope=='local':declaration+=kind+' target\n'
  output=('transmit '+name+'\n' if kind=='string' else ('itoa' if kind=='integer' else 'ltoa')+' '+name+' temp\ntransmit temp\n')
  source=('integer global_guard\nstring value,temp\nproc main\nglobal_guard=4321\nvalue="GUARD"\n'
   'waitfor "LOGIN:" 5\ntransmit "GETREADY"\ncall worker'+(' with '+seed if scope=='parameter' else '')+'\n'
   'if global_guard != 4321\ntransmit "BADGLOBAL"\nendif\ntransmit "/"\ntransmit value\ntransmit "^M"\n'
   'transmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\nproc worker\n'+declaration+
   'left_guard=1234\nright_guard=5678\n'+(name+'='+seed+'\n' if scope!='parameter' else '')+
   'get '+name+' 10\nif left_guard != 1234\ntransmit "BADLEFT"\nendif\n'
   'if right_guard != 5678\ntransmit "BADRIGHT"\nendif\n'+output+'endproc\n')
  rows.append(dict(base,name='get-vm-'+scope+'-'+kind,source=source,direct_GET=True,storage_scope=scope,storage_kind=kind,
   expected_value_hex=(bytes.fromhex(base['expected_value_hex'])+b'/GUARD').hex()))
 return rows

def policy_definitions():
 base=definitions()[0];rows=[]
 for label,width,observed,typed,value,error,cpr in [
  ('default',None,80,base['field_BIOS_words'],b'LoC42',0,b'[1;27R'),
  ('maximum','80',80,base['field_BIOS_words'],b'LoC42',0,b'[1;27R'),
  ('one','1',1,[0x1e41,0x1c0d],b'A',0,b'[1;22R'),
  ('zero','0',0,[],b'SEED',0,b'[1;22R'),
  ('negative','-1',0,[],b'',7,b''),
  ('oversize','81',0,[],b'',7,b''),
  ('bottom-shown',None,5,base['field_BIOS_words'],b'LoC42',0,b'[24;80R'),
  ('bottom-hidden',None,80,base['field_BIOS_words'],b'LoC42',0,b'[25;1R')]:
  setting='' # Status visibility is a PRM preference, not an admitted SET command.
  source=('string value\nproc main\n'+setting+('value="SEED"\n' if label=='zero' else '')+
   'waitfor "LOGIN:" 5\ntransmit "GETREADY"\nget value'+(' '+width if width is not None else '')+'\n'
   'transmit value\ntransmit "^M"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n')
  banner=base['banner']
  if label.startswith('bottom-'):banner=banner.replace(b'LOGIN:',renderer.ESC+b'[24;70HLOGIN:')
  rows.append(dict(base,name='get-vm-policy-'+label,source=source,direct_GET=True,policy_width=observed,
   field_BIOS_words=typed,expected_value_hex=value.hex(),success=not error,expected_exit=error,
   post_reply=renderer.ESC+cpr,banner=banner,policy_status_hidden=int(label.endswith('hidden'))))
 return rows

def source_memory_definitions():
 base=definitions()[0]
 target=base['source'].replace('pause 0\n','get value 10\n')
 start=dict(base,name='get-vm-source-start',source=target,direct_GET=True,source_memory='start',success=False,
  expected_exit=8,field_BIOS_words=[],expect_GET_boundary=False)
 chain='proc main\nwaitfor "LOGIN:" 5\nfopen 0 "OWNED.TXT" "w+b"\nfputs 0 "BEFORE|"\ntransmit "GETREADY"\nexecute "NEXT.ASP"\ntransmit "BADRETURN"\nendproc\n'
 following=target.replace('waitfor "LOGIN:" 5\n','')
 execute=dict(base,name='get-vm-source-execute',source=chain,direct_GET=True,source_memory='execute',success=False,
  expected_exit=8,field_BIOS_words=[],scripts={'NEXT':following},expect_GET_boundary=True)
 return [start,execute]

def source_fault_definitions():
 rows=[]
 for fault in ('missing','corrupt','truncated','compiler-error'):
  for base in source_memory_definitions():
   rows.append(dict(base,name=base['name']+'-'+fault,source_fault=fault,expected_exit=5))
 return rows

def source_recovery_definitions():
 rows=[]
 for kind in ('grow','read'):
  for base in source_memory_definitions():
   rows.append(dict(base,name=base['name']+'-recover-'+kind,source_lease=True,source_recovery=kind,
    success=True,expected_exit=0,field_BIOS_words=definitions()[0]['field_BIOS_words'],expect_GET_boundary=True))
 return rows

def source_cleanup_definitions():
 return [dict(base,name=base['name']+'-cleanup-unlink',source_cleanup=True,expected_exit=5)
  for base in source_memory_definitions()]

def source_reuse_definitions():
 base=source_memory_definitions()[0];good=base['source'].replace('proc main\n','proc main\ntransmit "SECONDREADY"\n',1)
 rows=[]
 for kind in ('write','begin-close','close','unlink'):
  row=dict(base,name='get-vm-source-reuse-'+kind,source='proc main\ntransmit "BADFIRST"\nendproc\n',
   scripts={'GOOD':good},source_reuse=True,success=True,expected_exit=0,
   peer_triggers=[('SECONDREADY',[(0.25,base['banner'].decode('ascii'))])],
   field_BIOS_words=definitions()[0]['field_BIOS_words'],expect_GET_boundary=True)
  row['source_begin' if kind in ('write','begin-close') else 'source_cleanup']=kind
  rows.append(row)
 return rows

def source_close_definitions():
 rows=[]
 for base in source_memory_definitions():
  rows.append(dict(base,name=base['name']+'-begin-close',source_begin='begin-close',expected_exit=5))
  rows.append(dict(base,name=base['name']+'-cleanup-close',source_cleanup='close',expected_exit=5))
 return rows

def source_repeat_definitions():
 rows=[]
 check='fetch break saved\nif saved != 1234\ntransmit "BADPOLICY"\nendif\n'
 for count in (2,3):
  base=source_memory_definitions()[1]
  first=base['source'].replace('proc main\n','proc main\nset break 1234\n',1)
  final='integer saved\n'+base['scripts']['NEXT'].replace('proc main\n','proc main\n'+check,1)
  scripts={'NEXT':final};outputs={'OWNED.TXT':b'BEFORE|'.hex()}
  if count==3:
   scripts={'NEXT':'integer saved\nproc main\n'+check+'fopen 0 "HOP.TXT" "w+b"\nfputs 0 "HOP|"\nexecute "FINAL.ASP"\ntransmit "BADRETURN"\nendproc\n','FINAL':final}
   outputs['HOP.TXT']=b'HOP|'.hex()
  rows.append(dict(base,name='get-vm-source-repeat-'+str(count),source=first,scripts=scripts,source_memory='start',source_repeat=count,
   source_lease=True,success=True,expected_exit=0,field_BIOS_words=definitions()[0]['field_BIOS_words'],expect_GET_boundary=True,source_outputs=outputs))
 return rows

def source_begin_definitions():
 return [dict(base,name=base['name']+'-begin-'+kind,source_begin=kind,expected_exit=5)
  for kind in ('create','write','short-write') for base in source_memory_definitions()]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--parent-dir',required=True,type=Path);p.add_argument('--child-dir',required=True,type=Path)
 p.add_argument('--output',required=True,type=Path);p.add_argument('--case',action='append')
 p.add_argument('--cpu',choices=('8086','386'),default='386')
 p.add_argument('--source-lease-cases',action='store_true',help='Require successful startup/EXECUTE source compilation through the parent lease')
 p.add_argument('--source-lease-reuse-cases',action='store_true',help='After a failed source startup, launch another source through real Alt-F5 without restarting the parent')
 p.add_argument('--source-lease-close-cases',action='store_true')
 p.add_argument('--source-lease-begin-cases',action='store_true',help='Fail backup creation/partial write before lending; require unchanged parent and safe abort')
 p.add_argument('--source-lease-repeat-cases',action='store_true',help='Compile two/three sources within one interpreter; verify each kernel token/MCB and stream retirement')
 p.add_argument('--source-lease-cleanup-cases',action='store_true',help='Deny backup unlink after verified restore; require safe typed error and preserved backup')
 p.add_argument('--source-lease-recovery-cases',action='store_true',help='Inject one restore grow/read failure, observe BIOS quarantine, then retry')
 p.add_argument('--source-lease-fault-cases',action='store_true',help='Require safe startup/EXECUTE return after module refusal or compiler syntax error')
 p.add_argument('--source-memory-cases',action='store_true',help='Diagnose startup and EXECUTE source compilation under the complete parent')
 p.add_argument('--policy-cases',action='store_true',help='Run default/boundary widths and bottom-row shown/hidden status policy')
 p.add_argument('--storage-cases',action='store_true',help='Run local and parameter string/int/long GET plus builtin S0 with frame guards')
 p.add_argument('--when-error-cases',action='store_true',help='Run framed WHEN divide fault and confirmed GET cancellation with pending CALL')
 p.add_argument('--when-cases',action='store_true',help='Run inline TRANSMIT and deferred plain/framed WHEN CALL during GET')
 p.add_argument('--lifetime-cases',action='store_true',help='Run repeated fields and EXECUTE with generation-conditioned BIOS input')
 p.add_argument('--get-compiler-dir',type=Path,help='Use actual opt-in DOS/Python GET compilation for ordinary cases; malformed EOF stays raw')
 p.add_argument('--disabled-control',action='store_true',help='Compare GET-disabled child: expect explicit unsupported after GETREADY')
 p.add_argument('--stream-probe',action='store_true',help='Keep a real owned FOPEN stream across GET')
 p.add_argument('--allocation-probe',action='store_true',help='Passively capture file/global/CRT heap metadata at child exit')
 p.add_argument('--connected-probe',action='store_true',help='Check raw CONNECTED128 and long promotion before/after GET and source EXECUTE')
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
 assert sum((a.source_lease_reuse_cases,a.source_lease_close_cases,a.source_lease_begin_cases,a.source_lease_repeat_cases,a.source_lease_cleanup_cases,a.source_lease_recovery_cases,a.source_lease_fault_cases,a.source_lease_cases,a.source_memory_cases,a.policy_cases,a.storage_cases,a.when_error_cases,a.when_cases,a.lifetime_cases))<=1
 rows=source_reuse_definitions() if a.source_lease_reuse_cases else source_close_definitions() if a.source_lease_close_cases else source_begin_definitions() if a.source_lease_begin_cases else source_repeat_definitions() if a.source_lease_repeat_cases else source_cleanup_definitions() if a.source_lease_cleanup_cases else source_recovery_definitions() if a.source_lease_recovery_cases else source_fault_definitions() if a.source_lease_fault_cases else source_memory_definitions() if a.source_memory_cases or a.source_lease_cases else policy_definitions() if a.policy_cases else storage_definitions() if a.storage_cases else when_error_definitions() if a.when_error_cases else when_definitions() if a.when_cases else lifetime_definitions() if a.lifetime_cases else definitions()
 if a.source_lease_cases:
  for row in rows:
   row.update(source_lease=True,success=True,expected_exit=0,field_BIOS_words=definitions()[0]['field_BIOS_words'],expect_GET_boundary=True)
 if a.source_lease_reuse_cases or a.source_lease_close_cases or a.source_lease_begin_cases or a.source_lease_repeat_cases or a.source_lease_cleanup_cases or a.source_lease_recovery_cases or a.source_lease_fault_cases or a.source_lease_cases or a.source_memory_cases or a.policy_cases or a.storage_cases or a.lifetime_cases or a.when_cases or a.when_error_cases:assert a.get_compiler_dir and not a.disabled_control
 if a.source_lease_fault_cases or a.source_lease_repeat_cases:assert a.allocation_probe
 if a.source_lease_cases:assert a.allocation_probe,'source lease acceptance requires the passive allocation/EXEC observer'
 if a.source_lease_reuse_cases or a.source_lease_close_cases or a.source_lease_begin_cases or a.source_lease_recovery_cases or a.source_lease_cleanup_cases:assert a.allocation_probe and a.watchdog
 if a.disabled_control:
  rows=[dict(r,success=False,expected_exit=3) for r in rows if r['name']=='get-vm-string']
 if a.case:rows=[r for r in rows if r['name'] in a.case];assert {r['name'] for r in rows}==set(a.case)
 if a.connected_probe:
  assert a.get_compiler_dir and not a.disabled_control
  guard='if connected != 128 || connected+1L != 129L\ntransmit "BADCARRIER"\nendif\n'
  def carrier_probe(source):
   result=[];count=0
   for line in source.splitlines(keepends=True):
    if line=='transmit "GETREADY"\n':result.append(guard);count+=1
    result.append(line)
    if line.startswith('get ') or line=='pause 0\n':result.append(guard);count+=1
   assert count,source
   return ''.join(result),count
  for row in rows:
   row['source'],row['CONNECTED_probe_count']=carrier_probe(row['source'])
   for name,source in row.get('scripts',{}).items():
    row['scripts'][name],count=carrier_probe(source)
    row['CONNECTED_probe_count']+=count
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
   if not row.get('direct_GET'):
    target='value' if row['name'] in ('get-vm-string','get-vm-cancel') else 'number'
    if row['name']=='get-vm-float':row['source']=row['source'].replace('integer number','float number',1)
    row['source']=row['source'].replace('pause 0\n','get '+target+' 10\n')
    code=bytes.fromhex('49'+dict(string='8c00',cancel='8c00',integer='8d00',long='8e00',float='8f00')[row['name'][7:]]+'01b50a')
    row['GET_hex']=code.hex()
   expected=renderer.compile_source(row['source'],enable_get=True)
   if not row.get('direct_GET'):assert expected.count(code)==1
   name='G'+str(i).zfill(3)
   (compile_folder/(name+'.ASP')).write_bytes(row['source'].encode('cp437'));stage.append((row,name,expected))
   batch+=['ASPCOMP '+name+'.ASP '+name+'.ASX >'+name+'.LOG','if errorlevel 1 goto failed']
   for j,(leaf,source) in enumerate(row.get('scripts',{}).items()):
    # Cases can use the same DOS leaf for different programs. Namespace the
    # bootstrap files before writing the batch, then map back to the real leaf.
    name='S'+str(i).zfill(3)+str(j).zfill(3);assert len(name)<=8
    row.setdefault('compile_script_names',{})[name]=leaf
    expected_script=renderer.compile_source(source,enable_get=True);(compile_folder/(name+'.ASP')).write_bytes(source.encode('cp437'))
    stage.append((row,name,expected_script));batch+=['ASPCOMP '+name+'.ASP '+name+'.ASX >'+name+'.LOG','if errorlevel 1 goto failed']
  batch+=['echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done','exit']
  (compile_folder/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode())
  (compile_folder/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(compile_folder)+'"\nc:\nRUN\n')
  with (compile_folder/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(compile_folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
  assert (compile_folder/'PASS.TXT').exists() and not (compile_folder/'FAIL.TXT').exists()
  for row,name,expected in stage:
   wire=(compile_folder/(name+'.ASX')).read_bytes();assert wire==expected,row['name']
   if name.startswith('G'):dos_compiled[row['name']]=wire
   else:row.setdefault('compiled_scripts',{})[row['compile_script_names'][name]]=wire.hex()
   if name.startswith('G'):
    row['compiled_source_sha256']=sha(compile_folder/(name+'.ASP'));row['compiled_ASX_sha256']=sha(compile_folder/(name+'.ASX'))
   else:row.setdefault('compiled_script_hashes',{})[row['compile_script_names'][name]]=dict(source_sha256=sha(compile_folder/(name+'.ASP')),ASX_sha256=sha(compile_folder/(name+'.ASX')))
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
  if active_case[0] is not None and 'policy_status_hidden' in active_case[0]:
   struct.pack_into('<H',data,0x1c2,active_case[0]['policy_status_hidden'])
  return bytes(data)
 scope=dict(renderer.__dict__);scope.update(OUT=out.parent,definitions=lambda:rows,get_compile=compiled,
  prm=settings,directory=lambda:renderer.directory(profile=4),
  PARENT_BINARY=parent/'TERMINAL.EXE',CHILD_BINARY=child/'ASPECT.EXE')
 allocation_fields=[('_runtime_script_file_open_calls',0),('_runtime_script_file_live',0),('_runtime_script_file_last',0),('_runtime_native_error_code',0),('_runtime_steps',0),('_runtime_live',0),('_runtime_alloc_calls',0),('___nheapbeg',0),('__curbrk',0),('__STACKLOW',0),('__STACKTOP',0)]
 if a.source_lease_reuse_cases or a.source_lease_close_cases or a.source_memory_cases or a.source_lease_cases or a.source_lease_fault_cases or a.source_lease_recovery_cases or a.source_lease_cleanup_cases or a.source_lease_repeat_cases or a.source_lease_begin_cases:allocation_fields += [('_runtime_compiler_exit',0),('_runtime_compiler_dos_error',0)]
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
  def configured(*args,**kwargs):
   case=next(r for r in rows if r['name']==args[0])
   for leaf,wire in case.get('compiled_scripts',{}).items():
    kwargs['files'][leaf+'.ASX']=bytes.fromhex(wire);kwargs['files'][leaf+'.ASP']=case['scripts'][leaf].encode('cp437')
   if case.get('source_memory'):
    kwargs['files']['ASPCOMP.EXE']=(a.get_compiler_dir/'ASPCOMP.EXE').read_bytes()
    if case['source_memory']=='start':kwargs['files'].pop('LOGIN.ASX')
    else:kwargs['files']['NEXT.ASX']=renderer.compile_source('proc main\ntransmit "STALE"\nendproc\n')
   if case.get('source_repeat'):
    for leaf in case['scripts']:
     kwargs['files'][leaf+'.ASX']=renderer.compile_source('proc main\ntransmit "STALE"\nendproc\n')
   if case.get('source_fault')=='compiler-error':
    leaf='LOGIN' if case['source_memory']=='start' else 'NEXT'
    kwargs['files'][leaf+'.ASP']=kwargs['files'][leaf+'.ASP'].replace(b'endproc',b'not_a_command\nendproc',1)
   if case.get('source_reuse'):
    kwargs['files'].pop('GOOD.ASX')
    for leaf in ('PCMETA.OVL','PCLINE.OVL'):kwargs['files'][leaf]=(parent/leaf).read_bytes()
   return run(*args,**dict(kwargs,cpu=a.cpu,profile=4,timeout=45,online_triggers=[(trigger.encode('ascii'),[(delay,data.encode('ascii')) for delay,data in chunks]) for trigger,chunks in case.get('peer_triggers',())]))
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
   if active_case[0] and active_case[0].get('source_memory'):
    marker='get_input_injected: dw 0';assert observer_source.count(marker)==1
    observer_source=observer_source.replace(marker,'get_compiler_largest: dw 0\nget_compiler_attempts: dw 0\nget_startup_prompt_seen: dw 0\n'+marker)
    # A nested compiler exits while the parent tail is lent. Count its exit,
    # but never inspect the suspended parent's history or pretend its PSP is
    # the interpreter's. Only the immediate ASPECT child gets those probes.
    marker=' mov al,[ss:bp+16]\n xor ah,ah\n mov [cs:exit_code],ax';assert observer_source.count(marker)==1
    guarded=' mov ah,0x51\n pushf\n call far [cs:old21]\n mov es,bx\n mov ax,[cs:parent_psp]\n cmp [es:0x16],ax\n je .direct_child_exit\n inc word [cs:child_exits]\n jmp .chain\n.direct_child_exit:\n'+marker
    observer_source=observer_source.replace(marker,guarded)
    marker='handler:\n save\n cld\n mov bp,sp';assert observer_source.count(marker)==1
    observer_source=observer_source.replace(marker,'handler:\n save\n cld\n save\n cmp ax,0x4b00\n jne .compiler_probe_done\n cmp word [cs:exec_seen],1\n jne .compiler_probe_done\n cmp word [cs:exec_done],0\n jne .compiler_probe_done\n inc word [cs:get_compiler_attempts]\n mov ah,0x48\n mov bx,0xffff\n pushf\n call far [cs:old21]\n mov [cs:get_compiler_largest],bx\n.compiler_probe_done:\n restore\n mov bp,sp')
   if active_case[0] and 'policy_width' in active_case[0]:
    marker='get_input_injected: dw 0';assert observer_source.count(marker)==1
    observer_source=observer_source.replace(marker,'get_policy_width: dw 0\n'+marker)
   if active_case[0] and active_case[0].get('when_action'):
    marker='get_input_injected: dw 0';assert observer_source.count(marker)==1
    observer_source=observer_source.replace(marker,'get_when_waiting: dw 0\nget_when_gate: dw 0\n'+marker)
   if active_case[0] and active_case[0].get('when_error'):
    marker='get_when_waiting: dw 0';assert observer_source.count(marker)==1
    observer_source=observer_source.replace(marker,'get_error_retirement: times 5 dw 0\n'+marker)
    storage=child_symbols['_runtime_get_field_storage']
    probe+=' mov ax,[cs:get_child_ds]\n add ax,'+str(storage//16)+'\n mov es,ax\n'
    for index,offset in enumerate((0,2,4,6,10)):
     probe+=' mov ax,[es:'+str(storage%16+offset)+']\n mov [cs:get_error_retirement+'+str(index*2)+'],ax\n'
    probe+=' mov ax,[cs:get_child_ds]\n mov es,ax\n'
   if active_case[0] and active_case[0].get('field_batches'):
    marker='get_input_injected: dw 0';assert observer_source.count(marker)==1
    observer_source=observer_source.replace(marker,'get_lifetime_generations: times '+str(len(active_case[0]['field_batches']))+' dw 0\n'+marker)
   if a.allocation_probe:
    marker='get_input_injected: dw 0';assert observer_source.count(marker)==1
    observer_source=observer_source.replace(marker,'get_allocation_probe: times '+str(len(allocation_names))+' dw 0\n'+marker)
    for index,(symbol,delta) in enumerate(allocation_fields):
     probe+=' mov ax,[es:'+str(child_symbols[symbol]+delta)+']\n mov [cs:get_allocation_probe+'+str(index*2)+'],ax\n'
    trailer=' mov ax,[cs:get_child_ds]\n sub ax,'+str(int(group[1],16)+16)+'\n mov es,ax\n mov dx,[es:0x2c]\n dec ax\n mov es,ax\n mov ax,[es:3]\n mov [cs:get_allocation_probe+22],ax\n mov ax,dx\n dec ax\n mov es,ax\n mov cx,[es:3]\n mov [cs:get_allocation_probe+24],cx\n mov word [cs:get_allocation_probe+26],0xffff\n cmp cx,1\n jb .get_env_done\n cmp cx,2048\n ja .get_env_done\n shl cx,1\n shl cx,1\n shl cx,1\n shl cx,1\n dec cx\n mov es,dx\n xor bx,bx\n.get_env_scan:\n cmp bx,cx\n jae .get_env_done\n cmp word [es:bx],0\n je .get_env_found\n inc bx\n jmp .get_env_scan\n.get_env_found:\n add bx,2\n mov [cs:get_allocation_probe+26],bx\n.get_env_done:\n'
    for old_offset,new_offset in ((26,2*len(allocation_fields)+4),(24,2*len(allocation_fields)+2),(22,2*len(allocation_fields))):
     trailer=trailer.replace('[cs:get_allocation_probe+'+str(old_offset)+']','[cs:get_allocation_probe+'+str(new_offset)+']')
    probe+=trailer
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
   if active_case[0] and active_case[0].get('source_memory')=='start' and not active_case[0].get('source_lease'):
    marker=' cmp word [cs:get_finish_phase],0\n jne .done\n mov dx,0x3920';assert finish.count(marker)==1
    finish=finish.replace(marker,' cmp word [cs:get_finish_phase],0\n jne .done\n call get_startup_prompt_probe\n or ax,ax\n jz .done\n mov word [cs:get_startup_prompt_seen],1\n mov dx,0x3920')
    finish+='''
get_startup_prompt_probe:
 push bx
 push cx
 push si
 push di
 push es
 mov ax,0xb800
 mov es,ax
 xor bx,bx
.scan:
 mov di,bx
 mov si,get_startup_prompt_text
 mov cx,21
.compare:
 mov al,[es:di]
 cmp al,[cs:si]
 jne .next
 inc si
 add di,2
 loop .compare
 mov ax,1
 jmp .return
.next:
 add bx,2
 cmp bx,3958
 jbe .scan
 xor ax,ax
.return:
 pop es
 pop di
 pop si
 pop cx
 pop bx
 ret
get_startup_prompt_text: db 'Program could not run.'
'''
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
    if 'policy_width' in active_case[0]:
     marker=' mov ax,0x40\n mov es,ax\n mov bx,[es:0x1c]';assert injector.count(marker)==1
     injector=injector.replace(marker,' mov ax,[es:si+34]\n mov [cs:get_policy_width],ax\n'+marker)
    if active_case[0].get('when_action'):
     marker=' mov ax,0x40\n mov es,ax\n mov bx,[es:0x1c]';assert injector.count(marker)==1
     injector=injector.replace(marker,' mov ax,ss\n mov es,ax\n mov ax,[es:'+str(child_symbols['_runtime_wait_gate'])+']\n or ax,ax\n jnz .when_pending\n mov word [cs:get_when_waiting],1\n jmp .done\n.when_pending:\n cmp ax,1\n jne .done\n cmp word [cs:get_when_waiting],1\n jne .done\n mov [cs:get_when_gate],ax\n'+marker)
    batches=active_case[0].get('field_batches')
    if batches:
     injector=injector.replace(' cmp word [cs:get_input_injected],0\n jne .done',' cmp word [cs:get_input_batch],'+str(len(batches))+'\n jae .done')
     marker=' mov ax,0x40\n mov es,ax\n mov bx,[es:0x1c]'
     assert injector.count(marker)==1
     injector=injector.replace(marker,' mov ax,[es:si+8]\n cmp ax,[cs:get_input_generation]\n je .done\n mov dx,ax\n'+marker)
     for j,batch_words in enumerate(batches):
      assert 0<len(batch_words)<15
      injector+=' cmp word [cs:get_input_batch],'+str(j)+'\n jne .batch_next'+str(j)+'\n mov [cs:get_input_generation],dx\n mov [cs:get_lifetime_generations+'+str(j*2)+'],dx\n'
      for i,word in enumerate(batch_words):
       injector+=' mov word [es:bx],'+str(word)+'\n add bx,2\n cmp bx,0x3e\n jb .batch_key'+str(j)+'_'+str(i)+'\n mov bx,0x1e\n.batch_key'+str(j)+'_'+str(i)+':\n'
      injector+=' mov [es:0x1c],bx\n add word [cs:get_input_injected],'+str(len(batch_words))+'\n inc word [cs:get_input_batch]\n jmp .done\n.batch_next'+str(j)+':\n'
     injector+='.done:\n ret\nget_input_batch: dw 0\nget_input_generation: dw 0\n'
    else:
     assert 0<len(input_words)<15
    for i,word in enumerate(input_words if not batches else []):
     injector+=' mov word [es:bx],'+str(word)+'\n add bx,2\n cmp bx,0x3e\n jb .key'+str(i)+'\n mov bx,0x1e\n.key'+str(i)+':\n'
    if not batches:injector+=' mov [es:0x1c],bx\n mov word [cs:get_input_injected],'+str(len(input_words))+'\n.done:\n ret\n'
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
   if active_case[0] and (active_case[0].get('source_recovery') or active_case[0].get('source_cleanup') or active_case[0].get('source_begin')):
    from compiler_bridge_recovery_observer import attach
    observer_source=attach(observer_source,kind=active_case[0].get('source_begin',active_case[0].get('source_recovery',active_case[0].get('source_cleanup') if isinstance(active_case[0].get('source_cleanup'),str) else 'unlink')),
     parent=json.loads((parent/'manifest.json').read_text()),listing=(parent/'terminal.map').read_text(),
     offsets=offsets,child_symbols=child_symbols,child_group=int(group[1],16))
   if active_case[0] and active_case[0].get('source_reuse'):
    from compiler_bridge_reuse_observer import attach
    observer_source=attach(observer_source,parent=json.loads((parent/'manifest.json').read_text()),listing=(parent/'terminal.map').read_text(),offsets=offsets)
   if active_case[0] and active_case[0].get('source_repeat'):
    from compiler_bridge_repeat_observer import attach
    observer_source=attach(observer_source,count=active_case[0]['source_repeat'],
     parent=json.loads((parent/'manifest.json').read_text()),listing=(parent/'terminal.map').read_text())
   temporary=dict(renderer.__dict__);exec(compile(observer_source,__file__,'exec'),temporary)
   return temporary['observer'](offsets)
  finally:renderer.OUT=previous
 scope.update(adapter=adapter,observer=observer)
 def case_observer(case,offsets):active_case[0]=case;return observer(offsets)
 scope['case_observer']=case_observer
 def kernel_fixture(case,folder):
  path=folder/'PCCOMP.OVL';fault=case.get('source_fault')
  if fault=='missing':path.unlink()
  elif fault in ('corrupt','truncated'):
   data=bytearray(path.read_bytes())
   if fault=='corrupt':data[0]^=1
   else:data.pop()
   path.write_bytes(data)
  case['kernel_fixture_sha256']=sha(path) if path.exists() else None
 scope['kernel_fixture']=kernel_fixture
 if (parent/'PCCOMP.OVL').exists():
  marker="shutil.copyfile(runner,folder/'ASPECT.EXE');";assert source.count(marker)==1
  scope['PARENT_KERNEL']=parent/'PCCOMP.OVL'
  source=source.replace(marker,marker+"shutil.copyfile(PARENT_KERNEL,folder/'PCCOMP.OVL');kernel_fixture(case,folder);")
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
  result['checks']['script_reached_GET_boundary']=(b'GETREADY' in wire)==case.get('expect_GET_boundary',True)
  if a.connected_probe:
   result['CONNECTED_probe_count']=case['CONNECTED_probe_count']
   result['checks']['CONNECTED_raw128_and_long129']=b'BADCARRIER' not in wire
  if get_enabled:result['checks']['BIOS_keys_after_field_admission']=injected==len(case['field_BIOS_words'])
  if case.get('when_action'):
   end=-20-(2*len(allocation_names) if a.allocation_probe else 0)
   waiting,gate=struct.unpack('<2H',(folder/'RENDER.BIN').read_bytes()[end-4:end])
   result['GET_pending_WHEN_gate']=gate
   result['GET_waiting_before_WHEN']=waiting
   result['checks']['field_observed_before_WHEN_CALL']=waiting==1
   result['checks']['WHEN_CALL_staged_before_field_input']=gate==1
   result['checks']['WHEN_transmit_and_worker_exact_once']=wire.count(b'INLINE')==1 and wire.count(b'WORKER')==case.get('when_worker_expected',1)
   result['checks']['no_bad_WHEN_output']=b'BAD' not in wire
  if case.get('when_error'):
   end=-24-(2*len(allocation_names) if a.allocation_probe else 0)
   retirement=list(struct.unpack('<5H',(folder/'RENDER.BIN').read_bytes()[end-10:end]))
   result['GET_error_retirement']=dict(zip(('active','busy','keys','display','completed'),retirement))
   result['checks']['GET_error_owners_retired']=retirement==[0]*5
   result['checks']['WHEN_error_stream_flushed']=(folder/'OWNED.TXT').read_bytes()==bytes.fromhex(case['expected_owned_hex'])
   result['checks']['error_matches_child_probe']=result['child_exit_probe']['error']==case['expected_exit']
  if case.get('field_batches'):
   count=len(case['field_batches']);end=-20-(2*len(allocation_names) if a.allocation_probe else 0)
   generations=list(struct.unpack('<'+str(count)+'H',(folder/'RENDER.BIN').read_bytes()[end-2*count:end]))
   result['GET_generations']=generations
   result['checks']['fresh_GET_generation_per_field']=generations==list(range(1,count+1))
   result['checks']['all_field_generations_completed']=injected==len(case['field_BIOS_words'])
   result['checks']['no_bad_transition_output']=b'BAD' not in wire
  if case.get('source_memory'):
   end=-20-(2*len(allocation_names) if a.allocation_probe else 0)
   largest,attempts,prompt_seen=struct.unpack('<3H',(folder/'RENDER.BIN').read_bytes()[end-6:end])
   result['compiler_EXEC_memory']=dict(largest_free_bytes=largest*16,attempts=attempts,startup_prompt_seen_before_ack=prompt_seen)
   if case['source_memory']=='start' and not case.get('source_lease') and not case.get('source_reuse'):
    result['startup_error_retained_after_return']=result['checks'].pop('typed_error_stays_in_parent')
    result['checks']['startup_error_restored_view']=not result['startup_error_retained_after_return']
    result['startup_prompt_visibility_established']=prompt_seen==1
   expected_attempts=1 if case.get('source_reuse') else 0 if case.get('source_begin') or case.get('source_fault') in ('missing','corrupt','truncated') else case.get('source_repeat',1)
   result['checks']['actual_compiler_EXEC_attempt']=attempts==expected_attempts and result['child_exit_probe']['compiler_calls']==expected_attempts and sum(n.upper().endswith('ASPCOMP.EXE') for n in result['observed_EXEC_names'])==expected_attempts
   if not case.get('source_lease') and not case.get('source_cleanup'):result['checks']['no_failed_compiler_publication']=not (folder/'LOGIN.ASX').exists() if case['source_memory']=='start' else (folder/'NEXT.ASX').read_bytes()==renderer.compile_source('proc main\ntransmit "STALE"\nendproc\n')
   result['checks']['no_stale_or_trailing_execution']=b'STALE' not in wire and b'BADRETURN' not in wire
   result['checks']['compiler_log_retired']=not list(folder.glob('LPC*.LOG'))
   if case['source_memory']=='execute':
    # Successful lease cases may continue writing the edited GET value through
    # this same stream. Refusal cases must flush only their original prefix.
    continued=bool(case.get('source_lease') and a.stream_probe)
    expected=b'BEFORE|'+(bytes.fromhex(case['expected_value_hex']) if continued else b'')
    result['checks']['source_success_stream_retained' if continued else 'source_failure_stream_flushed']=(folder/'OWNED.TXT').read_bytes()==expected
   if a.allocation_probe and not case.get('source_lease') and not case.get('source_fault') and not case.get('source_cleanup') and not case.get('source_begin'):result['checks']['compiler_native_heap_error']=result['allocation_probe']['_runtime_compiler_exit']==65535 and result['allocation_probe']['_runtime_compiler_dos_error']==5
  if case.get('source_repeat'):
   from compiler_bridge_repeat_observer import FIELDS,WORDS
   from compiler_bridge_recovery_observer import PREFIX
   count=case['source_repeat'];end=-20-2*len(allocation_names)-6
   raw=(folder/'RENDER.BIN').read_bytes()[end-2*count*WORDS:end]
   snapshots=[]
   for at in range(count):
    words=struct.unpack_from('<'+str(WORDS)+'H',raw,at*WORDS*2)
    snapshots.append(dict(sample=dict(zip(FIELDS,words[:len(FIELDS)])),kernel=dict(zip(PREFIX,words[len(FIELDS):]))))
   result['compiler_repeat']=snapshots
   result['checks']['distinct_kernel_nonce_each_compile']=[row['kernel']['token'] for row in snapshots]==list(range(1,count+1))
   result['checks']['one_interpreter_owns_every_loan']=all(row['sample']['child_ss']==row['sample']['child_ds']==result['child_exit_probe']['DS'] and row['sample']['current_psp']==row['kernel']['owner'] and row['sample']['parent_mcb_owner']==row['kernel']['parent']==result['passive_observer_header'][5] for row in snapshots)
   result['checks']['every_compile_uses_lent_parent']=all(row['kernel']['cookie']==0x434c and row['kernel']['phase']==2 and row['kernel']['valid']==row['kernel']['busy']==0 and row['kernel']['created']==1 and row['sample']['parent_extent']==row['kernel']['keep'] for row in snapshots)
   trusted=json.loads((parent/'manifest.json').read_text())
   result['checks']['every_loan_matches_trusted_bounds']=all(row['kernel']['keep']==trusted['experimental_compiler_lease_module']['keep_paragraphs'] and row['kernel']['full']==trusted['memory_layout']['retained_parent_paragraphs'] for row in snapshots)
   result['checks']['repeat_compiler_staging_retired']=not list(folder.glob('LPC*.*'))
   result['checks']['single_ASPECT_EXEC']=sum(name.upper().endswith('ASPECT.EXE') for name in result['observed_EXEC_names'])==1
   result['checks']['no_stale_or_bad_chain_output']=b'STALE' not in wire and b'BAD' not in wire
   for leaf,source_text in case['scripts'].items():
    result['checks']['compiled_chain_'+leaf+'_exact']=(folder/(leaf+'.ASX')).read_bytes()==renderer.compile_source(source_text,enable_get=True)
    del result['checks']['fixture_unchanged_'+leaf+'.ASX']
   for leaf,value in case['source_outputs'].items():result['checks']['stream_'+leaf+'_closed_exact']=(folder/leaf).read_bytes()==bytes.fromhex(value)
  failure_probe=result['child_exit_probe']
  if case.get('source_reuse'):
   from compiler_bridge_reuse_observer import FIELDS as RF,WORDS as RW
   from compiler_bridge_recovery_observer import WORDS as FW,PREFIX
   end=-20-2*len(allocation_names)-6-2*FW
   words=struct.unpack('<'+str(RW)+'H',(folder/'RENDER.BIN').read_bytes()[end-2*RW:end])
   reuse=dict(zip(RF,words[:len(RF)]));at=len(RF)
   first_header=list(words[at:at+7]);at+=7
   failure_probe=dict(zip(('DS','errno','error','opcode','compiler_calls','file_status'),words[at:at+6]));at+=6
   second=dict(zip(PREFIX,words[at:]))
   result['compiler_reuse']=dict(sample=reuse,first_header=first_header,first_probe=failure_probe,second_kernel=second)
  if case.get('source_begin'):
   from compiler_bridge_recovery_observer import FIELDS,PREFIX,WORDS,KINDS
   end=-20-2*len(allocation_names)-6
   words=struct.unpack('<'+str(WORDS)+'H',(folder/'RENDER.BIN').read_bytes()[end-2*WORDS:end])
   sample=dict(zip(FIELDS,words[:len(FIELDS)]));prefix=dict(zip(PREFIX,words[len(FIELDS):]))
   result['prepare_failure']=dict(kind=case['source_begin'],sample=sample,kernel=prefix)
   trusted=json.loads((parent/'manifest.json').read_text())
   result['checks']['prepare_fault_injected_once']=sample['kind']==KINDS[case['source_begin']] and sample['injected']==1 and sample['unsafe']==0
   result['checks']['prepare_never_lends_parent']=sample['parent_resize_calls']==0 and sample['parent_extent']==prefix['full']==trusted['memory_layout']['retained_parent_paragraphs'] and prefix['keep']==trusted['experimental_compiler_lease_module']['keep_paragraphs']
   result['checks']['prepare_failure_keeps_valid_owned_state']=prefix['cookie']==0x434c and prefix['phase']==1 and prefix['valid']==prefix['busy']==1 and prefix['parent']==result['passive_observer_header'][5] and sample['current_psp']==prefix['owner']
   result['checks']['prepare_failure_returns_IO']=failure_probe['error']==5 and result['allocation_probe']['_runtime_compiler_exit']==result['allocation_probe']['_runtime_compiler_dos_error']==0
   result['checks']['prepare_cleanup_retires_state']=sample['retired_phase']==sample['retired_busy']==0 and sample['retired_dos_error']==(0 if case['source_begin']=='short-write' else 5)
   result['checks']['prepare_never_quarantines']=sample['prompt_seen']==sample['hold_ticks']==sample['retry_key']==0
   result['checks']['prepare_preserves_exact_display']=sample['captured_cells']==sample['display_cells']==2000 and sample['display_checked']==sample['display_valid']==sample['display_cursor_ok']==sample['display_shape_ok']==1
   result['checks']['partial_backup_and_log_retired']=not list(folder.glob('LPM*.TMP')) and not list(folder.glob('LPC*.*'))
   if case['source_begin']=='create':result['checks']['exclusive_creation_denied']=sample['backup_create_calls']==1 and prefix['created']==0 and prefix['handle']==65535 and sample['backup_write_calls']==0
   elif case['source_begin']=='begin-close':
    result['checks']['backup_handle_actually_closed']=sample['close_calls']==1 and sample['close_probe_error']==6 and prefix['handle']==sample['closed_handle']!=65535 and sample['retired_handle']==65535
    result['checks']['complete_backup_before_close']=sample['backup_position_lo']+65536*sample['backup_position_hi']==(prefix['full']-prefix['keep'])*16
   else:result['checks']['actual_partial_backup_before_failure']=sample['backup_write_calls']==2 and sample['backup_position_lo']==4096 and sample['backup_position_hi']==0 and prefix['created']==1 and prefix['handle']!=65535
  if case.get('source_cleanup'):
   from compiler_bridge_recovery_observer import FIELDS,PREFIX,WORDS,KINDS
   from compiler_lease_module import crc16
   end=-20-2*len(allocation_names)-6
   words=struct.unpack('<'+str(WORDS)+'H',(folder/'RENDER.BIN').read_bytes()[end-2*WORDS:end])
   sample=dict(zip(FIELDS,words[:len(FIELDS)]));prefix=dict(zip(PREFIX,words[len(FIELDS):]))
   backups=list(folder.glob('LPM*.TMP'))
   result['restore_cleanup']=dict(sample=sample,kernel=prefix,backups=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p),crc16=crc16(p.read_bytes())) for p in backups])
   result['checks']['cleanup_error_is_safe_IO']=failure_probe['error']==5 and result['allocation_probe']['_runtime_compiler_exit']==result['allocation_probe']['_runtime_compiler_dos_error']==0
   result['checks']['cleanup_fault_injected_once']=sample['kind']==KINDS['close' if case['source_cleanup']=='close' else 'unlink'] and sample['injected']==1 and sample['unsafe']==0
   result['checks']['backup_handle_actually_closed']=sample['close_calls']==1 and sample['close_probe_error']==6 and prefix['handle']==(sample['closed_handle'] if case['source_cleanup']=='close' else 65535) and sample['retired_handle']==65535
   if case['source_cleanup']=='close':result['checks']['complete_restore_stream_before_close']=sample['backup_position_lo']+65536*sample['backup_position_hi']==(prefix['full']-prefix['keep'])*16
   result['checks']['cleanup_fails_after_valid_restore']=prefix['cookie']==0x434c and prefix['phase']==4 and prefix['valid']==prefix['created']==prefix['busy']==1 and sample['parent_extent']==prefix['full']
   result['checks']['cleanup_error_retires_busy_state']=sample['retired_phase']==4 and sample['retired_dos_error']==5 and sample['retired_busy']==0
   result['checks']['safe_cleanup_does_not_quarantine']=sample['prompt_seen']==sample['hold_ticks']==sample['retry_key']==0
   result['checks']['cleanup_restores_exact_display']=sample['captured_cells']==sample['display_cells']==2000 and sample['display_checked']==sample['display_cursor_ok']==sample['display_shape_ok']==sample['display_valid']==1
   result['checks']['intact_backup_preserved']=len(backups)==1 and backups[0].stat().st_size==(prefix['full']-prefix['keep'])*16 and crc16(backups[0].read_bytes())==prefix['crc']
   result['checks']['compiler_staging_and_log_retired']=not list(folder.glob('LPC*.*'))
   result['checks']['passive_EXEC_observed']=result['passive_observer_header'][:4]==[0x524e,1,1,2]
   leaf='LOGIN' if case['source_memory']=='start' else 'NEXT'
   expected_source=case['source'] if leaf=='LOGIN' else case['scripts']['NEXT']
   result['checks']['compiled_output_published_but_not_executed']=(folder/(leaf+'.ASX')).read_bytes()==renderer.compile_source(expected_source,enable_get=True) and (case.get('source_reuse') or b'Synth42\r' not in wire)
   if leaf=='NEXT':del result['checks']['fixture_unchanged_NEXT.ASX']
  if case.get('source_reuse'):
   trusted=json.loads((parent/'manifest.json').read_text())
   result['checks']['two_real_interpreter_EXECs']=sum(n.upper().endswith('ASPECT.EXE') for n in result['observed_EXEC_names'])==2
   result['checks']['fresh_peer_trigger_for_second_script']=wire.count(b'SECONDREADY')==1
   result['checks']['first_error_observed_before_manual_relaunch']=first_header[:4]==[0x524e,1,1,1+int(bool(case.get('source_cleanup')))] and first_header[6]==failure_probe['error']==5
   result['checks']['first_parent_owners_retired']=reuse['first_jft_equal']==reuse['first_owners_equal']==reuse['first_history_equal']==1
   result['checks']['same_parent_second_interpreter']=reuse['stage']==3 and reuse['prompt_seen']==1 and reuse['first_psp']==reuse['second_psp']==result['passive_observer_header'][5] and reuse['first_ds']==result['passive_observer_header'][4]
   result['checks']['second_real_compiler_lease']=reuse['second_compiler_seen']==1 and second['cookie']==0x434c and second['phase']==2 and second['valid']==second['busy']==0 and second['token']==2 and second['owner']+16+int(group[1],16)==reuse['second_ds']==result['child_exit_probe']['DS'] and second['parent']==reuse['second_psp'] and second['keep']==reuse['second_extent']==trusted['experimental_compiler_lease_module']['keep_paragraphs'] and second['full']==trusted['memory_layout']['retained_parent_paragraphs']
   result['checks']['new_backup_avoids_preserved_name']=second['sequence']==(2 if case.get('source_cleanup') else 1)
   result['checks']['good_source_compiled_exact']=(folder/'GOOD.ASX').read_bytes()==renderer.compile_source(case['scripts']['GOOD'],enable_get=True)
   result['checks']['failed_source_never_executed']=b'BADFIRST' not in wire
   result['checks']['actual_compiler_EXEC_attempt']=result['compiler_EXEC_memory']['attempts']==result['child_exit_probe']['compiler_calls']==1 and sum(n.upper().endswith('ASPCOMP.EXE') for n in result['observed_EXEC_names'])==1+reuse['first_compilers'] and failure_probe['compiler_calls']==reuse['first_compilers']
   result['checks']['second_compiler_and_child_exit']=result['passive_observer_header'][:4]==[0x524e,1,1,2] and result['child_exit_probe']['error']==0 and result['child_exit_probe']['compiler_calls']==1
   result['checks']['passive_EXEC_observed']=result['checks']['second_compiler_and_child_exit']
  if case.get('source_recovery'):
   from compiler_bridge_recovery_observer import FIELDS,PREFIX,WORDS
   end=-20-2*len(allocation_names)-6
   words=struct.unpack('<'+str(WORDS)+'H',(folder/'RENDER.BIN').read_bytes()[end-2*WORDS:end])
   recovery=dict(zip(FIELDS,words[:len(FIELDS)]));prefix=dict(zip(PREFIX,words[len(FIELDS):]))
   result['restore_recovery']=dict(kind=case['source_recovery'],sample=recovery,kernel=prefix)
   result['checks']['restore_fault_injected_once']=recovery['injected']==1
   result['checks']['BIOS_quarantine_observed']=recovery['prompt_seen']==1 and recovery['hold_ticks']>=5
   result['checks']['retry_only_after_quarantine']=recovery['retry_key']==1 and recovery['retry_calls']>=1 and recovery['unsafe']==0
   result['checks']['quarantine_keeps_compiler_scope_and_pause']=recovery['paused']==recovery['scope']==recovery['serial']==recovery['program_active']==1
   result['checks']['quarantine_uses_child_PSP']=recovery['current_psp']==prefix['owner'] and recovery['child_ds']==result['child_exit_probe']['DS']
   result['checks']['quarantine_keeps_invalid_owned_kernel']=prefix['cookie']==0x434c and prefix['parent']==result['passive_observer_header'][5] and prefix['valid']==prefix['busy']==0 and prefix['phase']==(2 if case['source_recovery']=='grow' else 3)
   result['checks']['failed_restore_extent_exact']=recovery['parent_extent']==prefix['keep' if case['source_recovery']=='grow' else 'full']
   trusted=json.loads((parent/'manifest.json').read_text())
   result['checks']['quarantine_kernel_bounds_exact']=prefix['keep']==trusted['experimental_compiler_lease_module']['keep_paragraphs'] and prefix['full']==trusted['memory_layout']['retained_parent_paragraphs']
   result['checks']['quarantine_records_DOS_failure']=prefix['dos_error']==(8 if case['source_recovery']=='grow' else 5)
   result['checks']['quarantine_notice_retired']=b'ASPECT memory restore incomplete.' not in (folder/'SCREEN.BIN').read_bytes()[::2]
   result['checks']['retained_capture_matches_original_display']=recovery['captured_cells']==2000
   result['checks']['exact_display_restored_before_scope_resume']=recovery['display_checked']==recovery['display_valid']==recovery['display_cursor_ok']==recovery['display_shape_ok']==1 and recovery['display_cells']==2000
  if case.get('source_fault'):
   result['source_fault']=case['source_fault']
   result['checks']['source_error_matches_child_probe']=result['child_exit_probe']['error']==case['expected_exit']
   result['checks']['compiler_fault_status_exact']=result['allocation_probe']['_runtime_compiler_exit']==int(case['source_fault']=='compiler-error') and result['allocation_probe']['_runtime_compiler_dos_error']==0
   result['checks']['passive_EXEC_observed']=result['passive_observer_header'][:4]==[0x524e,1,1,1+expected_attempts]
   result['checks']['compiler_staging_and_log_retired']=not list(folder.glob('LPC*.*'))
   result['checks']['backing_files_retired']=not list(folder.glob('LPM*.TMP'))
   path=folder/'PCCOMP.OVL'
   result['checks']['kernel_fault_fixture_unchanged']=(sha(path) if path.exists() else None)==case['kernel_fixture_sha256']
  if case.get('source_lease'):
   # The passive exit counter includes the actual nested compiler as well as
   # ASPECT. Require exactly both exits; precompiled cases retain count one.
   result['checks']['passive_EXEC_observed']=result['passive_observer_header'][:4]==[0x524e,1,1,1+expected_attempts]
   if case['source_memory']=='execute':
    # The deliberately stale fixture must be replaced, with exact new bytes.
    assert 'fixture_unchanged_NEXT.ASX' in result['checks']
    del result['checks']['fixture_unchanged_NEXT.ASX']
   leaf='LOGIN' if case['source_memory']=='start' else 'NEXT'
   expected_source=case['source'] if leaf=='LOGIN' else case['scripts']['NEXT']
   result['checks']['source_compiler_ASX_exact']=(folder/(leaf+'.ASX')).is_file() and (folder/(leaf+'.ASX')).read_bytes()==renderer.compile_source(expected_source,enable_get=True)
   result['checks']['compiler_loaded_from_lent_memory']=largest*16>=75920
   result['checks']['compiler_result_success']=result['allocation_probe']['_runtime_compiler_exit']==0 and result['allocation_probe']['_runtime_compiler_dos_error']==0
   result['checks']['backing_files_retired']=not list(folder.glob('LPM*.TMP'))
   result['checks']['kernel_file_unchanged']=sha(folder/'PCCOMP.OVL')==sha(parent/'PCCOMP.OVL')
  if 'policy_width' in case:
   end=-20-(2*len(allocation_names) if a.allocation_probe else 0)
   width=struct.unpack('<H',(folder/'RENDER.BIN').read_bytes()[end-2:end])[0]
   result['GET_observed_width']=width
   result['checks']['GET_width_matches_policy']=width==case['policy_width']
  if case.get('storage_scope'):
   result['checks']['storage_guards_intact']=b'BAD' not in wire
  if case['success']:
   value=bytes.fromhex(case['expected_value_hex'])
   result['checks']['GET_edited_value_reaches_peer']=b'GETREADY'+value+b'\rSynth42\r' in wire
  else:result['checks']['no_post_GET_execution']=b'Synth42\r' not in wire
  if case['name']=='get-vm-string' and get_enabled and a.stream_probe:result['checks']['shared_FOPEN_GET_scratch_and_stream_retained']=(folder/'OWNED.TXT').is_file() and (folder/'OWNED.TXT').read_bytes()==b'BEFORE|LoC42'
  if a.source_memory_cases:result['compatibility_accepted']=False
  result['passed']=all(result['checks'].values());(folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 report.update(source_lease_reuse_cases=a.source_lease_reuse_cases,source_lease_close_cases=a.source_lease_close_cases,source_lease_begin_cases=a.source_lease_begin_cases,source_lease_repeat_cases=a.source_lease_repeat_cases,source_lease_cleanup_cases=a.source_lease_cleanup_cases,source_lease_recovery_cases=a.source_lease_recovery_cases,source_lease_fault_cases=a.source_lease_fault_cases,source_lease_cases=a.source_lease_cases,source_memory_cases=a.source_memory_cases,source_compiler_residency_verified=all(r['passed'] for r in report['cases']) if a.source_lease_cases else False if a.source_memory_cases else None,policy_cases=a.policy_cases,storage_cases=a.storage_cases,when_error_cases=a.when_error_cases,when_cases=a.when_cases,lifetime_cases=a.lifetime_cases,passed=all(r['passed'] for r in report['cases']),GET_VM=get_enabled,allocation_probe=a.allocation_probe,stream_probe=a.stream_probe,disabled_control=a.disabled_control,compiler_GET_enabled=bool(a.get_compiler_dir),compiled_GET_cases=len(dos_compiled),GET_compiler_sha256=get_compiler_manifest['binary_sha256'] if get_compiler_manifest else None,emulated_cpu=a.cpu,
  CONNECTED_probe=a.connected_probe,checker_sha256=sha(__file__),scope=__doc__+(' Five ordinary cases can use real DOS/Python GET compilation; malformed EOF remains an explicitly authored input.' if a.get_compiler_dir else '')+' Actual parent, child, native dispatcher, GET bank, typed operands, DOS files/heap, UART/parser, BIOS keys and passive return observer. Synthetic modem peer; not physical Boca/ATA/SynthModem/BBS acceptance.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 if a.source_memory_cases:
  report['scope']+=' Expected memory-refusal diagnostic, not compiler residency acceptance. Startup post-return error retention is sampled; a zero prompt observation does not establish pre-return message absence.'
  (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Source compiler memory-refusal diagnostic:' if a.source_memory_cases else 'GET full VM:',len(report['cases']),'cases',report['passed'])
 return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
