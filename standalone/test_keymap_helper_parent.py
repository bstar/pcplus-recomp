#!/usr/bin/env python3
"""Capacity/resume check via existing PROGRAM path; not Alt-F8 integration."""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
import test_connection_dos as lab
from modem_fixtures import fixture
from test_keymap_helper import image,changed
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',required=True,type=Path);p.add_argument('--build',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--open',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 parent=a.parent.resolve();helper=a.build.resolve()/'PCKEYMAP.EXE';m=json.loads((a.build/'result.json').read_text());assert sha(helper)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h
 runtime=out/'runtime';runtime.mkdir()
 for name in ('TERMINAL.EXE','PCPLUS.MET','PCLINE.OVL','PCMETA.OVL','PCPLUS.ASP','PCPLUS.CMP'):
  path=parent.with_name(name)
  if path.is_file():shutil.copyfile(path,runtime/name)
 lab.BINARY=runtime/'TERMINAL.EXE';assert sha(lab.BINARY)==sha(parent)
 keys=bytearray(540)
 for i in range(10):struct.pack_into('<H',keys,i*54,3)
 cmd=b'D:\\PCKEYMAP.EXE 6 D:\\SYN.KBD';struct.pack_into('<H',keys,0,1);keys[2:2+len(cmd)]=cmd
 settings=bytearray(fixture())
 for at,v in ((0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113)):struct.pack_into('<H',settings,at,v)
 files={'TEST.KEY':bytes(keys),'PCKEYMAP.EXE':helper.read_bytes(),'SYN.KBD':image()}
 if a.open:files['NEXT.KBD']=image()
 opening='a-o p150 n e x t enter p700 ' if a.open else ''
 r=lab.run(out.name,'success','p900 enter p3000 a-1 p1800 '+opening+'f1 p100 tab n e w enter p200 a-s p700 escape p1000 space p1000 r e a d y p600 a-x',prm=bytes(settings),arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\TEST.KEY COM1 19200 HARD',files=files,cpu='8086',timeout=30,working_drive='d' if a.open else 'c')
 drive=ROOT/'build/connection-dos'/out.name;checks=dict(r['checks']);edited='NEXT.KBD' if a.open else 'SYN.KBD';checks.pop('fixture_unchanged_'+edited)
 checks['helper_saved_exact_selected_slot']=(drive/edited).read_bytes()==changed(image())
 checks['parent_keyboard_resumed']=b'ready' in (drive/'serial.bin').read_bytes();checks['source_helper_unchanged']=sha(drive/'PCKEYMAP.EXE')==sha(helper)
 result=dict(passed=all(checks.values()),opens_second_file=a.open,checks=checks,parent_sha256=sha(parent),helper_sha256=sha(helper),parent_result=str((drive/'result.json').relative_to(ROOT)),sources={n:sha(ROOT/n) for n in ('standalone/test_keymap_helper_parent.py','standalone/test_keymap_helper.py','standalone/test_connection_dos.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py')},scope=__doc__+' Owned copied runtime, synthetic modem and files; no physical or Enigma/SynthModem acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],[n for n,v in checks.items() if not v];print('PASS existing PROGRAM/helper/serial resume')
if __name__=='__main__':main()
