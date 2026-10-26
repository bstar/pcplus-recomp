#!/usr/bin/env python3
"""Actual linked reference, command dispatch and serviced UI; hardware/DOS modeled."""
import argparse,json,re,hashlib
from pathlib import Path
import check_transport as transport


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();base=binary.parent;manifest=json.loads((base/'manifest.json').read_text())
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 assert manifest['experimental_original_reference'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(transport.ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=base/'terminal.map'
 from check_recording_ui_live import UI
 from check_recording_rx_live import ordinary
 UI.browser_key=0x2960
 source=(transport.ROOT/'src/redisplay/command_reference.c').read_text()
 names=dict(re.findall(r'NAME\((\w+),"([^"\\]*)",',source))
 items=[dict(id=n,key=int(k,16),row=int(r),column=int(c),action=int(v)) for n,k,r,c,v in
        re.findall(r'ITEM\((\w+),(0x[0-9a-f]+),(\d+),(\d+),(\d+)\)',source)]
 assert len(items)==39
 native=json.loads((transport.ROOT/'reconstruction/command_reference/provenance.json').read_text())
 assert [names[x['id']] for x in items]==[x['name'] for x in native['labels']]
 cases=[]
 def check(name,fn):
  n=fn();cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 def open_ref(m):
  m.key(0x2c00);assert m.get('_command_menu_active') and b'COMMUNICATIONS' in m.text()
 def layout():
  m=UI();open_ref(m);text=m.text()
  for item in items:assert names[item['id']].encode() in text,item
  assert b'SET UP' in text and b'OTHER FUNCTIONS' in text
  for item in items:
   col=[3,28,54][item['column']];at=item['row']*160+col*2
   assert text[item['row']*80+col:].startswith(names[item['id']].encode())
   attribute=m.uc.mem_read(0xb8000+at+1,1)[0]
   assert attribute==(0x70 if item is items[0] else 8 if item['action']==255 else 7)
  m.key(27);assert not m.get('_redisplay_active') and not m.tx and not m.get('terminal_quit')
  return 39
 check('all-39-native-labels-column-placement-and-availability-attributes',layout)
 def refusals():
  count=0
  for item in items:
   if item['action']!=255:continue
   m=UI();m.put('connection_state',6);before=bytes(m.uc.mem_read(0xb8000,4000));m.key(item['key'])
   assert b'Not available in this build:' in m.text() and names[item['id']].encode() in m.text()
   assert m.get('_command_menu_active') and not m.get('terminal_quit') and not m.tx
   assert m.get('connection_state')==6 and not m.handles
   m.key(27);assert bytes(m.uc.mem_read(0xb8000,4000))==before
   assert not m.get('_redisplay_active') and not m.get('terminal_quit');count+=1
  return count
 check('every-unavailable-original-shortcut-refuses-without-wire-file-or-carrier-change',refusals)
 def help_and_navigation():
  m=UI();open_ref(m);m.key(0x4d00);m.key(0x5000);m.key(0x5000)
  before=bytes(m.uc.mem_read(0xb8000,4000));m.key(0x3b00)
  assert b'Choose a local DOS file' in m.text()
  m.key(27);assert bytes(m.uc.mem_read(0xb8000,4000))==before
  m.key(0x2960);assert b'Receive files' in m.text() and b'COMMUNICATIONS' not in m.text()
  m.key(0x2960);assert b'COMMUNICATIONS' in m.text();m.key(27)
  assert not m.tx and not m.get('_redisplay_active') and not m.get('terminal_quit')
  return 9
 check('column-navigation-contextual-help-return-and-backtick-browser-toggle',help_and_navigation)
 def received():
  m=UI();open_ref(m);before=bytes(m.uc.mem_read(0xb8000,4000));data=b'BBS-ACTIVE'
  m.call('terminal_redisplay_before');ordinary(m,data+b'\x1b[6n');m.call('terminal_redisplay_idle');m.drain()
  assert bytes(m.uc.mem_read(0xb8000,4000))==before
  assert bytes(m.tx)==b'\x1b[1;11R' and not m.get('uart_rx_dropped')
  m.key(27);assert data in m.text() and not m.get('terminal_quit')
  return 1
 check('live-UART-parser-query-and-updated-screen-restoration-through-reference',received)
 def transfers():
  for key in [0x4900,0x49e0,0x5100,0x51e0]:
   m=UI();open_ref(m);m.key(key)
   assert m.get('terminal_transfer_pending') and not m.get('_command_menu_active')
   m.keys.append(27);m.call('terminal_transfer_poll',limit=6000000)
   assert not m.get('terminal_transfer_pending') and not m.get('terminal_quit') and not m.tx
  return 4
 check('reference-page-shortcuts-enter-real-send-receive-and-cancel-cleanly',transfers)
 def script_and_info():
  m=UI();m.key(0x6c00);assert b'Script DOS 8.3 path:' in m.text()
  m.key(27);assert b'COMMUNICATIONS' in m.text();m.key(27)
  m=UI();m.start_record();m.key(0x6c00)
  assert b'Save or cancel recording' in m.text() and m.field('state')==1
  assert not m.get('terminal_program_pending');m.key(27);m.key(27)
  m=UI();m.key(0x1700);assert b'Application status' in m.text()
  m.key(27);assert b'COMMUNICATIONS' in m.text();m.key(27)
  return 3
 check('original-script-and-info-keys-use-owned-prompts-and-recorder-refusal',script_and_info)
 def translation():
  for via_reference in [False,True]:
   m=UI()
   if via_reference:open_ref(m)
   m.key(0x1100)
   assert m.get('terminal_translation_edit_status')==4
   assert not m.get('_command_menu_active') and not m.get('terminal_quit') and not m.tx
  m=UI();m.key(0x6f00);assert b'Not available in this build:' in m.text()
  assert m.get('terminal_translation_edit_status')==0 and not m.get('terminal_program_pending')
  return 3
 check('Alt-W-translation-binding-and-Alt-F8-never-launches-wrong-editor',translation)
 def owners():
  for owner in ['terminal_transfer_pending','terminal_program_pending','terminal_macro_active',
                'terminal_monitor_active','terminal_controller_active','terminal_ansi_wait_active']:
   m=UI();m.put(owner,1);m.key(0x2000)
   assert not m.get('_command_menu_active') and not m.get('terminal_quit')
  return 6
 check('unavailable-key-refusal-respects-existing-exclusive-byte-owners',owners)
 result=dict(passed=True,cases=cases,inputs=sum(r['inputs'] for r in cases),binary_sha256=sha(binary),
  source_inputs={str(p.relative_to(transport.ROOT)):sha(p) for p in [Path(__file__).resolve(),
   transport.ROOT/'src/redisplay/command_reference.c',transport.ROOT/'reconstruction/command_reference/provenance.json']},
  scope=__doc__+' Functional names/static grouping follow original file data. Navigation/refusal is maintained; no original runtime/pixel equivalence or physical hardware claim.')
 (base/'reference-checks.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
