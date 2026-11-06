#!/usr/bin/env python3
"""Actual serviced external parameter dialog, owned COM child, and UART/display return."""
import argparse,json,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import ROOT,sha

def recipes():
 return [dict(name='relative',parameters='PAGE.DAT'),dict(name='absolute',parameters='D:\\PAGE.DAT'),dict(name='options',parameters='PAGE.DAT',options=' /Q /X'),dict(name='spaces',parameters='D:\\A B.DAT'),dict(name='empty',parameters=''),dict(name='cancel',parameters=None),dict(name='long',parameters='A'*48),dict(name='maximum',parameters='A'*48,maximum=True),dict(name='reference',parameters='PAGE.DAT',prefix='a-z p500 a-v'),dict(name='browser',parameters='PAGE.DAT',prefix='` p500 v'),dict(name='malformed',parameters=None,malformed=True)]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--case');a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_external_viewer'] and sha(binary)==manifest['binary_sha256']
 names=['standalone/test_viewer_external_parent.py','standalone/viewer_external_child.asm','standalone/viewer_dialog_watch.asm','standalone/test_connection_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py'];frozen=dict(manifest['sources']);frozen.update({n:sha(ROOT/n) for n in names})
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);child=out/'VTEST.COM';subprocess.run(['nasm','-fbin',str(ROOT/'standalone/viewer_external_child.asm'),'-o',str(child)],check=True)
 harness.BINARY=binary;cases=[]
 selected=[r for r in recipes() if not a.case or r['name']==a.case];assert selected
 for r in selected:
  name=r['name'];settings=bytearray(prm(port=3,baud=5))
  for at,v in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:struct.pack_into('<H',settings,at,v)
  command='D:\\VTEST.COM'+r.get('options','')
  if r.get('maximum'):command='D:\\VTEST.COM '+'Q'*51
  assert len(command)<=64
  settings[0x35d:0x39e]=command.encode().ljust(65,b'\0') if not r.get('malformed') else b'X'*65
  observer=out/(name+'.COM');kind=10 if r.get('malformed') else 9
  subprocess.run(['nasm','-fbin','-DWATCH_KIND='+str(kind),str(ROOT/'standalone/viewer_dialog_watch.asm'),'-o',str(observer)],check=True)
  parameters=r['parameters'];body=r.get('prefix','a-v')+' p1000 '
  body+='escape' if parameters is None else ' '.join('space' if c==' ' else c for c in parameters)+' enter p1600'
  label=out.name+'-'+name;drive=ROOT/'build/connection-dos'/label;assert not drive.exists()
  base=harness.run(label,'success','p900 enter p3500 '+body+' p700 r e a d y enter p1000 a-x',prm=bytes(settings),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',observer='VIEWOBS',timeout=35,files={'VIEWOBS.COM':observer.read_bytes(),'VTEST.COM':child.read_bytes()},online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-VIEWER\x1b[6n'),))
  raw=(drive/'VIEWUI.BIN').read_bytes();words=struct.unpack_from('<9H',raw);before=raw[18:4018];prompt=raw[4018:8018];after=raw[8018:12018];wire=(drive/'serial.bin').read_bytes();child_report=drive/'VCHILD.BIN';data=child_report.read_bytes() if child_report.exists() else b''
  expected=(r.get('options','')+' '+parameters) if parameters is not None else None
  if r.get('maximum'):expected=' '+'Q'*51+' '+'A'*48
  if parameters=='':expected=''
  checks=dict(base['checks'],complete_observer=len(raw)==12083 and words[:2]==(0x5656,15),exact_frame_return=before==after,exact_cursor_shape_return=words[3:5]==words[7:9],parameter_field_native_cursor=words[5]==0x0c19,ordinary_keyboard_after_return=wire.count(b'ready\r')==1,fresh_CPR_after_return=b'\x1b[3;13R' in wire,owned_PRM_unchanged=(drive/'TEST.PRM').read_bytes()==settings,startup_path=raw[12018]==3 and raw[12019:].split(b'\0',1)[0]==b'',parameter_text_local=b'PAGE.DAT' not in wire)
  if parameters is None:checks['cancel_never_EXECutes']=not data
  else:checks.update(actual_child=len(data)==202 and struct.unpack_from('<2H',data)==(0x5645,1),exact_child_tail=len(data)==202 and data[8]==len(expected) and data[9:9+data[8]]==expected.encode(),child_CWD_unchanged=len(data)==202 and struct.unpack_from('<H',data,136)[0]==3 and not data[138])
  result=dict(case=name,passed=all(checks.values()),checks=checks,observer_words=words,child_tail_hex=data[8:136].hex() if data else None,frame_sha256=sha(drive/'VIEWUI.BIN'),drive=str(drive.relative_to(ROOT)));(out/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(name,{n:v for n,v in checks.items() if not v},flush=True);assert result['passed'],result;cases.append(result)
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 (out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),cases=cases,sources=frozen,original_inputs=[],scope=__doc__+' DOS8086 COM3/IRQ5 synthetic serial modem; owned PRM/COM; passive full2000-cell frames/cursor and actual PSP tail/CWD, then fresh parser/keyboard and hardware restoration. No physical/SIP/DSP or whole-parity claim.'),indent=2)+'\n')
if __name__=='__main__':main()
