#!/usr/bin/env python3
"""Actual Alt-F8 and checked live key publication on synthetic DOS media."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as lab
from modem_fixtures import fixture
from test_keymap_helper import image,changed
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','helper','output'):p.add_argument('--'+n,required=True,type=Path)
 p.add_argument('--profiles',type=int,choices=[5,7,33],default=33);p.add_argument('--profile',type=int,choices=[4,6],default=6);p.add_argument('--case',action='append');a=p.parse_args();assert a.profile<a.profiles;out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 parent=a.terminal.resolve();helper=a.helper.resolve();m=json.loads(parent.with_name('manifest.json').read_text());assert m['experimental_keymap_editor'] and sha(parent)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 settings=bytearray(fixture());struct.pack_into('<H',settings,0x194,a.profile);slot=a.profile*948+16*12
 for at,v in ((0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113)):struct.pack_into('<H',settings,at,v)
 base=image()[:a.profiles*948];results=[]
 cases=['save','cancel','discard','other-file','other-profile','missing-helper','invalid-return','recovery-exit','error-valid-return','reference','browser']
 if a.case:assert set(a.case).issubset(cases);cases=[n for n in cases if n in a.case]
 for name in cases:
  run=out/(out.name+'-'+name);run.mkdir();runtime=run/'runtime';runtime.mkdir()
  for leaf in ('TERMINAL.EXE','PCCHAT.OVL','PCHELP.RTE','PCPLUS.HLP','PCLINE.OVL','PCMETA.OVL'):
   source=parent.with_name(leaf)
   if source.is_file():shutil.copyfile(source,runtime/leaf)
  if name!='missing-helper':shutil.copyfile(helper,runtime/'PCKEYMAP.EXE')
  if name in ('invalid-return','recovery-exit','error-valid-return'):
   code='BITS 16\nCPU 8086\nSEGMENT _TEXT public class=CODE use16\nglobal start\nstart:\n push cs\n pop ds\n'
   if name!='recovery-exit':
    value=b'BADBADBADBAD' if name=='invalid-return' else b'fake\0'
    code+=' mov dx,filename\n mov ax,0x3d01\n int 21h\n jc failed\n mov bx,ax\n mov ax,0x4200\n xor cx,cx\n mov dx,'+str(slot)+'\n int 21h\n jc failed\n mov dx,value\n mov cx,'+str(len(value))+'\n mov ah,0x40\n int 21h\n jc failed\n mov ah,0x3e\n int 21h\n jc failed\n'
    code+=' mov ax,'+('0x4c01' if name=='error-valid-return' else '0x4c00')+'\n int 21h\n'
    code+="filename: db 'D:\\SYN.KBD',0\nvalue: db "+','.join(str(c) for c in value)+'\n'
   else:code+=' mov ax,0x4c0e\n int 21h\n'
   code+='failed: mov ax,0x4c07\n int 21h\nSEGMENT STACK stack class=STACK use16\nresb 256\n'
   (run/'fake.asm').write_text(code);subprocess.run(['nasm','-fobj',str(run/'fake.asm'),'-o',str(run/'fake.obj')],check=True)
   subprocess.run(['wlink','system','dos','option','quiet','option','start=start','name',str(runtime/'PCKEYMAP.EXE'),'file',str(run/'fake.obj')],check=True)
  opening='a-z p3500 a-f8' if name=='reference' else '` p700 right right right p300 k' if name=='browser' else 'a-f8'
  edit='p1600 f1 p100 tab n e w enter p150 '
  expected=base;other=base;wire_binding=('P%02d16'%a.profile).encode();end='p1000 f1 p250 r e a d y p300 a-x';triggers=()
  if name in ('save','reference','browser'):
   keys=edit+'a-s p500 escape';expected=changed(base,a.profile);wire_binding=b'new'
   if name=='save':end='p1000 f1 p250 r i s p500 f1 p250 r e a d y p300 a-x';triggers=((b'ris',b'\x1bcFIRST BYTE SAFE\x1b[6n'),)
  elif name=='cancel':keys='p1600 f1 p100 tab n e w escape p250 escape'
  elif name=='discard':keys=edit+'escape p150 n'
  elif name=='other-file':keys='p1600 a-o p150 n e x t enter p350 f1 p100 tab n e w enter p150 a-s p500 escape';other=changed(base,a.profile)
  elif name=='other-profile':keys='p1600 space p150 f1 p100 tab n e w enter p150 a-s p500 escape';expected=changed(base,(a.profile+1)%a.profiles)
  elif name=='recovery-exit':keys='';end=''
  else:
   keys='p1500 space'
   if name=='invalid-return':buf=bytearray(base);buf[slot:slot+12]=b'BADBADBADBAD';expected=bytes(buf)
   if name=='error-valid-return':buf=bytearray(base);buf[slot:slot+5]=b'fake\0';expected=bytes(buf);wire_binding=b'fake'
  lab.BINARY=runtime/'TERMINAL.EXE';label=run.name
  r=lab.run(label,'success','p900 enter p3000 '+opening+' '+keys+' '+end,prm=bytes(settings),arguments='@D:\\TEST.PRM /D:CaseTest:23 /K:D:\\SYN.KBD COM1 19200 HARD',files={'SYN.KBD':base,'NEXT.KBD':base},cpu='8086',profile=a.profile,working_drive='d',expected=14 if name=='recovery-exit' else 0,online_triggers=triggers,timeout=30)
  drive=ROOT/'build/connection-dos'/label;checks=dict(r['checks']);checks.pop('fixture_unchanged_SYN.KBD');checks.pop('fixture_unchanged_NEXT.KBD')
  checks['SYN_exact']=(drive/'SYN.KBD').read_bytes()==expected;checks['NEXT_exact']=(drive/'NEXT.KBD').read_bytes()==other
  wire=(drive/'serial.bin').read_bytes()
  if name!='recovery-exit':checks['live_binding']=wire_binding in wire;checks['ordinary_keys_resume']=b'ready' in wire
  if name=='save':checks['RIS_retains_binding']=wire.count(b'new')==2
  row=dict(case=name,passed=all(checks.values()),checks=checks,parent_sha256=sha(parent),helper_sha256=sha(runtime/'PCKEYMAP.EXE') if name!='missing-helper' else None,raw_result=str((drive/'result.json').relative_to(ROOT)))
  (run/'result.json').write_text(json.dumps(row,indent=2)+'\n');assert row['passed'],(name,[n for n,v in checks.items() if not v]);results.append(row);print('PASS Alt-F8',name,flush=True)
 result=dict(passed=True,cases=results,parent_sha256=sha(parent),matched_helper_sha256=sha(helper),original_inputs=[],cpu='8086',profiles=a.profiles,selected_profile=a.profile,file_bytes=len(base),sources={n:sha(ROOT/n) for n in ('standalone/test_keymap_editor_dos.py','standalone/test_keymap_helper.py','standalone/test_connection_dos.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py')},scope='Actual new Alt-F8/foreground child/strict reload/live key output/RIS and hardware restore on owned synthetic media. No physical, source-package or live BBS acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
