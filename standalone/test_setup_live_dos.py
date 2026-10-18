#!/usr/bin/env python3
"""Open the production DOS settings editor from an already running terminal."""
import hashlib,json
from test_setup_startup_dos import run,OUT,BINARY,EDITOR
from check_setup_model import image
from check_directory_live import word

def main():
 cases=[]
 for name,keys,expected,rate_mask,line_mask in [
  ('live-editor-cancel','p2000 a-f10 p500 escape space r e a d y',image(),1,1),
  ('live-editor-save','p2000 a-f10 p500 tab home del del del del 1 1 5 2 0 0 f10 escape space r e a d y',image()[:2]+b'\x08\0'+image()[4:],1,1),
  ('live-editor-apply-color','p2000 a-f10 p500 pgdown tab tab tab home del del 1 e f10 escape space r e a d y',word(image(),0x1ae,30),1,1),
  ('live-editor-apply-baud','p2000 a-f10 p500 tab home del del del del 1 1 5 2 0 0 f10 escape y r e a d y',word(image(),2,8),3,1),
  ('live-editor-apply-line','p2000 a-f10 p500 tab tab home del 7 tab home del e tab home del 2 f10 escape y r e a d y',word(word(word(image(),4,2),6,2),8,7),1,3),
  ('live-editor-translation-deferred','p2000 a-f10 p500 pgdown tab tab tab tab tab tab tab tab home del 2 f10 escape space r e a d y',word(image(),0x1e0,2),1,1),
  ('live-editor-apply-flow','p2000 a-f10 p500 tab tab tab tab tab home del 1 tab home del 0 f10 escape y r e a d y',word(word(image(),0x198,1),0x19a,0),1,1)]:
  proof,actual=run(name,keys=keys,arguments='@TEST.PRM',post_echo=True,rate_mask=rate_mask,line_mask=line_mask)
  assert actual==expected,(name,actual[:12],expected[:12])
  proof['checks']['exact_expected_PRM_after_live_child']=True
  assert b'ready' in (OUT/name/'serial.bin').read_bytes(),name
  proof['checks']['ordinary_typed_bytes_resume_after_editor']=True
  if name.endswith('apply-flow'):
   wire=(OUT/name/'serial.bin').read_bytes();assert wire.count(b'\x11')==1 and wire.index(b'\x11')<wire.index(b'ready')
   proof['checks']['new_software_flow_announces_XON_before_ordinary_data']=True
  screen=(OUT/name/'SCREEN.BIN').read_bytes();want=30 if name.endswith('apply-color') else 7
  assert screen[22:32:2]==b' LIVE' and screen[23:33:2]==bytes([want])*5,(name,screen[:34])
  proof['checks']['new_remote_characters_use_expected_live_attribute']=True
  cases.append(proof)
 keyboard=b''.join(b''.join(('P%d-%02d'%(profile,slot)).encode().ljust(12,b'\0') for slot in range(79)) for profile in range(7))
 for name,answer,kbd,profile,clear,key_bytes in [
  ('live-editor-apply-profile','y',None,6,True,None),
  ('live-editor-decline-profile','space',None,4,False,None),
  ('live-editor-profile-explicit','y',keyboard,6,True,b'P6-16'),
  ('live-editor-profile-missing-block','y',keyboard[:5*948],4,False,b'P4-16')]:
  keys='p2000 a-f10 p500 pgdown home del 6 f10 escape '+answer+' r e a d y'+(' f1' if kbd is not None else '')
  proof,actual=run(name,keys=keys,arguments='@TEST.PRM'+(' /K:TEST.KBD' if kbd is not None else ''),post_echo=True,rate_mask=1,line_mask=1,expected_profile=profile,profile_clear=clear,keyboard_file=kbd)
  assert actual==word(image(),0x194,6);proof['checks']['exact_expected_PRM_after_live_child']=True
  wire=(OUT/name/'serial.bin').read_bytes();assert b'ready' in wire
  if key_bytes is not None:assert key_bytes in wire;proof['checks']['correct_profile_F1_mapping_reached_peer']=True
  screen=(OUT/name/'SCREEN.BIN').read_bytes();start=0 if clear else 22
  assert screen[start:start+10:2]==b' LIVE' and screen[start+1:start+11:2]==b'\x07'*5
  proof['checks']['clear_or_preserve_screen_matches_profile_choice']=True;cases.append(proof)
 result=dict(passed=True,cases=cases,terminal_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),editor_sha256=hashlib.sha256(EDITOR.read_bytes()).hexdigest(),scope='Actual DOS AltF10 production editor: cancel, baud decline/accept, color,7E2, flow and profile choices. Fresh post-child CPR/DA and cell attributes verify resumed duplex operation and profile clear/preservation. Explicit KBD target mapping reaches the peer through F1; a missing target block retains the old mapping/profile. Independent INT1C divisor/LCR samples and exact final UART/PIC/vector restoration pass. Physical UART/firmware timing remains unverified.')
 (OUT/'live-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
