#!/usr/bin/env python3
"""Reject malformed line-controller call/return frames and MZ relocations."""
import hashlib,json,re,struct,tempfile
from pathlib import Path
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal'
def main():
 binary=OUT/'TERMINAL.EXE';mp=OUT/'terminal.map';raw=binary.read_bytes();listing=mp.read_text();memory=inspect_terminal_memory(binary,mp)
 assert memory['line_controller_entry_pairs_verified']==4 and memory['line_controller_register_callbacks_verified']==3
 header=struct.unpack_from('<14H',raw);start=header[4]*16
 symbols={n:int(s,16)*16+int(o,16) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 mutations=[]
 for name in ('csi_service_d668','csi_service_d73c','csi_service_daf2','terminal_wait_control_n'):
  for delta,kind in ((1,'offset'),(3,'segment'),(5,'near-return')):
   bad=bytearray(raw);bad[start+symbols[name]+delta]^=1;mutations.append((name+':'+kind,bad,listing))
 for name in ('line_native_insert_far','line_native_delete_far','line_poll_far','line_tick_far','line_receive_far','attribute_screen_set_cursor_far'):
  for delta,kind in ((1,'native-target'),(3,'far-return')):
   bad=bytearray(raw);bad[start+symbols[name]+delta]^=1;mutations.append((name+':'+kind,bad,listing))
 lo,hi=symbols['line_controller_code_start'],symbols['line_controller_code_end'];owner=raw[start+lo:start+hi]
 # Every explicit far call/jump in this owned controller needs a segment fixup.
 refs=[symbols[n]+3 for n in ('csi_service_d668','csi_service_d73c','csi_service_daf2','terminal_wait_control_n')]
 for target in ('terminal_line_insert_far','terminal_line_delete_far','line_native_insert_far','line_native_delete_far','attribute_screen_set_cursor_far','line_poll_far','line_tick_far','line_receive_far','terminal_render_read_now','attribute_repair_admit_far','repair_abort_far'):
  # Map symbol addresses use a paragraph-aligned code segment with offsets;
  # locate its exact serialized seg:off pair from the linker map.
  match=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+'+re.escape(target)+r'\s*$',listing,re.M|re.I);assert match
  encoded=struct.pack('<HH',int(match[2],16),int(match[1],16))
  found=[lo+i+3 for i in range(len(owner)-4) if owner[i] in (0x9a,0xea) and owner[i+1:i+5]==encoded]
  assert found,target;refs.extend(found)
 assert len(refs)==len(set(refs))
 for wanted in refs:
  bad=bytearray(raw)
  for j in range(header[3]):
   off,seg=struct.unpack_from('<HH',bad,header[12]+4*j)
   if seg*16+off==wanted:struct.pack_into('<HH',bad,header[12]+4*j,0,0);break
  else:raise AssertionError(('No MZ relocation',wanted))
  mutations.append(('missing-line-MZ-relocation-'+hex(wanted),bad,listing))
 for symbol,other in [('line_controller_code_end','line_controller_code_start'),('line_controller_code_start','line_controller_code_end')]:
  match=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})([*+ ]+\s+)'+symbol+r'(\s*)$',listing,re.M|re.I);assert match
  target=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+'+other+r'\s*$',listing,re.M|re.I);assert target
  changed=listing[:match.start()]+target[1]+':'+target[2]+match[3]+symbol+match[4]+listing[match.end():]
  assert changed!=listing;mutations.append(('empty-or-reversed-'+symbol,raw,changed))
 with tempfile.TemporaryDirectory(prefix='pcplus-line-layout-') as tmp:
  exe=Path(tmp)/'BAD.EXE';mapfile=Path(tmp)/'bad.map'
  for name,damaged,text in mutations:
   exe.write_bytes(damaged);mapfile.write_text(text)
   try:inspect_terminal_memory(exe,mapfile)
   except AssertionError:pass
   else:raise AssertionError(('Malformed line controller accepted',name))
 result=dict(passed=True,binary_sha256=hashlib.sha256(raw).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rejected_mutations=[n for n,_,_ in mutations],far_relocations=len(refs),scope='Current source-built MZ/map, four resident entries, six register-only native callbacks including shared cursor service, every explicit controller far call/jump relocation and controller extent. Damaged files are inspected only, never executed. Separate actual linked and DOS tests establish behavior.')
 (OUT/'line-controller-layout-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Line controller layout:',len(mutations),'damaged frames/relocations/extents rejected')
if __name__=='__main__':main()
