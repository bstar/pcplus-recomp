#!/usr/bin/env python3
"""Independently bind stock BBS window/continuation captures and prior failures."""
import argparse,hashlib,json,re,shutil,struct,subprocess,tempfile
from pathlib import Path
from modem import Telnet
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--baseline-label',default='script-window-compat-02')
 p.add_argument('--cohort',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label) and re.fullmatch(r'[A-Za-z0-9_-]+',a.baseline_label)
 cohort=a.cohort.resolve();target=a.output.resolve()
 assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
 assert target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 selected={Path(__file__).resolve()};servers={};prior={}
 for name,payload in [('synchronet',b'TQ'),('enigma',b'M\rQ\r')]:
  stage=ROOT/'build/bbs-lab/script-window'/name/a.label;out=ROOT/'build/bbs-lab/results'/name/a.label
  r=read(stage/'result.json');start=read(stage/'start.json');run=read(out/'result.json')
  assert r['passed'] and all(r['checks'].values()) and run['passed'] and all(run['checks'].values())
  assert r['inputs']==start['inputs']
  for path,digest in r['inputs'].items():assert sha(ROOT/path)==sha(stage/'frozen-source'/path)==digest,path
  for path,digest in r['captures_sha256'].items():assert sha(ROOT/path)==digest,path
  for path,digest in start['generated'].items():assert sha(stage/path)==digest,path
  assert 'WIN.OK' not in start['generated'] and (stage/'WIN.OK').read_bytes()==b'OK'
  assert sha(stage/'TERMINAL.EXE')==r['binary_sha256']==sha(ROOT/'build/terminal/TERMINAL.EXE')
  assert sha(stage/'ASPECT.EXE')==r['runner_sha256']==sha(ROOT/'build/aspect-runner/ASPECT.EXE')
  assert (out/'TEST.PRM').read_bytes()[0x79:0x79+25]==bytes(25)
  assert not [e for e in read(out/'modem.json')['events'] if e['kind']=='error']
  frame=(out/'RENDER.BIN').read_bytes();header=struct.unpack_from('<7H',frame)
  observation=struct.unpack('<5H',frame[-10:]);assert header[:4]==(0x524e,1,1,1) and header[6]==0
  assert observation[:2]==(1,1) and observation[2]>72 and observation[4]==1
  observer=(stage/'observer.asm').read_text()
  assert 'cmp word [cs:exec_done],1\n jne .try_reference\n mov word [cs:parent_menu_seen],1' in observer
  actor=struct.unpack('<8H',(out/'RECKEY.BIN').read_bytes());assert actor[:4]==(0x524b,3,3,1)
  assert len((out/'KEYOLD.BIN').read_bytes())==4 and (out/'KEYOLD.BIN').read_bytes()==(out/'KEYNEW.BIN').read_bytes()
  driver=(stage/'POSTKEY.ASM').read_text();begin=driver.index('stages:\n');end=driver.index('STAGE_COUNT equ',begin)
  assert driver[begin:end]=='stages:\n dw ready_marker,open_menu,90\n dw menu_marker,escape_key,18\n dw ready_marker,exit_keys,180\n'
  assert "ready_marker: db 'WINDOW DONE',0" in driver
  probe=(stage/'COMPOFF.ASM').read_text()
  assert probe==observer+'\ncompletion_offset: dw magic\n'
  sample=struct.unpack('<H',(stage/'COMPOFF.COM').read_bytes()[-2:])[0]
  assert 'completion_gate:\n cmp word [phase],1\n je scan\n' in driver
  assert ' mov ax,[es:0x86]\n mov es,ax\n' in driver
  for offset,value in [(0,'0x524e'),(2,'1'),(4,'1'),(6,'1'),(12,'0')]:
   assert f' cmp word [es:{sample+offset}],{value}\n jne .no\n' in driver
  assert driver.count(' call completion_gate\n')==1
  assert ' xor ax,ax\n jmp .out\n.no:\n mov ax,1\n or ax,ax\n.out:\n pop es\n pop ax\n ret\nresident_end:' in driver
  with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='window-audit-') as directory:
   for source,binary,flags in [('observer.asm','RENDER.COM',[]),('COMPOFF.ASM','COMPOFF.COM',[]),('POSTKEY.ASM','POSTKEY.COM',['-DRECORD_WATCHDOG_TICKS=2700'])]:
    product=Path(directory)/binary
    subprocess.run(['nasm','-fbin',*flags,str(stage/source),'-o',str(product)],check=True)
    assert sha(product)==sha(stage/binary)
  baseline=read(ROOT/'build/bbs-lab/recording'/name/a.baseline_label/'result.json')
  previous=bytes.fromhex(baseline['sessions']['record']['user_hex']);suffix=payload+b'+++ATH\r';assert previous.endswith(suffix)
  expected=previous[:-len(suffix)]+payload
  sent,_=Telnet().feed((out/'bbs-sent.bin').read_bytes())
  user=re.sub(rb'\x1b\[(?:\?[0-9;]*c|[0-9]+;[0-9]+R)',b'',sent)
  assert user==expected==bytes.fromhex(r['actual_user_hex'])==bytes.fromhex(start['expected_user_hex'])
  assert (out/'BEFORE.BIN').stat().st_size==42 and (out/'BEFORE.BIN').read_bytes()==(out/'AFTER.BIN').read_bytes()
  if name=='enigma':
   rows=[json.loads(line) for line in (out/'server-session.jsonl').read_text().splitlines()]
   ids={row['sessionId'] for row in rows if row.get('msg')=='User "loclab" successfully logged in'};assert len(ids)==1
   menus=[row['menuName'] for row in rows if row.get('menuName')];assert menus[menus.index('mainMenu'):]==['mainMenu','messageBaseMainMenu','mainMenu']
  else:
   plain=(out/'display-clean.txt').read_text();assert plain.count('■ File ■')==1
   assert '■ Main ■' in plain[plain.rfind('■ File ■'):] and 'Unrecognized command' not in plain
  servers[name]=dict(checks=r['checks'],terminal_sha256=r['binary_sha256'],runner_sha256=r['runner_sha256'],
   reference_seen=observation[0],help_seen=observation[1],window_ticks=observation[2],post_exit_parent_menu_seen=observation[4],
   actor_report=actor,exact_user_bytes=len(user),exact_user_sha256=hashlib.sha256(user).hexdigest(),
   scope='Owned stock loopback BBS; script pause/reference/help, resumed scripted navigation and post-exit normal menu. No sustained BBS output during the window.')
  # Preserve previous producers and their frozen witnesses. Passing an old
  # producer does not supersede the rejected timing/transport acceptance.
  for label in ['script-window-stock-01','script-window-stock-02']:
   earlier=ROOT/'build/bbs-lab/script-window'/name/label;e=read(earlier/'result.json')
   prior[name+'/'+label]=dict(producer_passed=e['passed'],failed_checks=[k for k,v in e['checks'].items() if not v])
   if label.endswith('01'):assert read(earlier/'acceptance-review.json')['accepted'] is False
   elif name=='enigma':assert not e['passed'] and prior[name+'/'+label]['failed_checks']==['regular_parent_menu_after_child_exit']
   for base in [earlier,ROOT/'build/bbs-lab/results'/name/label]:selected.update(f for f in base.rglob('*') if f.is_file())
  rejected=ROOT/'build/bbs-lab/script-window'/name/'pause-live-stock-01'
  rejected_result=read(rejected/'result.json')
  prior[name+'/pause-live-stock-01']=dict(producer_passed=rejected_result['passed'],
   failed_checks=[k for k,v in rejected_result['checks'].items() if not v],
   reason='The banner-gated driver failed to observe completion on ENiGMA; normal child exit, exact wire and script navigation passed. Actual EXEC-return gating supersedes that driver, without accepting the failed attempt.')
  if name=='enigma':assert not rejected_result['passed'] and rejected_result['actor_report'][:4]==[0x524b,0,0,2]
  for base in [rejected,ROOT/'build/bbs-lab/results'/name/'pause-live-stock-01',stage,out]:selected.update(f for f in base.rglob('*') if f.is_file())
 cohort.mkdir();kept={}
 for path in sorted(selected):
  copy=cohort/'accepted'/path.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,copy)
  assert sha(copy)==sha(path);kept[str(copy.relative_to(ROOT))]=sha(copy)
 result=dict(passed=True,selected_stock_BBS_script_window_accepted=True,current_audio_accepted=False,
  full_local_command_actions_accepted=False,full_F02_accepted=False,full_F13_accepted=False,
  servers=servers,earlier_attempts=prior,custody_sha256=kept,
  scope='Two production DOS sessions on the existing owned stock Synchronet/ENiGMA fixtures. Actual script-time reference/help, script continuation through read-only board navigation and regular menu after actual child exit pass. Entire typed streams, generated completion-gated BIOS keys, no relay errors, restored timer/DOS/UART and frozen source/binary custody checked. Blank hangup fixture matches the non-escape-aware test modem. Sustained/query/flow pressure during windows, broader scripts/actions, SIP/audio, physical Boca/SPA2102 and every full application gate remain open.')
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=True,servers=list(servers),custody_files=len(kept))))

if __name__=='__main__':main()
