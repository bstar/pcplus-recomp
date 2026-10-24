#!/usr/bin/env python3
"""Independent bounded line-plane/video oracle through actual parser and helpers."""
import hashlib,itertools,json,struct
from pathlib import Path
from unicorn.x86_const import *
from check_line_edit_live import Live,Abort,ROOT
from check_attribute_repair import Machine as Repair

def snapshots(t):
 return [bytes(t.uc.mem_read(t.symbols[n],4096)) for n in ('screen_attribute_cells','erase_attribute_values')]+[bytes(t.uc.mem_read(0xb8000,8000))]
def reference(flags,values,video,row,bottom,insert):
 flags=bytearray(flags);values=bytearray(values);video=list(video);start=row*80;end=(bottom+1)*80
 fill=(values[start-1] if start else values[0] if flags[0]&128 else 0x17) if insert else values[end-1]
 removed=any(f&128 for f in flags[start:start+80]);old=video[:]
 for y in range(row,bottom+1):
  source=y-1 if insert else y+1
  video[y*80:y*80+80]=old[source*80:source*80+80] if row<=source<=bottom else [fill*256+32]*80
 for plane,blank in ((flags,0),(values,fill)):
  if insert:plane[start+80:end]=plane[start:end-80];plane[start:start+80]=bytes([blank])*80
  else:plane[start:end-80]=plane[start+80:end];plane[end-80:end]=bytes([blank])*80
 if not insert and removed and row<bottom:
  r=object.__new__(Repair);r.cols=80;r.rows=bottom+1;r.flags=bytes(flags[:end]);r.values=bytes(values[:end]);r.cursor=start
  r.video=bytearray(struct.pack('<2000H',*video)+bytes(4000));r.shadow=bytearray(8000)
  repaired,painted,_,_=r.reference(2,True,None)
  values[:end]=repaired;video=list(struct.unpack('<2000H',painted[:4000]))
 return flags,values,video

def main():
 count=0;repairs=0;rejections=0
 geometries=[(1,0,0,0),(5,0,4,0),(5,1,3,2),(25,0,24,0),(25,0,24,23),(25,0,24,24),(25,3,10,5),(25,3,10,10)]
 for (height,top,bottom,row),insert,pattern,col,n,mono in itertools.product(geometries,(False,True),range(4),(0,79),(1,3),(0,1)):
  t=Live();t.put('csi_last_row',height-1);t.put('erase_cell_count',height*80);t.put('screen_first_row',top);t.put('screen_last_row',bottom);t.put('attributes_monochrome',mono);t.position(row,col)
  t.put('screen_cursor_wrap',0xffff if pattern==3 else 1)
  for key,value in [('attributes_current',0x9c),('attributes_preset_value',0x4e),('attributes_normal_value',0xab27),('csi_erase_attribute',0x17)]:t.put(key,value,1 if key!='attributes_normal_value' else 2)
  flags=bytearray(0 if pattern==0 else (0x80 if i%79==0 else i%4) if pattern==1 else (0x81 if i%80==0 else i%4) if pattern==2 else (0x80 if i in (row*80,(bottom+1)*80-1) else i%4) for i in range(height*80))
  values=bytearray((i*31+0x17)&255 for i in range(height*80));video=t.cells()
  t.uc.mem_write(t.symbols['screen_attribute_cells'],bytes(flags)+b'\x55'*(4096-len(flags)));t.uc.mem_write(t.symbols['erase_attribute_values'],bytes(values)+b'\x66'*(4096-len(values)))
  before=snapshots(t);wrap=t.get('screen_cursor_wrap');normal=t.get('attributes_normal_value');logical=t.get('erase_cell_count')
  for _ in range(min(n,bottom-row+1)):
   if not insert and row<bottom and any(f&128 for f in flags[row*80:(row+1)*80]):repairs+=1
   flags,values,video=reference(flags,values,video,row,bottom,insert)
  t.feed(b'\x1b['+str(n).encode()+(b'L' if insert else b'M'))
  after=snapshots(t)
  identity=(height,top,bottom,row,insert,pattern,col,n,mono)
  assert after[0]==bytes(flags)+before[0][logical:],(identity,'flags')
  assert after[1]==bytes(values)+before[1][logical:],(identity,'values')
  assert after[2][:4000]==struct.pack('<2000H',*video) and after[2][4000:]==before[2][4000:],(identity,'video')
  assert t.get('screen_cursor_wrap')==wrap and t.get('attributes_normal_value')==normal and t.get('erase_cell_count')==logical
  assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(row,col)
  for reg,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800),(UC_X86_REG_DS,t.ds),(UC_X86_REG_SS,t.ds)]:assert t.uc.reg_read(reg)==want,(identity,reg)
  assert t.uc.reg_read(UC_X86_REG_EFLAGS)&0x400==0,'Backward copy left DF set'
  count+=1
 mutations=[('screen_columns',79),('screen_attribute_row_bytes',79),('screen_video_row_bytes',158),('text_video_segment',0xb000),('screen_viewport_enabled',1),('screen_viewport_active',2),('screen_viewport_offset',1),('screen_last_column',78),('csi_last_row',25),('erase_cell_count',1999),('screen_attributes_base',0xff00),('erase_attribute_values_base',0xff00),('screen_cursor_column',80),('screen_attribute_offset',1),('screen_video_offset',1)]
 for service,(key,value) in itertools.product(('csi_service_d668','csi_service_d73c','csi_service_daf2'),mutations):
  t=Live();t.position(5,17);t.put('screen_cursor_wrap',1);t.put('ansi_parameters',3);t.put(key,value);before=snapshots(t)
  try:t.call(service)
  except Abort as e:assert e.args==(0x2d98,)
  else:raise AssertionError(('Missing pre-edit rejection',service,key))
  assert snapshots(t)==before and t.get('ansi_parameters')==3
  assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(5,80 if key=='screen_cursor_column' else 17)
  rejections+=1
 assert repairs
 result=dict(passed=True,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),cases=count,repair_operations=repairs,pre_mutation_rejections=rejections,checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),repair_reference_sha256=hashlib.sha256((ROOT/'standalone/check_attribute_repair.py').read_bytes()).hexdigest(),scope='Actual UART/parser NETWORK line dispatch, maintained bounded plane owner, real recovered native video-only line helpers and native field repair. Independent window shifts and field oracle; complete4096-byte planes/video canaries, smaller heights, final row, restricted margins, repeat counts, both profile gates, raw wrap word, DF/DS=SS/callee registers and sticky-state restoration. Modeled hardware/BIOS; no actual DOS/BBS or physical claim.')
 (ROOT/'build/terminal/line-attributes-live-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Bounded line attributes:',count,'cases,',repairs,'repairs,',rejections,'pre-edit rejections PASS')
if __name__=='__main__':main()
