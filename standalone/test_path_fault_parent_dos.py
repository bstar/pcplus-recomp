#!/usr/bin/env python3
"""Unchanged application through one-shot INT21 path faults in actual DOS8086."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
ROOT=harness.ROOT
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',type=int,choices=(1,2,3,4))
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['binary_sha256']==sha(binary) and manifest['experimental_path_control']
 out.mkdir(parents=True);package=out/'package';package.mkdir();shutil.copyfile(binary,package/'TERMINAL.EXE')
 witness=out/'WITNESS.COM'
 subprocess.run(['nasm','-fbin',str(ROOT/'standalone/path_fault_witness.asm'),'-o',str(witness)],check=True)
 keys_file=bytearray(540)
 for i in range(10):struct.pack_into('<H',keys_file,54*i,3)
 struct.pack_into('<H',keys_file,0,1);command=b'D:\\WITNESS.COM';keys_file[2:2+len(command)]=command
 settings=bytearray(prm(port=3,baud=5))
 for at,val in ((0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)):
  struct.pack_into('<H',settings,at,val)
 harness.BINARY=package/'TERMINAL.EXE';cases=[]
 for mode in (a.mode,) if a.mode else (1,2,3,4):
  fault=out/('fault'+str(mode)+'.COM');watch=out/('watch'+str(mode)+'.COM')
  subprocess.run(['nasm','-fbin','-DPATH_FAULT_MODE='+str(mode),str(ROOT/'standalone/path_fault_boundary.asm'),'-o',str(fault)],check=True)
  subprocess.run(['nasm','-fbin','-DWATCH_KIND='+('7' if mode==1 else '1'),str(ROOT/'standalone/path_dialog_watch.asm'),'-o',str(watch)],check=True)
  files={'PATHFLT.COM':fault.read_bytes(),'PATHOBS.COM':watch.read_bytes(),'WITNESS.COM':witness.read_bytes(),'TEST.KEY':bytes(keys_file),'OTHER/KEEP.TXT':b'owned fault fixture\r\n'}
  name=out.name+'-'+str(mode);drive=ROOT/'build/connection-dos'/name;assert not drive.exists()
  keys='p900 enter p3500 a-f7 p900 o t h e r enter'
  if mode==1:keys+=' p1000 o t h e r enter p700 a-1 p1200 space'
  if mode==2:keys+=' p100 a-1'
  if mode!=2:keys+=' p700 r e a d y enter p1000 a-x'
  base=harness.run(name,'success',keys,prm=bytes(settings),arguments='@TEST.PRM /T:TEST.KEY /D:CaseTest:23',
   com=3,irq=5,cpu='8086',working_drive='d',files=files,auxiliary=('PATHFLT',),observer='PATHOBS',
   expected=0 if mode==1 else 17,timeout=30,
   online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-FAULT-RETRY\x1b[6n'),) if mode!=2 else ())
  raw=(drive/'PATHVIEW.BIN').read_bytes();frame=raw[6:4006]
  stats=struct.unpack('<7H',(drive/'PATHFLT.BIN').read_bytes());magic,phase,others,roots,qfaults,nfaults,restored=stats
  wire=(drive/'serial.bin').read_bytes();checks=dict(base['checks'])
  checks.update(interrupt_boundary_restored=magic==0x5046 and restored==1,
   default_drive_preserved=raw[4006]==3,
   final_CWD_matches_restore_result=raw[4007:].split(b'\0',1)[0]==(b'OTHER' if mode==3 else b''),
   requested_change_reached_actual_DOS=others==(2 if mode==1 else 1),
   injected_query_faults=qfaults==(0 if mode==3 else 1),
   injected_native_faults=nfaults==(1 if mode in (2,3) else 0),
   actual_root_restore_calls=roots==({1:2,2:1,3:0,4:1}[mode]),
   final_fault_phase=phase==({1:4,2:4,3:3,4:5}[mode]),
   passive_observer_captured_popup=struct.unpack_from('<H',raw,2)[0]==3)
  if mode==1:
   notice=b'Change failed; previous directory restored.'
   checks.update(verified_rollback_notice=frame[1286:1286+2*len(notice):2]==notice,
    retry_keeps_session_usable=wire.count(b'ready\r')==1 and b'\x1b[3;18R' in wire,
    verified_rollback_allows_PROGRAM=(drive/'WITNESS.TXT').exists() and (drive/'WITNESS.TXT').read_bytes()==b'PROGRAM accepted after verified rollback\r\n')
  if mode==2:checks['fatal_rollback_does_not_run_queued_PROGRAM']=not (drive/'WITNESS.TXT').exists()
  if mode in (3,4):checks['successful_change_remains_usable_before_shutdown']=wire.count(b'ready\r')==1
  result=dict(mode=mode,passed=all(checks.values()),checks=checks,stats=dict(phase=phase,OTHER_successes=others,root_successes=roots,query_faults=qfaults,native_faults=nfaults),result=str(drive/'result.json'))
  cases.append(result);(out/('mode'+str(mode)+'.json')).write_text(json.dumps(result,indent=2)+'\n')
  print(mode,{k:v for k,v in checks.items() if not v},flush=True);assert result['passed'],result
 sources=('standalone/test_path_fault_parent_dos.py','standalone/path_fault_boundary.asm','standalone/path_fault_witness.asm','standalone/path_dialog_watch.asm','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py')
 (out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),cases=cases,
  sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Synthetic serial peer. The shim changes only owned test state and selected DOS results, never product memory/code. Not physical DOS failure acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
