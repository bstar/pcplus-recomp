#!/usr/bin/env python3
"""Native offline retirement, logical refresh, setup reuse and recovery behavior."""
import argparse,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import directory,prm
from directory_test_support import accounting_check
from test_directory_resource_owner_dos import FIELDS as BASE_FIELDS
ROOT=harness.ROOT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
FIELDS=BASE_FIELDS+[('directory_pending',1),('directory_pending_count',2),('terminal_exit_code',2),('terminal_quit',2),('terminal_sink_398a_enabled',2),('_capture_file_result',96)]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 package=a.package.resolve();manifest=json.loads((package/'manifest.json').read_text());assert manifest['experimental_directory_retirement']
 product=ROOT/'build'/manifest['products']['TERMINAL.EXE']['folder'];parent=json.loads((product/'manifest.json').read_text())
 for n,h in parent['sources'].items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 syms={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(product/'terminal.map').read_text(),re.M|re.I)}
 definitions={name:syms[symbol][1] for name,symbol in [('RETIRE','_terminal_directory_retirement'),('ACCOUNT','directory_account_result'),('PROGRAM_PENDING','terminal_program_pending'),('PROGRAM_ACTIVE','terminal_program_active'),('PROGRAM_KIND','terminal_program_kind'),('PROGRAM_STATUS','terminal_program_status'),('REDISPLAY','_redisplay_active'),('COMMAND','_command_menu_active'),('CONNECTION','connection_state')]}
 sizes={};field_bytes=0
 for name,size in FIELDS:sizes[name]=(field_bytes,size);field_bytes+=size
 definitions.update(FIELD_BYTES=field_bytes,FIELD_COUNT=len(FIELDS))
 (out/'retire-watch.inc').write_text(''.join(f'%define {n} {v}\n' for n,v in definitions.items()))
 (out/'retire-fields.inc').write_text(''.join(f'dw {syms[n][1]},{size}\n' for n,size in FIELDS))
 reports=[];harness.BINARY=package/'PCPLUSSE/TERMINAL.EXE'
 for mode in ('normal','counter-wrap','capture-preserved','existing-backup','installed-cleanup-error'):
  observer=out/('FAULT.COM' if mode=='installed-cleanup-error' else 'RETWATCH.COM')
  subprocess.run(['nasm','-fbin','-I'+str(out)+'/',*(['-DFAIL_BACKUP_DELETE']if mode=='installed-cleanup-error' else[]),str(ROOT/'standalone/directory_retirement_watch.asm'),'-o',str(observer)],check=True)
  raw=bytearray(directory(port=3,baud=5));raw[250+0x34:250+0x3d]=b'CHDIR\0\0\0\0'
  if mode=='counter-wrap':struct.pack_into('<H',raw,250+70,65535)
  settings=bytearray(prm(port=3,baud=5));struct.pack_into('<H',settings,0x188,5);struct.pack_into('<HH',settings,0x4e4,8,4)
  script=compile_source('proc main\nchdir "D:\\OTHER"\nmkdir "WITNESS"\ntransmit "CWD-MOVED^M"\nendproc\n')
  name=out.name+'-'+mode;drive=ROOT/'build/connection-dos'/name;assert not drive.exists()
  keys='p900 enter p3200 a-h p3000 '+('a-s p900 escape p1100 space p800 ' if mode=='normal' else '')+'a-x'
  if mode=='capture-preserved':keys='p900 enter p2400 a-f1 p500 c a p t u r e . l o g enter p800 a-h p3000 a-x'
  conflict=mode=='existing-backup';failure=mode in ('existing-backup','installed-cleanup-error');delta=0 if conflict else 1
  base=harness.run(name,'hangup',keys,directory=bytes(raw),prm=bytes(settings),arguments='@D:\\TEST.PRM /E:TEST.DIR /N:1',com=3,irq=5,cpu='8086',working_drive='d',expected=9 if failure else 0,
   files={'CHDIR.ASX':script,'OTHER/TEST.DIR':bytes(raw),'RETWATCH.COM':observer.read_bytes()},observer='RETWATCH',recovery_conflict=conflict,accounting_delta=delta)
  observed=(drive/'RETIRE.BIN').read_bytes();assert len(observed)==14+2*field_bytes+30+4000
  magic,flags,io_calls,violations,setup_execs,faults,appds=struct.unpack_from('<7H',observed)
  before=observed[14:14+field_bytes];after=observed[14+field_bytes:14+2*field_bytes];at=14+2*field_bytes
  retired=struct.unpack_from('<5H',observed,at);account=struct.unpack_from('<10H',observed,at+10);notice=observed[at+30:at+4030]
  actual=(drive/'TEST.DIR').read_bytes();expected=bytearray(before)
  installed=not conflict
  if installed:
   stats=actual[250+61:250+72]
   for field,offset in [('terminal_directory_plan',100+61),('terminal_directory_context',252+61)]:
    pos=sizes[field][0]+offset;expected[pos:pos+11]=stats
   for field in ('directory_pending','directory_pending_count'):
    pos,size=sizes[field];expected[pos:pos+size]=bytes(size)
  if failure:
   pos,size=sizes['terminal_exit_code'];expected[pos:pos+size]=struct.pack('<H',9)
  checks=dict(base['checks']);checks.update(observer_valid=magic==0x5254 and appds!=0,
   before_after_return_observed=flags&7==7,all_account_IO_quiesced=io_calls>0 and not violations,
   exact_active_changes_only=after==expected,retirement_completed=retired==(4 if failure else 3,3 if failure else 0,13 if mode=='installed-cleanup-error' else account[0] if conflict else 0,1,int(installed)),
   actual_child_CWD_changed=(drive/'OTHER/WITNESS').is_dir() and b'CWD-MOVED\r' in (drive/'serial.bin').read_bytes(),
   setup_reused_reconciled_context=setup_execs==(1 if mode=='normal' else 0),declared_fault_only=faults==int(mode=='installed-cleanup-error'),
   visible_error_notice=(flags&8!=0 and b'Log save error' in notice[::2]) if failure else flags&8==0,
   source_accounted_exactly_once=actual==raw if conflict else accounting_check(raw,actual,1),
   decoy_unchanged=(drive/'OTHER/TEST.DIR').read_bytes()==raw)
  backup=drive/'PCPBAK.$$$'
  checks['recovery_backup_preserved']=(backup.read_bytes()==raw if mode=='installed-cleanup-error' else backup.read_bytes()==b'SYNTHETIC RECOVERY CONFLICT' if conflict else not backup.exists())
  if mode=='capture-preserved':
   pos,_=sizes['terminal_sink_398a_enabled'];cap,_=sizes['_capture_file_result']
   checks['capture_stayed_open']=before[pos:pos+2]==after[pos:pos+2]==b'\x01\x00' and struct.unpack_from('<H',after,cap)[0]==1 and struct.unpack_from('<H',after,cap+10)[0]==1
   checks['capture_file_created']=(drive/'OTHER/CAPTURE.LOG').is_file()
  report=dict(case=mode,passed=all(checks.values()),checks=checks,observer_flags=flags,DOS_operations=io_calls,violations=violations,setup_EXECs=setup_execs,injected_faults=faults,retirement=retired,accounting=account,cohort=str(drive.relative_to(ROOT)),artifacts={str(q.relative_to(drive)):sha(q) for q in drive.rglob('*') if q.is_file()})
  reports.append(report);(out/(mode+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(mode,json.dumps({k:v for k,v in checks.items() if not v}),flush=True)
  assert report['passed'],mode
 result=dict(passed=True,cases=reports,binary_sha256=manifest['files']['TERMINAL.EXE'],package_manifest_sha256=sha(package/'manifest.json'),
  sources={n:sha(ROOT/n) for n in ['standalone/test_directory_retirement_dos.py','standalone/directory_retirement_watch.asm','standalone/test_connection_dos.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/test_directory_resource_owner_dos.py','src/aspect/compiler.py']},
  scope=__doc__+' Actual DOS8086 COM3/IRQ5 parent, ASPECT CWD change, user hangup and real filesystem; normal case then launches/cancels PRMEDIT to prove the frozen setup context was reconciled. Passive DOS/timer observer except one explicit backup-delete error in the cleanup case. No analog/hardware/full-application acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(reports),'offline retirement workflows')
if __name__=='__main__':main()
