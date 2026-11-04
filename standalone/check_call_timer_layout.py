#!/usr/bin/env python3
"""Verify linked timer calls, relocations and all220 normalized native bytes."""
import argparse, hashlib, json, re, struct, subprocess
from pathlib import Path
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
m=DosImage(a.terminal,a.terminal.parent/'terminal.map');listing=(a.terminal.parent/'terminal.map').read_text()
entries={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
image=a.terminal.read_bytes();header=struct.unpack_from('<14H',image);relocations={s*16+o for o,s in (struct.unpack_from('<HH',image,header[12]+i*4)for i in range(header[3]))}
bank=entries['elapsed_start'][0]
code_names={0x3f73:'elapsed_seconds',0x778c:'elapsed_gettime',0x8d48:'elapsed_divide',0x8da8:'elapsed_remainder',0x82b6:'elapsed_sprintf'}
data_names={0xcff2:('elapsed_start_stamp',0),0xcd8e:('elapsed_start_seconds',0),0xcd90:('elapsed_start_seconds',2),0xcfec:('elapsed_hours',0),0xcfee:('elapsed_minutes',0),0xcff0:('elapsed_secs',0),0x473b:('elapsed_format',0),0x2c7c:('elapsed_duration',0)}
for name in (*code_names.values(),'elapsed_start','elapsed_update','terminal_call_timer_start_far','terminal_call_timer_stop_far','terminal_call_timer_refresh_far'):assert entries[name][0]==bank,name
sites=[]
for site,target in [('direct_connected','start'),('modem_connected','start'),('carrier_end','stop'),('retire_end','stop'),('direct_end','stop')]:
 name='terminal_call_timer_'+site+'_site';target='terminal_call_timer_'+target+'_far'
 addr=m.symbols[name];raw=bytes(m.uc.mem_read(addr,5));seg,off=entries[target]
 assert raw==b'\x9a'+struct.pack('<HH',off,m.base_segment+seg),name
 assert addr-m.base+3 in relocations,name
 sites.append(dict(site=name,target=target,segment_fixup=True))

def disasm(path,origin):
 rows=[]
 for line in subprocess.check_output(['ndisasm','-b16','-o'+str(origin),str(path)],text=True).splitlines():
  match=re.fullmatch(r'([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)',line);assert match,line
  rows.append((int(match[1],16),bytes.fromhex(match[2]),match[3]))
 return rows
units=[]
for name,entry,size in [('start',0x3f61,18),('seconds',0x3f73,41),('update',0x37a5,161)]:
 source=ROOT/f'reconstruction/local_controls/timer_{name}.asm';flat=out/(name+'-flat.bin')
 subprocess.run(['nasm','-fbin','-DRECON_FLAT','-I'+str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(flat)],check=True)
 symbol='elapsed_'+name;offset=entries[symbol][1];actual=out/(name+'-linked.bin')
 actual.write_bytes(bytes(m.uc.mem_read(m.symbols[symbol],size)))
 original_rows=disasm(flat,entry);linked_rows=disasm(actual,offset)
 assert len(original_rows)==len(linked_rows)
 for (at,raw,text),(lat,lraw,ltext) in zip(original_rows,linked_rows):
  assert at-entry==lat-offset and len(raw)==len(lraw)
  expected=text
  # Resolve only declared native call sites, data operands and local branches.
  call=re.fullmatch(r'call (0x[0-9a-f]+)',text)
  branch=re.fullmatch(r'(j\w+) (?:short |near )?(0x[0-9a-f]+)',text)
  if call:
   target=code_names[int(call[1],16)];expected='call '+hex(entries[target][1])
  elif branch:
   target=int(branch[2],16);assert entry<=target<entry+size
   expected=branch[1]+' '+hex(offset+target-entry)
   ltext=ltext.replace('short ','').replace('near ','')
  else:
   for address,(target,delta) in data_names.items():
    expected=re.sub(r'(?<![a-z0-9])'+hex(address)+r'(?![a-z0-9])',hex(m.offset(target)+delta),expected)
  assert expected==ltext,(name,hex(at),text,expected,ltext)
 units.append(dict(name=name,native_bytes=size,instructions=len(original_rows),linked_sha256=hashlib.sha256(actual.read_bytes()).hexdigest()))
result=dict(passed=True,terminal_sha256=hashlib.sha256(image).hexdigest(),far_sites=sites,units=units,
 sources={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [Path(__file__).resolve(),ROOT/'src/terminal/call_timer.asm',ROOT/'src/terminal/connection.asm']},
 scope=__doc__+' Declared near call/data binding and internal branch offsets are normalized; no instruction/operand is omitted. No execution of malformed images or physical acceptance.')
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS call timer layout:',len(sites),'far fixups and220 native bytes')
