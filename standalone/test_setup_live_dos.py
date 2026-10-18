#!/usr/bin/env python3
"""Open the production DOS settings editor from an already running terminal."""
import hashlib,json
from test_setup_startup_dos import run,OUT,BINARY,EDITOR
from check_setup_model import image

def main():
 cases=[]
 for name,keys,expected in [
  ('live-editor-cancel','p2000 a-f10 p500 escape space r e a d y',image()),
  ('live-editor-save','p2000 a-f10 p500 tab home del del del del 1 1 5 2 0 0 f10 escape space r e a d y',image()[:2]+b'\x08\0'+image()[4:])]:
  proof,actual=run(name,keys=keys,arguments='@TEST.PRM')
  assert actual==expected,(name,actual[:12],expected[:12])
  proof['checks']['exact_expected_PRM_after_live_child']=True
  assert b'ready' in (OUT/name/'serial.bin').read_bytes(),name
  proof['checks']['ordinary_typed_bytes_resume_after_editor']=True
  cases.append(proof)
 result=dict(passed=True,cases=cases,terminal_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),editor_sha256=hashlib.sha256(EDITOR.read_bytes()).hexdigest(),scope='Actual DOS terminal AltF10 to production PRMEDIT.EXE, staged cancel/save with exact opaque PRM preservation, return to same terminal display, initial serial replies and ordinary typed bytes delivered after editor return, independent active-UART and final hardware/vector samples. Saved baud change remains on disk for next startup; current connection retains original baud.')
 (OUT/'live-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
