#!/usr/bin/env python3
"""Unmodified DOS terminal plus declared test-only plane fixture and exit observer."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
ROOT=harness.ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);a=p.parse_args();assert re.fullmatch('[A-Za-z0-9_-]+',a.label)
 out=ROOT/'build/line-attributes-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
 binary=ROOT/'build/terminal/TERMINAL.EXE';listing=(ROOT/'build/terminal/terminal.map').read_text()
 group=re.search(r'^DGROUP\s+([0-9a-f]+):([0-9a-f]+)',listing,re.M|re.I);base=int(group[1],16)*16+int(group[2],16)
 symbols={name:int(seg,16)*16+int(off,16)-base for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 names=['screen_columns','screen_attributes_base','screen_attribute_cells','erase_attribute_values_base','erase_attribute_values','screen_cursor_wrap','attributes_normal_value','erase_cell_count','screen_cursor_row','screen_cursor_column']
 (out/'line_attributes_offsets.inc').write_text(''.join('%define '+n.upper()+' '+str(symbols[n])+'\n' for n in names))
 subprocess.run(['nasm','-fbin','-I',str(out)+'/',str(ROOT/'standalone/line_attributes_watch.asm'),'-o',str(out/'LATTR.COM')],check=True)
 esc=b'\x1b';header=esc+b'[2J'+esc+b'[HFIRST BYTE SAFE'+esc+b'[6n'+esc+b'[0c'
 def position(row,col):return esc+b'['+str(row+1).encode()+b';'+str(col+1).encode()+b'H'
 payload=header+position(5,17) # Declared single fixture boundary, before edits.
 video=[0x0720]*2000
 def text(row,col,data):
  nonlocal payload
  payload+=position(row,col)+data
  for i,c in enumerate(data):video[row*80+col+i]=0x700|c
 for i,c in enumerate(b'FIRST BYTE SAFE'):video[i]=0x700|c
 for row,data in [(1,b'TOP'),(2,b'R2'),(3,b'R3'),(4,b'R4'),(5,b'R5'),(6,b'BOTTOM')]:text(row,0,data)
 payload+=esc+b'[3;6r'+position(3,17)+esc+b'[M'+position(4,79)+esc+b'[3L'+esc+b'[r'
 # Delete row3: its boundary is removed. Only row3..5 may be repaired; the
 # protected marker at row10 must remain untouched and retain video attr07.
 for row in (3,4):video[row*80:(row+1)*80]=video[(row+1)*80:(row+2)*80]
 video[5*80:6*80]=[0x0720]*80
 # Count3 clips to the two remaining rows4..5; both end blank, column79 kept.
 video[4*80:6*80]=[0x0720]*160
 text(24,0,b'LAST')
 payload+=position(24,79)+esc+b'[32767L'+esc+b'[32767M'+esc+b'[6n'
 video[24*80:25*80]=[0x0720]*80
 inputs={str(p.relative_to(ROOT)):sha(p) for p in [binary,ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/test_terminal.py',ROOT/'standalone/line_attributes_watch.asm',Path(__file__)]}
 expected_flags=bytearray(2000);expected_flags[10*80]=0x81
 (out/'expectations.json').write_text(json.dumps(dict(inputs=inputs,peer_payload_hex=payload.hex(),expected_cursor=[24,79],expected_CPR_hex=(esc+b'[25;80R').hex(),fixture='One BIOS cursor boundary seeds logical flags/values and disjoint guard tails; all subsequent edits execute the unmodified DOS application.'),indent=2)+'\n')
 # Redirect only the owned output boundary, keeping the canonical modem/UART,
 # BIOS keyboard, hardware sampler and product launch unchanged.
 source=Path(harness.__file__).read_text();old="out=ROOT/'build/connection-dos'/name";assert source.count(old)==1
 scope=dict(harness.__dict__);scope['LABEL_ROOT']=out
 source=source.replace(old,"out=LABEL_ROOT/name")
 exec(compile(source,str(Path(harness.__file__)),'exec'),scope)
 result=scope['run']('product','success','p5000 a-x',arguments='@D:\\TEST.PRM /D:CaseTest:23 /A:NETWORK',banner=payload,files={'LATTR.COM':(out/'LATTR.COM').read_bytes()},observer='LATTR')
 raw=(out/'product/LINEATTR.BIN').read_bytes();assert len(raw)==12216
 state=struct.unpack_from('<12H',raw);flags=raw[24:24+4096];values=raw[24+4096:24+8192];screen=raw[24+8192:]
 checks=dict(canonical_DOS_harness=result['passed'],fixture_and_exit_seen=state[:4]==(0x4c41,1,1,0),DS_equals_SS=state[4]==state[5],temporary_state_restored=state[6:9]==(1,7,2000),cursor_preserved=state[9:11]==(24,79),post_edit_cursor_snapshots=state[11]>=3,flags_and_guards=flags==bytes(expected_flags)+b'\x55'*(4096-2000),values_and_guards=values==b'\x07'*2000+b'\x66'*(4096-2000),video_byte_exact=screen==struct.pack('<2000H',*video),last_row_CPR=esc+b'[25;80R' in (out/'product/serial.bin').read_bytes(),inputs_unchanged=inputs=={p:sha(ROOT/p) for p in inputs})
 report=dict(passed=all(checks.values()),checks=checks,binary_sha256=sha(binary),inputs=inputs,observer_program_sha256=sha(out/'LATTR.COM'),capture_sha256=sha(out/'product/LINEATTR.BIN'),state=list(state),scope='Actual unmodified DOS terminal EXE/UART/parser/native BIOS video and maintained far line owner. Explicit test-only BIOS-boundary plane fixture, passive post-edit cursor snapshots plus DOS-exit state, logical and4096-byte guard checks. Partial-region delete-boundary repair, repeated insert clipping and physical last-row huge counts; DS=SS/state/cursor and canonical hardware restoration. Not a normal configuration path for protected plane mode, a BBS server run or physical hardware.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],checks=checks),indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
