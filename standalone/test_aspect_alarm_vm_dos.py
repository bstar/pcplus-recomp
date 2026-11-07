#!/usr/bin/env python3
"""Opt-in actual parent/VM ALARM through live native receive and WHEN service."""
import inspect,json,sys,struct,argparse
from pathlib import Path
import test_aspect_pause_when_dos as pause
import test_aspect_keys_dos as keys
from alarm_speaker_observer import instrument
ROOT=keys.ROOT
PARENT=ROOT/'build/terminal-alarm-policy-admission-20261106'
CHILD=ROOT/'build/aspect-alarm-vm-numeric-final-20261106'

def main():
 global PARENT,CHILD
 parser=argparse.ArgumentParser(add_help=False)
 parser.add_argument('--parent-dir',type=Path,default=PARENT)
 parser.add_argument('--child-dir',type=Path,default=CHILD)
 parser.add_argument('--variant',choices=('when','policy','keys'),default='when')
 parser.add_argument('--speaker',action='store_true',help='Enable the parent sound policy and sample actual speaker gate/exit state')
 parser.add_argument('--observe-alarm',action='store_true',help='Sample speaker/exit state without enabling sound')
 selected,remaining=parser.parse_known_args();sys.argv=[sys.argv[0],*remaining]
 PARENT=selected.parent_dir.resolve();CHILD=selected.child_dir.resolve()
 assert PARENT.is_relative_to(ROOT/'build') and CHILD.is_relative_to(ROOT/'build')
 original=pause.definitions
 original_prm=keys.renderer.prm
 def configured_prm():
  settings=bytearray(original_prm())
  for off,value in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,4),(0x1e6,0),(0x1e4,0)]:struct.pack_into('<H',settings,off,value)
  if selected.speaker:struct.pack_into('<H',settings,0x1bc,1)
  return bytes(settings)
 keys.renderer.prm=configured_prm
 observer_text=inspect.getsource(keys.renderer.observer)
 old=" cmp word [PROGRAM_KIND],4\n jne .chain\n"
 assert observer_text.count(old)==1
 observer_text=observer_text.replace(old,"")
 old=" call far [cs:old21]\n save\n push cs"
 new=" call far [cs:old21]\n save\n mov bp,sp\n test word [ss:bp+18],1\n jz .exec_return_recorded\n mov ax,[ss:bp+16]\n mov [cs:exit_code],ax\n.exec_return_recorded:\n push cs"
 assert observer_text.count(old)==1
 observer_text=observer_text.replace(old,new)
 if selected.speaker or selected.observe_alarm:
  observer_text=instrument(observer_text,pause.window.symbols(CHILD/'ASPECT.map'))
 exec(compile(observer_text,str(Path(__file__)),'exec'),keys.renderer.__dict__)
 # The shared peer gained a software-flow block before line.append. Retain
 # that block and insert the existing READY/END hooks at the exact append.
 adapter_text=inspect.getsource(keys.adapter)
 adapter_text=adapter_text.replace("old='if online:\\n       line.append(byte)'", "old='       line.append(byte)'")
 adapter_text=adapter_text.replace("if b'done' in line", "if b'PAUSEDONE' in line")
 exec(compile(adapter_text,str(Path(__file__)),'exec'),keys.__dict__)
 def definitions():
  rows=original()
  if selected.variant!='when':
   template=next(r for r in rows if r['name']=='pause-when-plain-terminal')
   rows=[]
   variants=(('default','alarm',3,5),
             ('zero-default','alarm 0\ntransmit "FIRSTDONE"\nalarm',3,5),
             ('override-default','alarm 2\ntransmit "FIRSTDONE"\nalarm',4,7)) if selected.variant=='policy' else tuple(
             (name,'alarm 32767',1,7) for name in ('escape','printable','extended'))
   for name,command,low,high in variants:
    row=dict(template,name='pause-when-'+selected.variant+'-'+name,
             source=template['source'].replace('pause 4',command),expected_min=low,expected_max=high)
    if 'FIRSTDONE' in command:row['key_wire']=row['key_wire'].replace(b'keys',b'keysFIRSTDONE',1)
    rows.append(row)
  rows=[r for r in rows if r['name']!='pause-when-future-wait']
  for row in rows:
   row['name']=row['name'].replace('pause-when','alarm-vm')
   row['source']=row['source'].replace('pause 4','alarm 4')
   row['keys']='p900 enter p14000 space p700 r e a d y p700 a-x'
   if selected.variant=='keys':
    key={'escape':'escape','printable':'x','extended':'f1'}[row['name'].rsplit('-',1)[1]]
    row['keys']='p900 enter p5000 '+key+' p3000 space p700 r e a d y p700 a-x'
   assert row['key_wire'].startswith(b'keys') and row['key_wire'].endswith(b'done')
   row['key_wire']=row['key_wire'][4:-4]
   row['no_window']=True
  return rows
 # Reuse the frozen peer, real native renderer and passive observer. Only
 # declared binary/map paths and authored source definitions differ.
 text=inspect.getsource(keys.main)
 old="source=inspect.getsource(renderer.main)"
 replacement="source=inspect.getsource(renderer.main).replace(\"ROOT/'build/terminal/TERMINAL.EXE'\", "+repr("Path("+repr(str(PARENT/'TERMINAL.EXE'))+")")+").replace(\"ROOT/'build/aspect-runner/ASPECT.EXE'\", "+repr("Path("+repr(str(CHILD/'ASPECT.EXE'))+")")+")"
 text=text.replace("exec(compile(source,__file__,'exec'),scope)","source=source.replace(\"observer='RENDER'\",\"observer='RENDER',observer_high=True\");exec(compile(source,__file__,'exec'),scope)")
 assert text.count(old)==1;text=text.replace(old,replacement)
 exec(compile(text,str(Path(__file__)), 'exec'),keys.__dict__)
 scope=dict(pause.__dict__);scope['definitions']=definitions;scope['BASE']=ROOT/'build/aspect-alarm-vm-dos'
 text=inspect.getsource(pause.main).replace("4 <= elapsed <= 5", "3 <= elapsed <= 5").replace("ROOT / 'build/terminal/terminal.map'", "Path("+repr(str(PARENT/'terminal.map'))+")").replace("ROOT / 'build/aspect-runner/ASPECT.map'", "Path("+repr(str(CHILD/'ASPECT.map'))+")")
 if selected.variant!='when':
  text=text.replace('3 <= elapsed <= 5',"spec['expected_min'] <= elapsed <= spec['expected_max']")
 if selected.variant=='policy':
  # Place the receive query inside the configured default, after both the
  # zero and two-count first alerts. Freeze wire ordering before execution.
  old="(3.0, specs[args[0]]['marker'] + QUERY)"
  assert text.count(old)==1
  text=text.replace(old,"(4.5, specs[args[0]]['marker'] + QUERY)")
 exec(compile(text,str(Path(__file__)),'exec'),scope);scope['main']()
 report=ROOT/'build/aspect-alarm-vm-dos'/sys.argv[sys.argv.index('--label')+1]/'pause-checks.json'
 assert json.loads(report.read_text())['passed'], 'ALARM VM acceptance remains unproven; inspect preserved captures'
 if selected.speaker or selected.observe_alarm:
  result=json.loads(report.read_text());cases=[]
  for case in result['cases']:
   raw=(report.parent/case['case']/'RENDER.BIN').read_bytes()
   on,edges,last,port,owned,duration,abi=struct.unpack('<7H',raw[-28:-14])
   checks=dict(speaker_activity_matches_policy=(on>0 and edges>=2) if selected.speaker else on==edges==0,
               speaker_gate_off_at_exit=port==0,speaker_owner_released=owned==0,
               configured_duration_restored_at_exit=duration==4,child_DS_equals_SS=abi==1)
   cases.append(dict(case=case['case'],passed=all(checks.values()),checks=checks,
                     speaker_on_ticks=on,speaker_gate_edges=edges,last_sample=last,
                     exit_port=port,exit_owned=owned,exit_duration=duration))
  speaker=dict(passed=all(c['passed'] for c in cases),enabled=selected.speaker,cases=cases,
               scope='Passive INT1C samples actual emulated port61 gate bits during child EXEC; reads child owner/duration at DOS exit under verified DS=SS. No PIT writes, key or reply substitution. Detects enabled output and cleanup, not exact frequency, tone cadence or physical audibility.')
  (report.parent/'speaker-checks.json').write_text(json.dumps(speaker,indent=2)+'\n')
  assert speaker['passed'],speaker
 if selected.variant=='policy':
  result=json.loads(report.read_text());checks=[]
  for case in result['cases']:
   if 'default' not in case['case'] or case['case'].endswith('policy-default'):continue
   target=report.parent/case['case'];events=json.loads((target/'peer-events.json').read_text())
   received=b'';first=done=None
   for event in events:
    if event['kind']!='receive':continue
    received+=bytes.fromhex(event['hex'])
    if first is None and b'FIRSTDONE' in received:first=event['time']
    if done is None and b'PAUSEDONE' in received:done=event['time']
   delay=None if first is None or done is None else done-first
   hold=next(e['time'] for e in events if e['kind']=='send' and e['hex']==b'HOLD'.hex())
   check=dict(case=case['case'],configured_default_after_override_seconds=delay,
              configured_default_observed=delay is not None and 3<=delay<=5,
              first_alert_seconds=None if first is None else first-hold)
   if 'zero-default' in case['case']:check['zero_returns_without_second_wait']=first is not None and 0<=first-hold<=1
   check['passed']=check['configured_default_observed'] and check.get('zero_returns_without_second_wait',True)
   checks.append(check)
  assert len(checks)==2
  policy=dict(passed=all(c['passed'] for c in checks),cases=checks,
              scope='Actual parent policy reread after explicit overrides. Native wrapper restoration itself remains separately established by the exact-byte controller tests; this timing check does not sample the child duration word between commands.')
  (report.parent/'policy-checks.json').write_text(json.dumps(policy,indent=2)+'\n')
  assert policy['passed'],policy
if __name__=='__main__':main()
