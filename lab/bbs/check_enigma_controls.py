#!/usr/bin/env python3
"""Replay recovered SOH/VT/CAN instructions, with optional actual ENiGMA wire.

Public regressions use synthetic byte fixtures and require no captured session
or original executable. Actual captured BBS data can be supplied explicitly.
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
from check_formfeed import Terminal,MissingService
from unicorn.x86_const import UC_X86_REG_AX
class BbsTerminal(Terminal):
 def interrupt(self,uc,number,data):
  if number==0x10 and uc.reg_read(UC_X86_REG_AX)>>8==1:return # BIOS cursor shape accepted by the declared model.
  super().interrupt(uc,number,data)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',type=Path,default=ROOT/'build/terminal/TERMINAL.EXE');p.add_argument('--map',type=Path,default=ROOT/'build/terminal/terminal.map');p.add_argument('--wire',type=Path);args=p.parse_args()
 output=ROOT/'build/bbs-lab/enigma/controls-checks';output.mkdir(parents=True,exist_ok=True)
 proof=json.loads((ROOT/'reconstruction/input_controls/provenance.json').read_text())
 for unit in proof['units']:
  target=output/(Path(unit['file']).stem+'.bin')
  subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/unit['file']),'-o',str(target)],check=True)
  assert len(target.read_bytes())==unit['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest()==unit['sha256']
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def terminal():return BbsTerminal(args.binary,args.map)
 def heading():
  for gate,want in [(0,(5,7)),(1,(0,0))]:
   t=terminal();t.position(5,7);t.put('terminal_control_mode_9026',gate);t.call('terminal_control_0e62')
   assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==want
 check('soh-original-mode-gated-home',heading)
 def vertical():
  for profile,dec,newline,want in [(4,0,0,(5,7)),(4,1,0,(6,7)),(20,0,0,(4,7))]:
   t=terminal();t.position(5,7);t.put('csi_terminal_id',profile);t.put('terminal_dec_keys',dec);t.put('terminal_newline_mode_9020',newline);t.call('terminal_control_0f62')
   assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==want
  t=terminal();t.position(3,7);t.put('terminal_control_mode_9026',1);t.data=b'\x05';t.call('terminal_control_0f62')
  assert t.index==1 and (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(5,7)
 check('vt-original-linefeed-high-profile-up-encoded-row-and-ignore',vertical)
 def cancel():
  for newline,want in [(0,(5,7)),(1,(5,8))]:
   t=terminal();t.position(5,7);t.put('terminal_tab_wrap',0);t.put('terminal_control_mode_9026',0);t.put('terminal_newline_mode_9020',newline);t.put('terminal_control_mode_1fb0',0);t.call('terminal_control_11a8')
   assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==want
 check('can-original-default-and-mode-gated-cursor-right',cancel)
 def gaps():
  for entry,setup,want in [('terminal_control_0f62',lambda t:(t.put('terminal_dec_keys',0),t.put('terminal_newline_mode_9020',1)),0xba33),('terminal_control_11a8',lambda t:t.put('terminal_tab_wrap',1),0xb9eb),('terminal_control_11a8',lambda t:t.put('terminal_control_mode_9026',1),0x6dca),('terminal_control_11a8',lambda t:t.put('terminal_control_mode_1fb0',1),0xaad9)]:
   t=terminal();setup(t)
   try:t.call(entry)
   except MissingService as error:assert error.args[0]==want,(entry,error.args,want)
   else:raise AssertionError('unsupported emulation/protocol path silently succeeded')
 check('nondefault-emulation-and-protocol-services-remain-explicit',gaps)
 def fixture():
  t=terminal();payload=b'SAUCE00\r\n 20230904\x8b\x0b\x00\x00\x01\x01P\x00\x18\x00\x00\x00\x00\x00\x00\x03IBM VGA\r'
  t.feed(payload);assert t.index==len(payload) and not t.get('csi_unimplemented_service')
 check('synthetic-malformed-sauce-control-byte-fixture',fixture)
 if args.wire:
  def wire():
   t=terminal();data=args.wire.read_bytes();t.feed(data);assert t.index==len(data) and not t.get('csi_unimplemented_service')
  check('optional-actual-enigma-captured-wire-consumed',wire)
 result={'passed':True,'binary_sha256':hashlib.sha256(args.binary.read_bytes()).hexdigest(),'baseline_bytes':sum(unit['bytes'] for unit in proof['units']),'cases':cases,'optional_wire_sha256':hashlib.sha256(args.wire.read_bytes()).hexdigest() if args.wire else None,'scope':'Actual linked recovered control/cursor/render/history code; declared BIOS model. Synthetic public fixture; optional local capture is not a required test input.'}
 (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return result
if __name__=='__main__':main()
