#!/usr/bin/env python3
"""Open the production DOS settings editor from an already running terminal."""
import hashlib,json
from test_setup_startup_dos import run,OUT,BINARY,EDITOR
from check_setup_model import image
from check_directory_live import word

def main():
 cases=[]
 for name,keys,expected in [
  ('live-editor-cancel','p2000 a-f10 p500 escape space r e a d y',image()),
  ('live-editor-save','p2000 a-f10 p500 tab home del del del del 1 1 5 2 0 0 f10 escape space r e a d y',image()[:2]+b'\x08\0'+image()[4:]),
  ('live-editor-apply-color','p2000 a-f10 p500 pgdown tab tab tab home del del 1 e f10 escape space r e a d y',word(image(),0x1ae,30))]:
  proof,actual=run(name,keys=keys,arguments='@TEST.PRM',post_echo=True)
  assert actual==expected,(name,actual[:12],expected[:12])
  proof['checks']['exact_expected_PRM_after_live_child']=True
  assert b'ready' in (OUT/name/'serial.bin').read_bytes(),name
  proof['checks']['ordinary_typed_bytes_resume_after_editor']=True
  screen=(OUT/name/'SCREEN.BIN').read_bytes();want=30 if name.endswith('apply-color') else 7
  assert screen[22:32:2]==b' LIVE' and screen[23:33:2]==bytes([want])*5,(name,screen[:34])
  proof['checks']['new_remote_characters_use_expected_live_attribute']=True
  cases.append(proof)
 result=dict(passed=True,cases=cases,terminal_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),editor_sha256=hashlib.sha256(EDITOR.read_bytes()).hexdigest(),scope='Actual DOS terminal AltF10 to production PRMEDIT.EXE, cancel and exact opaque baud/color saves. After editor return the peer receives typed bytes, sends new display bytes and gets a fresh cursor reply; new cells prove the saved normal attribute was adopted live. Independent active-UART and final hardware/vector samples show baud-only save stays deferred and the connection retains its original rate.')
 (OUT/'live-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
