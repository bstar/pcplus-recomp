#!/usr/bin/env python3
"""Actual disconnected Alt-D preview -> PROGRAM resource reads -> exact return."""
import argparse,hashlib,json,os,re,shutil,struct,subprocess
from pathlib import Path
from test_terminal import SAMPLER
from modem_fixtures import fixture as prm
from directory_view_fixture import fixture as directory
from test_directory_resources_dos import keyboard,actions,DISABLED
ROOT=Path(__file__).resolve().parents[1]
FIELDS=[('terminal_option_mask',2),('terminal_dial_target',64),('terminal_directory_entry',2),
 ('terminal_directory_path',64),('terminal_configuration_values',44),('terminal_modem_settings',368),
 ('terminal_directory_plan',214),('terminal_directory_context',496),('terminal_directory_context_valid',2),
 ('terminal_keymap',948),('terminal_action_definitions',540),('terminal_keyboard_path',64),
 ('terminal_actions_path',64),('_terminal_transfer_preferences',66),('terminal_translation_table',256)]
NAMES=['valid-directory-pair-profile6','invalid-KBD-no-publication','invalid-KEY-no-publication','missing-bindings-reset-defaults',
 'reference-parent-releases-whole-popup','browser-parent-releases-whole-popup','proposal-corrupted-after-queue-before-UART-stage']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 binary=args.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text())
 assert manifest['experimental_directory_resource_owner'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 syms={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(binary.parent/'terminal.map').read_text(),re.M|re.I)}
 ds=syms['terminal_stack_top'][0];field_bytes=sum(n for _,n in FIELDS)
 assert all(syms[n][0]==ds for n,_ in FIELDS)
 definitions={
 'OWNER':syms['_terminal_directory_resources'][1],'RESOURCE':syms['_directory_resource_result'][1],
 'PROGRAM_PENDING':syms['terminal_program_pending'][1],'PROGRAM_ACTIVE':syms['terminal_program_active'][1],
 'PROGRAM_KIND':syms['terminal_program_kind'][1],'PROGRAM_STATUS':syms['terminal_program_status'][1],
 'REDISPLAY_ACTIVE':syms['_redisplay_active'][1],'COMMAND_ACTIVE':syms['_command_menu_active'][1],
 'CONNECTION':syms['connection_state'][1],'FIELD_BYTES':field_bytes,'FIELD_COUNT':len(FIELDS),
 'FROZEN_RELATIVE':syms['redisplay_snapshot'][0]-ds,'FROZEN_OFFSET':syms['redisplay_snapshot'][1]}
 (out/'owner-watch.inc').write_text(''.join(f'%define {n} {v}\n' for n,v in definitions.items()))
 (out/'owner-fields.inc').write_text(''.join(f'dw {syms[n][1]},{size}\n' for n,size in FIELDS))
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
 for mode,name in enumerate(NAMES):
  case=out/f'T{mode:03}';case.mkdir();shutil.copyfile(binary,case/'TERMINAL.EXE')
  for leaf in ['WATCH.COM','SNAP.COM']:shutil.copyfile(out/leaf,case/leaf)
  if mode==6:subprocess.run(['nasm','-fbin','-DCORRUPT_PROPOSAL','-I'+str(out)+'/',str(ROOT/'standalone/directory_resource_owner_watch.asm'),'-o',str(case/'WATCH.COM')],check=True)
  subprocess.run(['nasm','-fbin',str(ROOT/'standalone/dos_strategy_sample.asm'),'-o',str(case/'STRAT.COM')],check=True)
  settings=bytearray(prm(timeout=5));struct.pack_into('<HH',settings,0,2,5)
  struct.pack_into('<H',settings,0x178,0x3e8);struct.pack_into('<H',settings,0x188,5);struct.pack_into('<HH',settings,0x4e4,8,4)
  data=bytearray(directory());data[250+0x56:250+0x68]=bytes(18)
  data[250+0x56:250+0x5c]=b'BOARD\0';data[250+0x5f:250+0x65]=b'BOARD\0'
  (case/'TEST.PRM').write_bytes(settings);(case/'PCPLUS.DIR').write_bytes(data)
  if mode!=3:
   kbd=bytearray(keyboard('N'))
   if mode==1:kbd[6*948:6*948+12]=b'X'*12
   key=bytearray(actions('N'))
   if mode==2:struct.pack_into('<H',key,0,4)
   (case/'BOARD.KBD').write_bytes(kbd);(case/'BOARD.KEY').write_bytes(key)
  originals={f.name:f.read_bytes() for f in case.iterdir() if f.suffix in ('.PRM','.DIR','.KBD','.KEY')}
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
set PCPLUS=
STRAT B
SNAP B
WATCH T
ADDKEY p900 enter p1100 {entry_keys} p500 enter p3000 enter p1200 r p1800 space p900 a-x
TERMINAL @TEST.PRM
if errorlevel 1 goto failed
WATCH
STRAT A
SNAP A
SNAP S
echo PASS>PASS.TXT
exit
:failed
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
  observed=(case/'OWNER.BIN').read_bytes();assert len(observed)==14+2*field_bytes+1190+2*1624+14+142+4000+14
  magic,flags,ticks,io_calls,opens,violations,app_ds=struct.unpack_from('<7H',observed)
  assert magic==0x524f and flags==(15 if mode==6 else 7) and ticks>20 and not violations and app_ds,(name,magic,flags,ticks,io_calls,opens,violations)
  assert observed[14:14+field_bytes]==observed[14+field_bytes:14+2*field_bytes],name
  pos=14+2*field_bytes;proposed=observed[pos:pos+1190];pos+=1190
  before=observed[pos:pos+1624];pos+=1624;bundle=observed[pos:pos+1624];pos+=1624
  owner=struct.unpack_from('<7H',observed,pos);pos+=14;resource=observed[pos:pos+142];pos+=142
  prompt=observed[pos:pos+4000];success=mode in (0,3,4,5)
  released=struct.unpack_from('<7H',observed,pos+4000)
  assert released[0]==0 and released[1:]==owner[1:],(name,released,owner)
  assert owner[0]==(3 if success else 4) and owner[1]==(0 if success else 4 if mode==6 else 7) and owner[6]==1,(name,owner)
  assert opens==(2 if mode in (0,2,4,5) else 1 if mode==1 else 0),(name,opens)
  assert (io_calls==0 if mode==6 else io_calls>0),name
  if success:
   loaded=mode in (0,4,5)
   expected=struct.pack('<4H',6,4608 if loaded else 0,2 if loaded else 0,2 if loaded else 0)
   expected+=(b'C:\\BOARD.KBD' if loaded else b'').ljust(64,b'\0')+(b'C:\\BOARD.KEY' if loaded else b'').ljust(64,b'\0')
   expected+=keyboard('N')[6*948:7*948]+actions('N') if loaded else bytes(default)+DISABLED
   assert bundle==expected,name
   assert b'KEY/KBD resources checked.' in prompt[::2],name
  else:
   assert bundle==before and b'Could not prepare KEY/KBD resources.' in prompt[::2],name
  for leaf,original in originals.items():assert (case/leaf).read_bytes()==original,(name,leaf)
  reports.append(dict(case=name,passed=True,observer_ticks=ticks,DOS_operations_under_quiescence=io_calls,content_opens=opens,ownership_violations=violations,owner_state=owner,resource_state=struct.unpack_from('<7H',resource),active_state_unchanged=True,hardware_restored=True))
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 result=dict(passed=True,binary_sha256=sha(binary),cases=reports,case_count=len(reports),source_resources_unchanged=True,
  sources={n:sha(ROOT/n) for n in ['standalone/test_directory_resource_owner_dos.py','standalone/directory_resource_owner_watch.asm','standalone/dos_strategy_sample.asm','standalone/test_terminal.py','standalone/modem_fixtures.py','standalone/directory_view_fixture.py','standalone/test_directory_resources_dos.py']},
  artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
  scope='Actual DOS8086 COM3/IRQ5 dummy UART, real popup/PROGRAM/kernel reads and passive DOS/INT1C observer. No selected settings/target applied; no live modem/SIP/analog claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(reports),'actual DOS resource owner workflows')
if __name__=='__main__':main()
