#!/usr/bin/env python3
"""Actual disconnected Alt-D preview -> PROGRAM resource reads -> exact return."""
import argparse,hashlib,json,os,re,shutil,struct,subprocess,sys
from pathlib import Path
from test_terminal import SAMPLER
from modem_fixtures import fixture as prm
from directory_view_fixture import fixture as directory
from test_directory_resources_dos import keyboard,actions,DISABLED
from test_directory_key_bindings_dos import actions as launch_actions
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
FIELDS=[('terminal_option_mask',2),('terminal_dial_target',64),('terminal_directory_entry',2),
 ('terminal_directory_path',64),('terminal_configuration_values',44),('terminal_modem_settings',368),
 ('terminal_directory_plan',214),('terminal_directory_context',496),('terminal_directory_context_valid',2),
 ('terminal_keymap',948),('terminal_action_definitions',540),('terminal_keyboard_path',64),
 ('terminal_actions_path',64),('_terminal_transfer_preferences',66),('terminal_translation_table',256),('terminal_baud_low',2)]
NAMES=['valid-directory-pair-profile6','invalid-KBD-no-publication','invalid-KEY-no-publication','missing-bindings-reset-defaults',
 'reference-parent-releases-whole-popup','browser-parent-releases-whole-popup','proposal-corrupted-after-queue-before-UART-stage',
 'actual-transfer-changed-after-queue-before-resource-read','actual-DTE-changed-after-queue-before-resource-read']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--case',action='append',help='Run only named workflows');args=p.parse_args()
 binary=args.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text())
 assert manifest['experimental_directory_resource_owner'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 translation=bool(manifest.get('experimental_directory_translation'))
 fields=FIELDS+([('terminal_translation_enabled',2),('terminal_translation_mode',2),('terminal_translation_path',64),('_directory_resource_cli',202)] if translation else [])
 names=NAMES+(['XLT-current-default','XLT-PCPLUS-default','XLT-original-CLI-overrides-mode2','XLT-missing-required','XLT-truncated','XLT-suffixed','XLT-invalid-current-no-fallback','XLT-directory-no-fallback','XLT-mode2-no-read','XLT-mode0-no-read'] if translation else [])
 assert not args.case or set(args.case)<=set(names),'Unknown workflow name'
 bundle_bytes=1948 if translation else 1624;resource_bytes=206 if translation else 142
 out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 syms={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(binary.parent/'terminal.map').read_text(),re.M|re.I)}
 ds=syms['terminal_stack_top'][0];field_bytes=sum(n for _,n in fields)
 assert all(syms[n][0]==ds for n,_ in fields)
 definitions={'BUNDLE_BYTES':bundle_bytes,'RESOURCE_BYTES':resource_bytes,
 'TRANSFER':syms['_terminal_transfer_preferences'][1],'ACTUAL_BAUD':syms['terminal_baud_low'][1],
 'OWNER':syms['_terminal_directory_resources'][1],'RESOURCE':syms['_directory_resource_result'][1],
 'PROGRAM_PENDING':syms['terminal_program_pending'][1],'PROGRAM_ACTIVE':syms['terminal_program_active'][1],
 'PROGRAM_KIND':syms['terminal_program_kind'][1],'PROGRAM_STATUS':syms['terminal_program_status'][1],
 'REDISPLAY_ACTIVE':syms['_redisplay_active'][1],'COMMAND_ACTIVE':syms['_command_menu_active'][1],
 'CONNECTION':syms['connection_state'][1],'FIELD_BYTES':field_bytes,'FIELD_COUNT':len(fields),
 'FROZEN_RELATIVE':syms['redisplay_snapshot'][0]-ds,'FROZEN_OFFSET':syms['redisplay_snapshot'][1]}
 (out/'owner-watch.inc').write_text(''.join(f'%define {n} {v}\n' for n,v in definitions.items()))
 (out/'owner-fields.inc').write_text(''.join(f'dw {syms[n][1]},{size}\n' for n,size in fields))
 subprocess.run(['nasm','-fbin','-I'+str(out)+'/',str(ROOT/'standalone/directory_resource_owner_watch.asm'),'-o',str(out/'WATCH.COM')],check=True)
 sampler=SAMPLER
 for off in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+off),hex(0x3e8+off))
 (out/'sampler.asm').write_text(sampler);subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 table=(ROOT/'src/terminal/key_configuration.asm').read_text().split('keyboard_network_defaults:\n',1)[1]
 (out/'defaults.asm').write_text('BITS 16\n'+table)
 subprocess.run(['nasm','-fbin',str(out/'defaults.asm'),'-o',str(out/'DEFAULTS.BIN')],check=True)
 raw=(out/'DEFAULTS.BIN').read_bytes();default=bytearray(948);at=0;seen=set()
 while raw[at]!=255:
  slot=raw[at];at+=1;assert slot<79 and slot not in seen;seen.add(slot)
  end=raw.index(0,at);assert end-at<12;default[slot*12:slot*12+end-at]=raw[at:end];at=end+1
 assert len(seen)==79 and at+1==len(raw)
 reports=[]
 for mode,name in enumerate(names):
  if args.case and name not in args.case:continue
  case=out/f'T{mode:03}';case.mkdir();shutil.copyfile(binary,case/'TERMINAL.EXE')
  for leaf in ['WATCH.COM','SNAP.COM']:shutil.copyfile(out/leaf,case/leaf)
  if 6<=mode<=8:subprocess.run(['nasm','-fbin',{6:'-DCORRUPT_PROPOSAL',7:'-DCORRUPT_SESSION',8:'-DCORRUPT_BAUD'}[mode],'-I'+str(out)+'/',str(ROOT/'standalone/directory_resource_owner_watch.asm'),'-o',str(case/'WATCH.COM')],check=True)
  subprocess.run(['nasm','-fbin',str(ROOT/'standalone/dos_strategy_sample.asm'),'-o',str(case/'STRAT.COM')],check=True)
  settings=bytearray(prm(timeout=5));struct.pack_into('<HH',settings,0,2,5)
  struct.pack_into('<H',settings,0x178,0x3e8);struct.pack_into('<H',settings,0x188,5);struct.pack_into('<HH',settings,0x4e4,8,4)
  data=bytearray(directory());data[250+0x56:250+0x68]=bytes(18)
  data[250+0x56:250+0x5c]=b'BOARD\0';data[250+0x5f:250+0x65]=b'BOARD\0'
  xlt_mode=2 if mode in (11,17) else 1 if 9<=mode<=16 else 0
  struct.pack_into('<H',settings,0x1e0,xlt_mode)
  table_bytes=bytes((i*73+19)%256 for i in range(256))
  if mode>=9:
   (case/'ENV').mkdir();(case/'ENV/PCPLUS.XLT').write_bytes(bytes(reversed(table_bytes)))
   (case/'OTHER').mkdir();(case/'PCPLUS.XLT').write_bytes(bytes(range(256)))
   if mode==11:(case/'CLI.XLT').write_bytes(table_bytes)
   if mode not in (10,11,12):
    if mode==16:(case/'OTHER/PCPLUS.XLT').mkdir()
    else:(case/'OTHER/PCPLUS.XLT').write_bytes(table_bytes[:255] if mode in (13,15,17,18) else table_bytes+b'X' if mode==14 else table_bytes)
   (case/'CHDIR.ASX').write_bytes(compile_source('proc main\nchdir "C:\\OTHER"\nmkdir "WITNESS"\nendproc\n'))
   (case/'START.KEY').write_bytes(launch_actions(b'C:\\CHDIR.ASX',0))
   shutil.copyfile(ROOT/'build/aspect-register-parent-custom-irq/ASPECT.EXE',case/'ASPECT.EXE')
  (case/'TEST.PRM').write_bytes(settings);(case/'PCPLUS.DIR').write_bytes(data)
  if mode!=3:
   kbd=bytearray(keyboard('N'))
   if mode==1:kbd[6*948:6*948+12]=b'X'*12
   key=bytearray(actions('N'))
   if mode==2:struct.pack_into('<H',key,0,4)
   (case/'BOARD.KBD').write_bytes(kbd);(case/'BOARD.KEY').write_bytes(key)
  if mode>=9:
   for leaf in ('PCPLUS.DIR','BOARD.KBD','BOARD.KEY'):shutil.copyfile(case/leaf,case/'OTHER'/leaf)
  originals={str(f.relative_to(case)):f.read_bytes() for f in case.rglob('*') if f.is_file() and f.suffix in ('.PRM','.DIR','.KBD','.KEY','.XLT','.ASX','.EXE')}
  child_keys='a-1 p6500 ' if mode>=9 else ''
  entry_keys='a-z p400 a-d' if mode==4 else '` p400 tab p300 l' if mode==5 else 'a-d'
  config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 12000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=dummy irq:5
serial4=disabled
[autoexec]
@echo off
mount c "{case}"
mount d "{case}"
c:
set PCPLUS={r'C:\ENV' if mode in (10,15,16) else ''}
STRAT B
SNAP B
WATCH T
ADDKEY p900 enter p1100 {child_keys}{entry_keys} p500 enter p3000 enter p1200 r p1800 space p900 a-x
TERMINAL @TEST.PRM {'/T:START.KEY' if mode>=9 else ''} {'/X:CLI.XLT' if mode==11 else ''}
if errorlevel 1 goto failed
cd \\
WATCH
STRAT A
SNAP A
SNAP S
echo PASS>PASS.TXT
exit
:failed
cd \\
WATCH
SNAP A
SNAP S
echo FAIL>FAIL.TXT
exit
'''
  (case/'dosbox.conf').write_text(config)
  with (case/'dosbox.log').open('w') as log:run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(case/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=45)
  assert run.returncode==0 and (case/'PASS.TXT').exists() and not (case/'FAIL.TXT').exists(),name
  assert (case/'BEFORE.BIN').read_bytes()==(case/'AFTER.BIN').read_bytes() and len((case/'BEFORE.BIN').read_bytes())==42,name
  assert len((case/'STRATB.BIN').read_bytes())==2 and (case/'STRATB.BIN').read_bytes()==(case/'STRATA.BIN').read_bytes(),name
  observed=(case/'OWNER.BIN').read_bytes();assert len(observed)==14+2*field_bytes+1190+2*bundle_bytes+14+resource_bytes+4000+14
  magic,flags,ticks,io_calls,opens,violations,app_ds=struct.unpack_from('<7H',observed)
  assert magic==0x524f and flags==(15 if 6<=mode<=8 else 7) and ticks>20 and not violations and app_ds,(name,magic,flags,ticks,io_calls,opens,violations)
  expected_fields=bytearray(observed[14:14+field_bytes])
  if mode==7:
   transfer_at=sum(size for field,size in fields[:next(i for i,(field,size) in enumerate(fields) if field=='_terminal_transfer_preferences')])
   expected_fields[transfer_at]^=1
  if mode==8:
   baud_at=sum(size for field,size in fields[:next(i for i,(field,size) in enumerate(fields) if field=='terminal_baud_low')]);expected_fields[baud_at:baud_at+2]=struct.pack('<H',38400)
  assert expected_fields==observed[14+field_bytes:14+2*field_bytes],name
  pos=14+2*field_bytes;proposed=observed[pos:pos+1190];pos+=1190
  before=observed[pos:pos+bundle_bytes];pos+=bundle_bytes;bundle=observed[pos:pos+bundle_bytes];pos+=bundle_bytes
  owner=struct.unpack_from('<7H',observed,pos);pos+=14;resource=observed[pos:pos+resource_bytes];pos+=resource_bytes
  prompt=observed[pos:pos+4000];success=mode in (0,3,4,5,9,10,11,17,18)
  released=struct.unpack_from('<7H',observed,pos+4000)
  assert released[0]==0 and released[1:]==owner[1:],(name,released,owner)
  assert owner[0]==(3 if success else 4) and owner[1]==(0 if success else 4 if 6<=mode<=8 else 7) and owner[6]==1,(name,owner)
  assert opens==(3 if mode in (9,10,11,13,14,15) else 2 if mode in (0,2,4,5,17,18) else 1 if mode==1 else 0),(name,opens)
  assert (io_calls==0 if 6<=mode<=8 else io_calls>0),name
  if success:
   loaded=mode in (0,4,5,9,10,11,17,18)
   expected=struct.pack('<4H',6,(4608 if loaded else 0)|(16384 if mode in (9,10,11) else 0),2 if loaded else 0,1 if mode>=9 else 2 if loaded else 0)
   expected+=(b'C:\\OTHER\\BOARD.KBD' if mode>=9 else b'C:\\BOARD.KBD' if loaded else b'').ljust(64,b'\0')+(b'C:\\START.KEY' if mode>=9 else b'C:\\BOARD.KEY' if loaded else b'').ljust(64,b'\0')
   expected+=keyboard('N')[6*948:7*948]+(launch_actions(b'C:\\CHDIR.ASX',0) if mode>=9 else actions('N')) if loaded else bytes(default)+DISABLED
   if translation:
    enabled=mode in (9,10,11)
    path=(b'C:\\CLI.XLT' if mode==11 else b'C:\\ENV\\PCPLUS.XLT' if mode==10 else b'C:\\OTHER\\PCPLUS.XLT') if enabled else b''
    expected+=struct.pack('<2H',1 if enabled else xlt_mode,1 if mode==11 else 0)+path.ljust(64,b'\0')
    expected+=(bytes(reversed(table_bytes)) if mode==10 else table_bytes) if enabled else bytes(256)
    assert struct.unpack_from('<H',proposed,496+40)[0]==(1 if mode==11 else xlt_mode),name
   assert bundle==expected,name
   assert (b'KEY/KBD/XLT resources checked.' if translation else b'KEY/KBD resources checked.') in prompt[::2],name
  else:
   assert bundle==before and (b'Could not prepare KEY/KBD/XLT resources.' if translation else b'Could not prepare KEY/KBD resources.') in prompt[::2],name
  if mode>=9:assert (case/'OTHER/WITNESS').is_dir(),name
  for leaf,original in originals.items():assert (case/leaf).read_bytes()==original,(name,leaf)
  reports.append(dict(case=name,passed=True,observer_ticks=ticks,DOS_operations_under_quiescence=io_calls,content_opens=opens,ownership_violations=violations,owner_state=owner,resource_state=struct.unpack_from('<7H',resource),active_state_unchanged=mode not in (7,8),declared_session_fault_only=mode in (7,8),hardware_restored=True))
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 result=dict(passed=True,binary_sha256=sha(binary),cases=reports,case_count=len(reports),translation=translation,source_resources_unchanged=True,
  sources={n:sha(ROOT/n) for n in ['standalone/test_directory_resource_owner_dos.py','standalone/directory_resource_owner_watch.asm','standalone/dos_strategy_sample.asm','standalone/test_terminal.py','standalone/modem_fixtures.py','standalone/directory_view_fixture.py','standalone/test_directory_resources_dos.py','standalone/test_directory_key_bindings_dos.py','src/aspect/compiler.py']},
  artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
  scope='Actual DOS8086 COM3/IRQ5 dummy UART, real popup/PROGRAM/kernel reads and passive DOS/INT1C observer. No selected settings/target applied; no live modem/SIP/analog claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(reports),'actual DOS resource owner workflows')
if __name__=='__main__':main()
