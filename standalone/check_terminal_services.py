#!/usr/bin/env python3
"""Source-only support-unit and combined parser regression checks."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
from check_csi import Csi
ROOT=Path(__file__).resolve().parents[1]

def main():
 proof=json.loads((ROOT/'reconstruction/terminal_services/provenance.json').read_text())
 with tempfile.TemporaryDirectory() as temp:
  for unit in proof['units']:
   out=Path(temp)/'flat.bin'
   subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/unit['file']),'-o',str(out)],check=True)
   assert len(out.read_bytes())==unit['bytes'] and hashlib.sha256(out.read_bytes()).hexdigest()==unit['sha256']
 cases=[]
 def check(name,operation):
  operation();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def keys():
  for prefix,next_prefix in [('O','['),('[','O')]:
   c=Csi();c.put('terminal_dec_keys',1)
   entries=[bytes([27,ord(prefix),ch,0])+b'\xa5'*8 for ch in b'ABCD']
   # Include custom/longer bindings, an unmatched arrow suffix and final slot.
   entries += [b'CUSTOM\0'+b'\xa5'*5,bytes([27,ord(prefix),ord('A'),ord('X'),0])+b'\xa5'*7,
               bytes([27,ord(prefix),ord('E'),0])+b'\xa5'*8]
   while len(entries)<79:entries.append(b'\0'+b'\xa5'*11)
   entries[-1]=bytes([27,ord(prefix),ord('D'),0])+b'\xa5'*8
   original=b''.join(entries);c.uc.mem_write(c.symbols['terminal_keymap'],original)
   c.call('terminal_keyboard_mode',(ord(next_prefix),))
   want=bytearray(original)
   for i in [0,1,2,3,78]:want[i*12+1]=ord(next_prefix)
   assert bytes(c.uc.mem_read(c.symbols['terminal_keymap'],948))==want
   assert c.get('terminal_mode_372c')==0
   c.put('terminal_dec_keys',0);c.call('terminal_keyboard_mode',(ord(prefix),))
   assert bytes(c.uc.mem_read(c.symbols['terminal_keymap'],948))==want
 check('application-cursor-prefix-rewrite-preserves-custom-bindings-and-boundaries',keys)
 def tabs():
  for columns in [0,1,8,80,132]:
   c=Csi();c.put('screen_attribute_row_bytes',columns)
   c.call('csi_clear_tabs',(1,))
   want=bytes(range(0,columns,8))+b'\xfe'*(30-len(range(0,columns,8)))
   assert bytes(c.uc.mem_read(c.symbols['terminal_tab_stops'],30))==want
  c=Csi();c.call('csi_clear_tabs',(1,));c.sequence(b'[1;17H');c.sequence(b'[g')
  assert bytes(c.uc.mem_read(c.symbols['terminal_tab_stops'],30))==bytes([0,8,24,32,40,48,56,64,72])+b'\xfe'*21
  c.sequence(b'[0g');c.sequence(b'[3g')
  assert bytes(c.uc.mem_read(c.symbols['terminal_tab_stops'],30))==b'\xfe'*30
 check('default-tab-stops-and-real-csi-tab-clear',tabs)
 def reset():
  c=Csi();c.sequence(b'[5;20r');c.sequence(b'[r')
  assert (c.get('csi_scroll_top'),c.get('csi_scroll_bottom'))==(0,24)
  c.sequence(b'[20;5r')
  assert (c.get('csi_scroll_top'),c.get('csi_scroll_bottom'))==(0,24)
  c.sequence(b'[10;20H');c.put('attributes_current',0x4f);c.put('csi_origin_row',3)
  c.call('terminal_clear_home')
  assert (c.get('screen_cursor_row'),c.get('screen_cursor_column'))==(3,0)
  assert c.get('attributes_current')==7
  assert c.video_cells()==[0x0720]*2000
 check('real-scroll-region-reset-and-clear-home-bios-video',reset)
 out=ROOT/'build/csi/terminal-services-results.json'
 out.write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/csi/CSI.EXE').read_bytes()).hexdigest(),'recovered_bytes':sum(u['bytes'] for u in proof['units']),'cases':cases,'scope':'Exact support-unit hashes; actual linked key-table rewrite, tabs, region reset and clear/home; fixture key bindings, BIOS video model and no live modem.'},indent=2)+'\n')
if __name__=='__main__':main()
