#!/usr/bin/env python3
"""Apply a directory selection, change CWD, then dial and run its canonical script."""
import argparse,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm,directory
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def action(command):
 raw=bytearray(540)
 for i in range(10):struct.pack_into('<H',raw,i*54,3)
 struct.pack_into('<H',raw,0,1);raw[2:2+len(command)]=command;return bytes(raw)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--case',choices=['canonical-ASX','compiled-ASP','changed-ASX-refused']);a=p.parse_args()
 package=a.package.resolve();m=json.loads((package/'manifest.json').read_text());assert m.get('experimental_directory_adopt')
 for n,h in m['files'].items():assert sha(package/'PCPLUSSE'/n)==h,n
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 harness.BINARY=package/'PCPLUSSE/TERMINAL.EXE';reports=[]
 from test_directory_resource_owner_dos import FIELDS
 terminal=ROOT/'build'/m['products']['TERMINAL.EXE']['folder'];syms={n:(int(seg,16),int(off,16)) for seg,off,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(terminal/'terminal.map').read_text(),re.M|re.I)}
 ds=syms['terminal_stack_top'][0];field_bytes=sum(size for _,size in FIELDS)
 defs=dict(RESOURCE_KIND=8,PREVIEW_KEY=ord('A'),BUNDLE_BYTES=2024,RESOURCE_BYTES=272,TRANSFER=syms['_terminal_transfer_preferences'][1],ACTUAL_BAUD=syms['terminal_baud_low'][1],OWNER=syms['_terminal_directory_resources'][1],RESOURCE=syms['_directory_resource_result'][1],PROGRAM_PENDING=syms['terminal_program_pending'][1],PROGRAM_ACTIVE=syms['terminal_program_active'][1],PROGRAM_KIND=syms['terminal_program_kind'][1],PROGRAM_STATUS=syms['terminal_program_status'][1],REDISPLAY_ACTIVE=syms['_redisplay_active'][1],COMMAND_ACTIVE=syms['_command_menu_active'][1],CONNECTION=syms['connection_state'][1],FIELD_BYTES=field_bytes,FIELD_COUNT=len(FIELDS),FROZEN_RELATIVE=syms['redisplay_snapshot'][0]-ds,FROZEN_OFFSET=syms['redisplay_snapshot'][1],ADOPT_SCRIPT_RELATIVE=syms['directory_adopt_script_storage'][0]-ds,ADOPT_SCRIPT_OFFSET=syms['directory_adopt_script_storage'][1])
 (out/'owner-watch.inc').write_text(''.join(f'%define {n} {v}\n' for n,v in defs.items()));(out/'owner-fields.inc').write_text(''.join(f'dw {syms[n][1]},{size}\n' for n,size in FIELDS))
 subprocess.run(['nasm','-fbin','-I'+str(out)+'/',str(ROOT/'standalone/directory_adopt_connection_watch.asm'),'-o',str(out/'WATCH.COM')],check=True)

 good_source='proc main\nfopen 0 "D:\\CANON.OK" "wb"\nfputs 0 "CANONICAL"\nfclose 0\nendproc\n';good=compile_source(good_source)
 bad=compile_source('proc main\nfopen 0 "D:\\EVIL.OK" "wb"\nfputs 0 "WRONG FILE"\nfclose 0\nendproc\n')
 for name in ([a.case] if a.case else ['canonical-ASX','compiled-ASP','changed-ASX-refused']):
  raw=bytearray(directory(port=3,baud=5));raw[250+0x34:250+0x3d]=b'GO'.ljust(9,b'\0');raw[250+0x56:250+0x5f]=b'DOIT'.ljust(9,b'\0')
  settings=bytearray(prm(port=3,baud=5));struct.pack_into('<H',settings,0x188,5);struct.pack_into('<HH',settings,0x4e4,8,4)
  source=name!='canonical-ASX';command=b'COPY /B /Y D:\\BAD.ASX D:\\GO.ASX' if name=='changed-ASX-refused' else b'CD D:\\OTHER'
  files={'WATCH.COM':(out/'WATCH.COM').read_bytes(),'DOIT.KEY':action(command),'OTHER/GO.ASX':bad,'OTHER/KEEP.BIN':b'UNTOUCHED'}
  files['GO.ASP' if source else 'GO.ASX']=good_source.encode() if source else good
  if name=='changed-ASX-refused':files['BAD.ASX']=bad
  path_keys=' '.join(['bs']*10)+' T E S T . D I R'
  keys='p900 enter p900 a-d p400 '+path_keys+' enter p6500 enter p1800 a p6500 space p800 a-1 p1800 space p600 ` p300 tab p300 d p4500 '+('space p500 ' if name=='changed-ASX-refused' else '')+'a-h p1700 a-x'
  cohort=out.name+'-'+name;assert not (ROOT/'build/connection-dos'/cohort).exists()
  proof=harness.run(cohort,'hangup',keys,directory=bytes(raw),prm=bytes(settings),arguments='@D:\\TEST.PRM',com=3,irq=5,cpu='8086',working_drive='d',files=files,accounting_delta=1,timeout=45,emulated_modem=True,observer='WATCH')
  drive=ROOT/'build/connection-dos'/cohort
  observed=(drive/('OWNER.BIN' if (drive/'OWNER.BIN').exists() else 'OTHER/OWNER.BIN')).read_bytes();print(name,'observer',struct.unpack_from('<7H',observed),flush=True);assert struct.unpack_from('<7H',observed)[1]==7 and not struct.unpack_from('<7H',observed)[5],name
  checks=dict(proof['checks']);checks.update(selected_target_dialed=bool(proof['checks'].get('emulated_modem_connected_to_selected_endpoint')),wrong_script_never_executed=not (drive/'EVIL.OK').exists())
  if name=='changed-ASX-refused':checks.update(changed_compiled_script_not_executed=not (drive/'CANON.OK').exists(),actual_PROGRAM_replaced_ASX=(drive/'GO.ASX').read_bytes()==bad)
  else:checks.update(canonical_script_executed=(drive/'CANON.OK').is_file() and (drive/'CANON.OK').read_bytes()==b'CANONICAL',CWD_decoy_ignored=not (drive/'EVIL.OK').exists())
  if source and name!='changed-ASX-refused':checks['actual_ASPCOMP_produced_exact_ASX']=(drive/'GO.ASX').read_bytes()==good
  report=dict(case=name,passed=all(checks.values()),checks=checks,cohort=str(drive.relative_to(ROOT)),binary_sha256=proof['binary_sha256'],artifacts={str(q.relative_to(drive)):sha(q) for q in drive.rglob('*') if q.is_file()});assert report['passed'],report
  reports.append(report)
 result=dict(passed=True,binary_sha256=m['files']['TERMINAL.EXE'],package_manifest_sha256=sha(package/'manifest.json'),cases=reports,original_inputs=[],sources={n:sha(ROOT/n) for n in ['standalone/directory_adopt_connection_watch.asm','standalone/test_directory_resource_owner_dos.py','standalone/test_directory_adopt_connection_dos.py','standalone/test_connection_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/directory_test_support.py','standalone/test_terminal.py','src/aspect/compiler.py']},scope=__doc__+' Actual DOS8086 COM3/IRQ5 parent, compiler/ASPECT, real PROGRAM CD/COPY and DOSBox modem carrier model and a TCP BBS peer. Same-write CONNECT/banner and actual ANSI replies. No live BBS/SIP/DSP/analog/card acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(reports),'selection/connection/script workflows')
if __name__=='__main__':main()
