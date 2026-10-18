#!/usr/bin/env python3
"""Saved separator: production importer, editor, candidate, owner and live apply."""
import hashlib,json,struct
from pathlib import Path
from check_terminal_config import Import
from terminal_config_fixtures import image
from check_setup_model import Model as Editor,build as build_editor,image as setup_image
from check_live_configuration import Model as Candidate
from check_live_setup_owner import Owner
from check_directory_live import word
from check_live_setup_apply import launch
from live_setup_kernel import LiveSettings
from check_clipboard_live import Clipboard
ROOT=Path(__file__).resolve().parents[1]
def main():
 groups=[]
 def check(name,fn):
  n=fn();groups.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 def importer():
  for value in range(256):
   m=Import();status,data=m.decode(image(clipboard=value));assert status==0 and len(data)==44 and struct.unpack_from('<H',data,42)[0]==value
   m.uc.mem_write(m.symbols['terminal_configuration_values'],data);m.call('terminal_apply_configuration');assert m.get('_clipboard_separator')==value
  for value in (256,32768,65535):
   m=Import();assert m.decode(image(clipboard=value))==(13,b'\xcc'*44)
  return 259
 check('all256-PRM04EA-words-44-byte-import-and-startup-apply-invalid-high-bytes-reject',importer)
 def editor():
  build_editor();m=Editor();baseline=setup_image()
  for value in range(256):
   m.reset();assert m.set(45,str(value).encode())==0
   expected=bytearray(baseline);struct.pack_into('<H',expected,0x4ea,value)
   assert m.raw()==expected and m.get(45)==(0,str(value).encode()) and m.validate()==(0,65535)
  for value in (b'',b'-1',b'+13',b' 13',b'256',b'65535',b'4294967296'):
   m.reset();assert m.set(45,value)==2 and m.raw()==baseline
  for value in (256,65535):
   m.reset(word(baseline,0x4ea,value));assert m.get(45)[0]==3 and m.validate()==(3,45)
   assert m.set(45,b'13')==0 and m.validate()==(0,65535)
  return 265
 check('46th-editor-field-all256-values-only-two-bytes-change-invalid-reject-and-repair',editor)
 def candidates():
  Candidate.terminal=True
  for value in range(256):
   m=Candidate();m.raw=word(m.raw,0x4ea,value);assert m.decode()[0]==0
   assert m.change()==(0 if value==13 else 4096) and struct.unpack_from('<H',m.output(),42)[0]==value
  for directory in (False,True):
   m=Candidate(directory);m.raw=word(m.raw,0x4ea,256)
   assert m.decode(mask=15)[0]==(4 if directory else 2)
  m=Candidate();active=bytearray(m.baseline);struct.pack_into('<H',active,42,256);m.uc.mem_write(m.data_base+m.active,bytes(active));assert m.decode()[0]==5
  return 259
 check('all256-628-byte-candidates-new4096-change-bit-CLI-cannot-hide-invalid-and-active-validation',candidates)
 def owners():
  def active(m,sep):
   m.uc.mem_write(m.data_base+m.active,word(m.initial,42,sep))
  for directory in (False,True):
   m=Owner(directory);active(m,32);assert m.bind()==0 and m.begin()==0
   assert m.finish()==(0,(0,0,0,0)) and struct.unpack_from('<H',m.output(),42)[0]==32
   assert m.begin()==0;m.raw=word(m.raw,0x1ae,30)
   assert m.finish()==(0,(0,0,32,0)) and struct.unpack_from('<H',m.output(),42)[0]==32
   assert m.begin()==0;m.raw=word(m.raw,0x4ea,0)
   assert m.finish()==(0,(0,0,4096|32,0)) and struct.unpack_from('<H',m.output(),42)[0]==0
   # Acknowledge accepted saved value0. A later session override255 must survive
   # the same stored value, while a file revert to13 must be seen as an edit.
   assert m.invoke('_live_setup_acknowledge',[0])==0
   active(m,255);assert m.begin()==0
   assert m.finish()==(0,(0,0,32,0)) and struct.unpack_from('<H',m.output(),42)[0]==255
   assert m.begin()==0;m.raw=word(m.raw,0x4ea,13)
   assert m.finish()==(0,(0,0,4096|32,0)) and struct.unpack_from('<H',m.output(),42)[0]==13
  m=Owner();active(m,32);assert m.bind()==0 and m.begin()==0
  m.raw=word(m.raw,0x4ea,256);assert m.finish()[0]==5
  m.raw=word(m.raw,0x4ea,13);assert m.begin()==0 and m.finish()==(0,(0,0,0,0)) and struct.unpack_from('<H',m.output(),42)[0]==32
  m=Owner();active(m,32);assert m.bind()==0 and m.begin()==0
  assert m.invoke('_live_setup_abort',[0])==0 and m.invoke('_live_setup_acknowledge',[0])==0
  assert m.begin()==0 and m.finish()==(0,(0,0,0,0)) and struct.unpack_from('<H',m.output(),42)[0]==32
  # A saved edit can equal the current R value and therefore have no applied
  # change bit. A successful acknowledgement must still advance its baseline.
  m=Owner();active(m,32);assert m.bind()==0 and m.begin()==0;m.raw=word(m.raw,0x4ea,32)
  assert m.finish()==(0,(0,0,0,0)) and struct.unpack_from('<H',m.output(),42)[0]==32
  assert m.invoke('_live_setup_acknowledge',[0])==0
  active(m,255);assert m.begin()==0 and m.finish()==(0,(0,0,0,0)) and struct.unpack_from('<H',m.output(),42)[0]==255
  return 15
 check('session-R-preserved-on-noop-unrelated-save-invalid-file-abort-and-accepted-baseline-revert',owners)
 def live():
  for value in (0,13,32,255):
   m=LiveSettings();launch(m,word(m.raw,0x4ea,value));assert m.get('_clipboard_separator')==value
   assert m.get('terminal_setup_outcome',8)>>32&65535==(0 if value==13 else 4096)
   assert not m.get('terminal_quit') and m.vector_value()==m.parent_vector
  for changed in (False,True):
   m=LiveSettings();m.put('_clipboard_separator',32);launch(m,word(m.raw,0x1ae,30) if changed else m.raw)
   assert m.get('_clipboard_separator')==32 and not m.get('terminal_quit')
  m=Clipboard();m.put('_clipboard_separator',255);m.open_clip();m.add(b'one.zip');assert int.from_bytes(m.state()[2:4],'little')==255
  m.key(ord('r'));m.type(b'32');m.key(13);assert m.get('_clipboard_separator')==32
  m.key(27);m.put('_clipboard_separator',0);m.open_clip();assert m.names()==[b'ONE.ZIP'] and int.from_bytes(m.state()[2:4],'little')==0
  m.key(ord('p'));m.complete();assert bytes(m.tx)==b'ONE.ZIP\0\r'
  return 7
 check('real-live-setup-applies-or-preserves-global-and-existing-list-reopens-with-new-separator',live)
 sources=['standalone/check_clipboard_settings.py','standalone/check_terminal_config.py','standalone/check_setup_model.py','standalone/check_live_configuration.py','standalone/check_live_setup_owner.py','standalone/check_live_setup_apply.py','standalone/live_setup_kernel.py','standalone/terminal_config_fixtures.py','standalone/check_startup_import.py','standalone/check_clipboard_live.py']
 result=dict(passed=True,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),inputs=sum(g['inputs'] for g in groups),groups=groups,sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},scope='Actual linked importer44/candidate628/owner/live apply and source-owned editor field45. Hardware/file/child boundaries modeled in live tests; no original executable, raw native Setup binding, physical modem or actual DOS persistence claim.')
 (ROOT/'build/terminal/clipboard-settings-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Clipboard settings',result['inputs'],'inputs passed')
if __name__=='__main__':main()
