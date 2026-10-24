#!/usr/bin/env python3
"""Independent logical field/metadata oracle for ICH/DCH through the real parser."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
import check_transport
from check_reset_live import fixture,ROOT
from check_viewport_live import logical
from check_attribute_repair import Machine as Repair

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reference(cells,flags,values,rows,row,col,unit,insert,count,wrap,protected,cols=132):
 cells=list(cells);flags=bytearray(flags);values=bytearray(values);start=row*cols+col;repairs=0;edits=0
 if unit==2 and col%2:return cells,flags,values,edits,repairs
 bound=(row+1)*cols
 if protected:bound=next((i for i in range(start,bound)if flags[i]&0x81),bound)
 for _ in range(min(1 if count>32767 else count,(bound-start)//unit)):
  end=(row+1)*cols
  if protected:
   end=next((i for i in range(start,end)if flags[i]&0x81),end)
  if end-start<unit:break
  removed=bool(wrap and not protected and not insert and any(x&0x80 for x in flags[start:start+unit]))
  fill=cells[start]&0xff00 if insert else 0x2700
  if insert:cells[start:end]=[fill|32]*unit+cells[start:end-unit]
  else:cells[start:end]=cells[start+unit:end]+[fill|32]*unit
  blank=start if insert else end-unit
  if wrap and not protected:
   for plane in (flags,values):
    if insert:plane[start+unit:end]=plane[start:end-unit]
    else:plane[start:end-unit]=plane[start+unit:end]
   for i in range(blank,blank+unit):flags[i]&=0xfe
  if wrap and (not protected or not insert):
   for i in range(blank,blank+unit):cells[i]=0x20|(values[i]<<8)
  if removed:
   oracle=object.__new__(Repair);oracle.cols=cols;oracle.rows=rows;oracle.cursor=start
   oracle.flags=bytes(flags);oracle.values=bytes(values);oracle.video=bytearray(struct.pack('<'+str(len(cells))+'H',*cells));oracle.shadow=bytearray(8000)
   repaired,painted,_,_=oracle.reference(2,True,None)
   values[:]=repaired;cells=list(struct.unpack('<'+str(len(cells))+'H',painted));repairs+=1
  edits+=1
 return cells,flags,values,edits,repairs

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']and manifest['native_reset_transaction']
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map';cases=0;edits=0;repairs=0;blocked=0
 for rows,hidden in [(1,0),(5,0),(24,0),(25,1)]:
  for profile,col,unit,insert,wrap,protected,pattern in itertools.product((4,6),(0,51,79,80,130,131),(1,2),(False,True),(0,1),(0,1),range(3)):
   if not(wrap or protected)or unit==2 and col%2:continue
   m,address=fixture(profile,rows=rows,hidden=hidden);assert m.call('terminal_native_width',ax=1,limit=2000000)==0
   row=rows//2;size=rows*132;start=row*132+col
   flags=bytearray(size);values=bytearray((i*31+0x17)&255 for i in range(size));cells=[((i%0x70+7)<<8)|((i*7)%90+33)for i in range(size)]
   if not protected:
    for i in range(size):flags[i]=i%4
   marks={start}if pattern==0 else{min(row*132+131,start+3)}if pattern==1 else{row*132+131,min(size-1,(row+1)*132+3)}
   for i in marks:flags[i]=0x80|(i&1)
   flags_before=bytes(flags)+b'\x55'*(4096-size);values_before=bytes(values)+b'\x66'*(4096-size)
   m.uc.mem_write(m.symbols['screen_attribute_cells'],flags_before);m.uc.mem_write(m.symbols['erase_attribute_values'],values_before)
   backing=bytearray(b'\x5a'*8192);backing[:size*2]=struct.pack('<'+str(size)+'H',*cells);m.uc.mem_write(address,bytes(backing))
   for y in range(rows):m.uc.mem_write(0xb8000+y*160,struct.pack('<80H',*cells[y*132:y*132+80]))
   m.uc.mem_write(m.symbols['screen_line_flags'],bytes(128))
   if unit==2:m.uc.mem_write(m.symbols['screen_line_flags']+row,b'\x40')
   m.position(row,col)
   for name,value in dict(screen_cursor_wrap=wrap,screen_attribute_checks=protected,attributes_current=0x9c,attributes_preset_value=0x4e,attributes_normal_value=0xab27,csi_erase_attribute=0x17).items():m.put(name,value)
   oldvideo=bytes(m.uc.mem_read(0xb8000,4000));oldshadow=bytes(m.uc.mem_read(address,8192))
   expected,flags,values,n,r=reference(cells,flags,values,rows,row,col,unit,insert,3,wrap,protected)
   m.feed(b'\x1b[3'+(b'@'if insert else b'P'))
   identity=(rows,profile,col,unit,insert,wrap,protected,pattern)
   assert logical(m,address,rows)==struct.pack('<'+str(size)+'H',*expected),(identity,'video')
   assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096))==bytes(flags)+flags_before[size:],(identity,'flags')
   assert bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096))==bytes(values)+values_before[size:],(identity,'values')
   assert bytes(m.uc.mem_read(address+size*2,8192-size*2))==backing[size*2:]
   assert bytes(m.uc.mem_read(0xb8000+rows*160,4000-rows*160))==oldvideo[rows*160:]
   assert(m.get('screen_cursor_row'),m.get('screen_cursor_column'),m.get('screen_cursor_wrap'),m.get('screen_attribute_checks'))==(row,col,wrap,protected)
   if not n:assert bytes(m.uc.mem_read(address,8192))==oldshadow
   cases+=1;edits+=n;repairs+=r;blocked+=not n
 narrow_cases=0
 for insert,wrap,protected,pattern in itertools.product((False,True),(0,1),(0,1),(0,1)):
  if not(wrap or protected):continue
  rows=24;size=rows*80;row=5;col=17;start=row*80+col
  m,address=fixture();assert m.call('terminal_native_width',ax=1,limit=2000000)==0;assert m.call('terminal_native_width',ax=0,limit=2000000)==0
  m.uc.mem_write(m.symbols['screen_line_flags'],bytes(128));m.position(row,col)
  flags=bytearray(size);flags[start if pattern==0 else start+3]=0x80
  values=bytearray((i*31+23)&255 for i in range(size));cells=[((i%112+7)<<8)|((i*7)%90+33)for i in range(size)]
  m.uc.mem_write(m.symbols['screen_attribute_cells'],bytes(flags)+b'\x55'*(4096-size));m.uc.mem_write(m.symbols['erase_attribute_values'],bytes(values)+b'\x66'*(4096-size))
  m.uc.mem_write(0xb8000,struct.pack('<'+str(size)+'H',*cells));status=bytes(m.uc.mem_read(0xb8000+size*2,4000-size*2));shadow=bytes(m.uc.mem_read(address,8192))
  for name,value in dict(screen_cursor_wrap=wrap,screen_attribute_checks=protected,attributes_current=0x9c,attributes_preset_value=0x4e,attributes_normal_value=0xab27,csi_erase_attribute=0x17).items():m.put(name,value)
  expected,flags,values,_,_=reference(cells,flags,values,rows,row,col,1,insert,3,wrap,protected,cols=80)
  m.feed(b'\x1b[3'+(b'@'if insert else b'P'))
  assert bytes(m.uc.mem_read(0xb8000,size*2))==struct.pack('<'+str(size)+'H',*expected),('narrow',insert,wrap,protected,pattern,'video')
  assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096))==bytes(flags)+b'\x55'*(4096-size)
  assert bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096))==bytes(values)+b'\x66'*(4096-size)
  assert bytes(m.uc.mem_read(address,8192))==shadow and bytes(m.uc.mem_read(0xb8000+size*2,4000-size*2))==status
  narrow_cases+=1
 report=dict(passed=True,binary_sha256=sha(binary),cases=cases,edits=edits,repairs=repairs,blocked=blocked,narrow_field_cases=narrow_cases,sources=manifest['sources'],checker_sha256=sha(Path(__file__)),repair_reference_sha256=sha(ROOT/'standalone/check_attribute_repair.py'),scope=__doc__+' Plain and field modes, both panes, coherent paired metadata, marker deletion native mode2 repair and field-limited shifts. Hardware modeled; no DOS/BBS or full peer width acceptance.')
 (binary.parent/'width-field-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS wide fields:',cases,'cases,',edits,'edits,',repairs,'repairs,',blocked,'blocked,',narrow_cases,'narrow field cases')
if __name__=='__main__':main()
