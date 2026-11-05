#!/usr/bin/env python3
"""Run the linked listing formatter and fixed-field editor with independent expectations."""
import argparse,json,struct
from pathlib import Path
from check_directory_identity import Identity,ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['terminal','output']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_file_directory'] and sha(binary)==manifest['binary_sha256']
 m=Identity(binary);rows=[]
 for name in [b'F00.TXT',b'LONGNAME.EXT',b'\x82CHO.TXT']:
  for year in [1980,1993,2000,2026,2107]:
   for hour,minute in [(0,0),(14,32),(23,59)]:
    for size in [0,1,999999,1000000,0xffffffff]:
     for attr in [0,1,0x10,0x11]:
      date=((year-1980)<<9)|(7<<5)|9;time=(hour<<11)|(minute<<5)|5
      entry=struct.pack('<13sxHHHI',name,attr,time,date,size);at=m.stage_near(entry)
      m.uc.mem_write(0xb8000,b'Z'*64);m.bank('_file_dialog_format',[at,0,0xb800],far=True)
      prefix=name.decode('cp437').ljust(12);suffix=f' 7-09-{year%100:02d}'
      if attr==0x10:expected=prefix+'   <DIR>  '+suffix+'  '+f'{hour:02d}:{minute:02d}'
      elif size<=999999:expected=prefix+'  '+f'{size:6d}'+'  '+suffix+'  '+f'{hour:02d}:{minute:02d}'
      else:expected=prefix+' '+f'{size:10d}'+' '+suffix+' '+f'{hour:02d}:{minute:02d}'
      want=expected.ljust(38).encode('cp437')+b'\0';actual=bytes(m.uc.mem_read(0xb8000,64))
      assert len(want)==39 and actual==want+b'Z'*25,(year,size,attr,actual,want)
      rows.append(dict(year=year,size=size,attr=attr,passed=True))
 state_address=m.symbols['_terminal_file_dialog_state'];field=bytes(range(33,97));edits=0
 for position,full in [(i,0) for i in range(64)]+[(63,1)]:
  for insert in [0,1]:
   for key in [0x0e08,0x5300,0x4b00,0x4d00,0x4700,0x4f00,0x7500,0x5200,ord('Z')]:
    state=bytearray(1676);struct.pack_into('<13H',state,0,0x4644,1,1,position,insert,full,25,0,0,0,0,0,0);state[26:90]=field
    m.uc.mem_write(state_address,bytes(state));want=field;cur=position;latch=full;ins=insert
    if key==0x0e08:
     latch=0
     if cur:cur-=1;want=field[:cur]+field[cur+1:]+b' '
    elif key==0x5300:latch=0;want=field[:cur]+field[cur+1:]+b' '
    elif key==0x4b00:latch=0;cur=max(0,cur-1)
    elif key==0x4d00:cur=min(63,cur+1)
    elif key==0x4700:latch=0;cur=0
    elif key==0x4f00:latch=0;cur=63
    elif key==0x7500:latch=0;want=field[:cur]+b' '*(64-cur)
    elif key==0x5200:ins=1-insert
    elif not full:
     want=field[:cur]+b'Z'+field[cur:63] if insert else field[:cur]+b'Z'+field[cur+1:]
     if cur==63:latch=1
     else:cur+=1
    assert m.bank('_file_dialog_event',[1,key,0,0xb800],far=True)==1
    actual=bytes(m.uc.mem_read(state_address,1676));head=struct.unpack_from('<13H',actual)
    assert head[:6]==(0x4644,1,1,cur,ins,latch) and actual[26:90]==want,(position,full,insert,key,head[:6],actual[26:90],want)
    edits+=1
 sources=['standalone/check_file_dialog_linked.py','standalone/check_directory_identity.py','standalone/dos_image.py','standalone/terminal_memory.py']
 out.mkdir(parents=True);r=dict(passed=True,binary_sha256=sha(binary),formatter_cases=len(rows),editor_cases=edits,sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Actual relocated far cdecl functions with DS=SS and stack/register checks. Metadata covers CP437 names, DIR equality,1980–2107,32-bit sizes and output canaries; no DOS/BIOS endpoint is modeled or invoked. Full UI/search/serial acceptance is separate.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(rows),'formatter cases;',edits,'editor cases')
if __name__=='__main__':main()
