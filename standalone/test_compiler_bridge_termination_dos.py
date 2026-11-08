#!/usr/bin/env python3
"""Force real DOS termination of ASPECT while a compiler loan is active.

Expected fail-stop only. Never treats lack of normal exit/hardware restoration
as normal success; an owned TSR must record the specific fatal state first.
"""
import argparse, hashlib, json, os, re, shutil, struct, subprocess, time, types
from pathlib import Path
import test_aspect_renderer_dos as renderer
from compiler_bridge_recovery_observer import PREFIX
from compiler_lease_module import crc16

ROOT=renderer.ROOT
FATAL=b'\r\nParent memory restore incomplete. Reboot required.\r\n'
FIELDS=['parent_psp','parent_ds','child_psp','child_ds','child_paras','aspect_execs',
 'compiler_execs','compiler_exits','compiler_code','killed','injection_point','kill_ss','kill_extent','restore_reads','restore_position','aspect_exits','aspect_code',
 'guard_seen','guard_ticks','ier','irq_offset','irq_segment','current_psp','parent_extent',
 'parent_owner','post_dos','post_resizes','post_reads','post_writes','outside_retained',
 'text_count','video_other','video_overflow','before_attrs','after_attrs','before_row',
 'before_col','after_row','after_col','before_history_offset','before_history_segment',
 'after_history_offset','after_history_segment','write_error','observer_segment']
REPORT_BYTES=4+2*len(FIELDS)+56+128+4000
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('parent','child','compiler','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--case',action='append',choices=('startup-status','execute-status','startup-restore','execute-restore'))
 a=p.parse_args();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifests=[]
 for folder,leaf in ((a.parent,'TERMINAL.EXE'),(a.child,'ASPECT.EXE'),(a.compiler,'ASPCOMP.EXE')):
  m=json.loads((folder/'manifest.json').read_text());assert sha(folder/leaf)==m['binary_sha256'] and m.get('original_inputs',[])==[]
  for name,digest in m['sources'].items():assert sha(ROOT/name)==digest,name
  manifests.append(m)
 parent,child,compiler=manifests
 assert parent['experimental_compiler_lease_bridge'] and child['experimental_compiler_parent_lease']
 out.mkdir();offsets=renderer.map_offsets(a.parent/'terminal.map')
 listing=(a.parent/'terminal.map').read_text()
 match=re.search(r'^([0-9a-f]+):([0-9a-f]+)\s+_compiler_lease_storage\b',listing,re.M);assert match
 segment,offset=(int(n,16) for n in match.groups())
 group=re.search(r'DGROUP\s+([0-9a-f]+):', (a.child/'ASPECT.map').read_text(),re.I);assert group
 constants=dict(PROCESS_PSP=offsets['process_psp'],CHILD_GROUP=int(group[1],16),KERNEL_SEGMENT=segment,KERNEL_OFFSET=offset,
  FULL_PARAS=parent['memory_layout']['retained_parent_paragraphs'],KEEP_PARAS=parent['experimental_compiler_lease_module']['keep_paragraphs'],
  ATTRS=offsets['screen_attribute_cells'],ROW=offsets['screen_cursor_row'],COL=offsets['screen_cursor_column'],
  HISTORY=offsets['terminal_history_pointer'],IER_PORT=offsets['uart_port_ier'],IRQ_VECTOR=offsets['terminal_irq_vector'],FATAL_LENGTH=len(FATAL))
 assert (segment*16+offset+28+15)//16+16<=constants['KEEP_PARAS']
 observer_path=ROOT/'standalone/compiler_bridge_termination_observer.asm'
 results=[]
 for case in a.case or ('startup-status','execute-status','startup-restore','execute-restore'):
  launch,point=case.split('-')
  constants['TERMINATION_POINT']=1 if point=='status' else 2
  asm='\n'.join('%define '+key+' '+str(value) for key,value in constants.items())+'\n'+observer_path.read_text()
  folder=out/case;folder.mkdir()
  for leaf in ('TERMINAL.EXE','PCCOMP.OVL','PCLINE.OVL','PCMETA.OVL'):shutil.copyfile(a.parent/leaf,folder/leaf)
  (folder/'observer.asm').write_text(asm)
  subprocess.run(['nasm','-fbin',str(folder/'observer.asm'),'-o',str(folder/'TERM.COM')],check=True)
  source='proc main\ntransmit "BADRUN"\nendproc\n'
  files={'TERM.COM':(folder/'TERM.COM').read_bytes(),'ASPECT.EXE':(a.child/'ASPECT.EXE').read_bytes(),'ASPCOMP.EXE':(a.compiler/'ASPCOMP.EXE').read_bytes()}
  if launch=='startup':files['LOGIN.ASP']=source.encode()
  else:
   files['LOGIN.ASP']=b'proc main\nexecute "NEXT.ASP"\ntransmit "BADRETURN"\nendproc\n'
   files['LOGIN.ASX']=renderer.compile_source(files['LOGIN.ASP'].decode(),enable_get=True)
   files['NEXT.ASP']=source.encode()
  settings=bytearray(renderer.prm())
  for at,value in ((0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,4),(0x1e6,0),(0x1e4,0)):struct.pack_into('<H',settings,at,value)
  directory=bytearray(renderer.directory(profile=4));directory[302:311]=b'LOGIN\0\0\0\0';directory[325:336]=b'Synth42\0\0\0\0'
  text=(ROOT/'standalone/test_connection_dos.py').read_text()
  marker="out=ROOT/'build/connection-dos'/name";assert text.count(marker)==1;text=text.replace(marker,'out=TERM_OUT/name')
  module=types.ModuleType('termination_peer');module.__file__=str(ROOT/'standalone/test_connection_dos.py');module.TERM_OUT=out
  exec(compile(text,module.__file__,'exec'),module.__dict__)
  observation={}
  def owned_run(argv,**kw):
   if argv[0]!='dosbox-x':return subprocess.run(argv,**kw)
   deadline=time.monotonic()+kw.pop('timeout');process=subprocess.Popen(argv,**kw)
   observation.update(pid=process.pid,reason='exited-before-evidence',alive_before_stop=False)
   try:
    while process.poll() is None:
     evidence=folder/'FATAL.BIN'
     if evidence.exists() and evidence.stat().st_size==REPORT_BYTES:
      observation.update(reason='recorded-fail-stop',alive_before_stop=True);break
     if time.monotonic()>=deadline:observation['reason']='observation-timeout';break
     time.sleep(.05)
   finally:
    if process.poll() is None:
     process.terminate()
     try:process.wait(timeout=2)
     except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
   observation['returncode']=process.returncode
   return subprocess.CompletedProcess(argv,process.returncode)
  module.subprocess=types.SimpleNamespace(run=owned_run);module.BINARY=folder/'TERMINAL.EXE'
  normal=module.run(case,'success','space',directory=bytes(directory),prm=bytes(settings),
   arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',files=files,
   banner=renderer.ESC+b'[2J'+renderer.ESC+b'[HFIRST BYTE SAFE'+renderer.QUERY+renderer.DA+b'LOGIN:',
   profile=4,working_drive='d',observer='TERM',observer_high=True,timeout=40)
  checks=dict(specific_evidence_before_owned_stop=observation['reason']=='recorded-fail-stop' and observation['alive_before_stop'],
   no_normal_completion=not any((folder/name).exists() for name in ('PASS.TXT','FAIL.TXT','AFTER.BIN','SCREEN.BIN')),
   product_unchanged=sha(folder/'TERMINAL.EXE')==parent['binary_sha256'],no_peer_errors=normal['errors']==[],
   actual_init_and_dial=normal['commands']==['ATZ','ATDCaseTest:23'])
  result=dict(case=case,observation=observation,checks=checks,normal_exit_diagnostics=normal['checks'])
  path=folder/'FATAL.BIN'
  if path.exists() and path.stat().st_size==REPORT_BYTES:
   data=path.read_bytes();assert struct.unpack_from('<2H',data)==(0x5446,2)
   words=struct.unpack_from('<'+str(len(FIELDS))+'H',data,4);sample=dict(zip(FIELDS,words));at=4+2*len(FIELDS)
   before=dict(zip(PREFIX,struct.unpack_from('<14H',data,at)));after=dict(zip(PREFIX,struct.unpack_from('<14H',data,at+28)));at+=56
   output=data[at:at+128][:sample['text_count']];video=data[at+128:];wire=(folder/'serial.bin').read_bytes()
   backups=list(folder.glob('LPM*.TMP'))
   irq=sample['irq_segment']+sample['irq_offset']//16
   checks.update(observer_in_UMB=sample['observer_segment']>=0xa000,actual_compiler_success=sample['compiler_execs']==sample['compiler_exits']==1 and sample['compiler_code']==0,
    actual_ASPECT_termination=sample['aspect_execs']==sample['killed']==sample['aspect_exits']==1 and sample['aspect_code']==0x55,
    authenticated_invalid_loan=before['cookie']==0x434c and before['parent']==sample['parent_psp'] and before['owner']==sample['child_psp'] and before['phase']==(2 if point=='status' else 3) and before['valid']==0 and before['busy']==int(point=='restore') and before['keep']==constants['KEEP_PARAS'] and before['full']==constants['FULL_PARAS'],
    invalid_state_preserved=before==after,parent_allocation_owned=sample['parent_owner']==sample['parent_psp'] and before['keep']<=sample['parent_extent']<=before['full'],
    parent_identity_restored=sample['current_psp']==sample['parent_psp'],specific_fatal_notice=sample['guard_seen']==1 and sample['guard_ticks']>=5 and output==FATAL and b'Parent memory restore incomplete.' in video[::2],
    only_fatal_BIOS_output=sample['video_other']==sample['video_overflow']==0,UART_quiet=sample['ier']==0,
    no_freed_child_IRQ=not sample['child_psp']+16<=irq<sample['child_psp']+sample['child_paras'],
    no_retained_model_progress=sample['before_attrs']==sample['after_attrs'] and sample['before_row']==sample['after_row'] and sample['before_col']==sample['after_col'] and sample['before_history_offset']==sample['after_history_offset'] and sample['before_history_segment']==sample['after_history_segment'],
    no_parent_file_IO=sample['post_reads']==sample['post_writes']==0,no_DOS_from_lent_code=sample['outside_retained']==0,
    no_aborted_script_execution=b'BADRUN' not in wire and b'BADRETURN' not in wire,
    complete_backup_preserved=len(backups)==1 and backups[0].stat().st_size==(before['full']-before['keep'])*16 and crc16(backups[0].read_bytes())==before['crc'],report_write_succeeded=sample['write_error']==0)
   checks['injection_context_exact']=sample['injection_point']==constants['TERMINATION_POINT'] and sample['kill_ss']==sample['child_ds' if point=='status' else 'parent_ds'] and sample['kill_extent']==before['keep' if point=='status' else 'full']
   if point=='restore':checks['actual_partial_restore_before_termination']=sample['restore_reads']==2 and sample['restore_position']==4096
   target='LOGIN' if launch=='startup' else 'NEXT';checks['actual_compiler_ASX_exact']=(folder/(target+'.ASX')).read_bytes()==renderer.compile_source(source,enable_get=True)
   result.update(sample=sample,kernel_before=before,kernel_after=after,BIOS_text_hex=output.hex(),report_sha256=sha(path),observer_sha256=sha(folder/'TERM.COM'),
    backups=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in backups])
  result['passed']=all(checks.values());(folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
  print(case,'EXPECTED FAIL-STOP',result['passed'],{k:v for k,v in checks.items() if not v},flush=True)
 report=dict(passed=all(r['passed'] for r in results),cases=results,parent_sha256=parent['binary_sha256'],child_sha256=child['binary_sha256'],compiler_sha256=compiler['binary_sha256'],
  sources={name:sha(ROOT/name) for name in ('standalone/test_compiler_bridge_termination_dos.py','standalone/compiler_bridge_termination_observer.asm','standalone/test_connection_dos.py','standalone/test_aspect_renderer_dos.py')},
  original_inputs=[],physical_verified=False,scope=__doc__+' Synthetic termination at ASPECT AH4D or the second parent restore read after one actual4096-byte restore; owned emulator stop after TSR report, not normal application exit or repair.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
