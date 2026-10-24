#!/usr/bin/env python3
"""Independent region/field oracle for actual LF, IND and RI parser consumers."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport
from check_reset_live import fixture,ROOT,Abort
from check_viewport_live import logical
from check_attribute_repair import Machine as Repair

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reference(cells,flags,values,cols,rows,top,bottom,down,fill,skip):
 cells=list(cells);flags=bytearray(flags);values=bytearray(values);first=top*cols;end=(bottom+1)*cols
 old=cells[:]
 for row in range(top,bottom+1):
  source=row-1 if down else row+1
  cells[row*cols:(row+1)*cols]=old[source*cols:(source+1)*cols]if top<=source<=bottom else[(fill<<8)|32]*cols
 for plane,blank in ((flags,0),(values,fill)):
  if down:plane[first+cols:end]=plane[first:end-cols];plane[first:first+cols]=bytes([blank])*cols
  else:plane[first:end-cols]=plane[first+cols:end];plane[end-cols:end]=bytes([blank])*cols
 repairs=0;start=(top+int(down))*cols
 if not skip and top<bottom and not flags[start]&0x80:
  carry=values[start-1]if start else 0x17
  if values[start]!=carry:
   r=object.__new__(Repair);r.cols=cols;r.rows=rows;r.cursor=start;r.flags=bytes(flags[:end]);r.values=bytes(values[:end])
   r.video=bytearray(struct.pack('<'+str(len(cells))+'H',*cells));r.shadow=bytearray(8000)
   repaired,painted,_,_=r.reference(2,True,None);values[:end]=repaired;cells=list(struct.unpack('<'+str(len(cells))+'H',painted));repairs=1
 return cells,flags,values,repairs

def line_reference(cells,flags,values,cols,rows,row,bottom,insert,count):
 cells=list(cells);flags=bytearray(flags);values=bytearray(values);repairs=0;first=row*cols;end=(bottom+1)*cols
 for _ in range(min(count,bottom-row+1)):
  removed=not insert and any(x&0x80 for x in flags[first:first+cols])
  fill=(values[first-1]if first else values[0]if flags[0]&0x80 else 0x17)if insert else values[end-1]
  old=cells[:]
  for y in range(row,bottom+1):
   origin=y-1 if insert else y+1
   cells[y*cols:(y+1)*cols]=old[origin*cols:(origin+1)*cols]if row<=origin<=bottom else[(fill<<8)|32]*cols
  for plane,blank in ((flags,0),(values,fill)):
   if insert:plane[first+cols:end]=plane[first:end-cols];plane[first:first+cols]=bytes([blank])*cols
   else:plane[first:end-cols]=plane[first+cols:end];plane[end-cols:end]=bytes([blank])*cols
  if removed and row<bottom:
   r=object.__new__(Repair);r.cols=cols;r.rows=rows;r.cursor=first;r.flags=bytes(flags[:end]);r.values=bytes(values[:end]);r.video=bytearray(struct.pack('<'+str(len(cells))+'H',*cells));r.shadow=bytearray(8000)
   fixed,painted,_,_=r.reference(2,True,None);values[:end]=fixed;cells=list(struct.unpack('<'+str(len(cells))+'H',painted));repairs+=1
 return cells,flags,values,repairs

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();mft=json.loads((binary.parent/'manifest.json').read_text());assert mft['native_reset_transaction']and sha(binary)==mft['binary_sha256']
 for name,digest in mft['sources'].items():assert sha(ROOT/name)==digest,name
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map';cases=0;repairs=0
 for rows,hidden in [(1,0),(5,0),(24,0),(25,1)]:
  for cols,profile,right,(command,policy),restricted,protected,skip in itertools.product((80,132),(4,6),(False,True),[(op,0)for op in (b'\n',b'\x1bD',b'\x1bM',b'wrap')]+[(op,policy)for op in (b'\x1b[3L',b'\x1b[3M')for policy in(0,1)],(False,True),(0,1),(0,1)):
   if restricted and rows<5 or right and cols==80:continue
   m,address=fixture(profile,rows=rows,hidden=hidden);assert m.call('terminal_native_width',ax=1,limit=2000000)==0
   if cols==80:assert m.call('terminal_native_width',ax=0,limit=2000000)==0
   top,bottom=(1,rows-2)if restricted else(0,rows-1);row=(top+bottom)//2 if command in(b'\x1b[3L',b'\x1b[3M')else top if command==b'\x1bM'else bottom;col=cols-1 if right else 17 if cols>17 else 0
   m.put('screen_first_row',top);m.put('screen_last_row',bottom);m.position(row,col)
   size=rows*cols;flags=bytearray(size);values=bytearray(size);cells=[];carry=0x17
   markers={top*cols+3:0x1e,min(size-1,(top+1)*cols+4):0x2a}
   for i in range(size):
    if i in markers:flags[i]=0x80|(i&1);carry=markers[i]
    values[i]=carry;paint=(0x4e if flags[i]&1 else 0x27)if flags[i]&0x80 else carry
    cells.append((paint<<8)|(33+(i*7)%90))
   m.uc.mem_write(m.symbols['screen_attribute_cells'],bytes(flags)+b'\x55'*(4096-size));m.uc.mem_write(m.symbols['erase_attribute_values'],bytes(values)+b'\x66'*(4096-size))
   m.uc.mem_write(m.symbols['screen_line_flags'],bytes(128))
   # Repaint the current physical pane from the independently staged logical data.
   offset=m.get('screen_viewport_offset')if cols==132 else 0
   if cols==132:m.uc.mem_write(address,struct.pack('<'+str(size)+'H',*cells)+b'\x5a'*(8192-size*2))
   for y in range(rows):m.uc.mem_write(0xb8000+y*160,struct.pack('<80H',*cells[y*cols+offset:y*cols+offset+80]))
   for name,v in dict(screen_cursor_wrap=1,terminal_ansi_m_policy=policy,attributes_monochrome=0,screen_attribute_checks=protected,scroll_skip_attribute_scan=skip,attributes_normal_value=0xab27,attributes_current=0x9c,attributes_preset_value=0x4e,csi_erase_attribute=0x17).items():m.put(name,v)
   video=bytes(m.uc.mem_read(0xb8000,4000));shadow=bytes(m.uc.mem_read(address,8192));down=command==b'\x1bM';fill=values[(bottom+1)*cols-1]if command in(b'\n',b'wrap')else 0x17
   is_line=command in(b'\x1b[3L',b'\x1b[3M')
   if is_line:
    if protected:expected=cells[:];r=0
    else:expected,flags,values,r=line_reference(cells,flags,values,cols,rows,row,bottom,command.endswith(b'L'),3)
   else:expected,flags,values,r=reference(cells,flags,values,cols,rows,top,bottom,down,fill,skip)
   if command==b'wrap':m.call('screen_wrap_forward',limit=2000000)
   else:m.feed(command)
   identity=(rows,cols,profile,right,command,policy,restricted,protected,skip)
   actual=logical(m,address,rows)if cols==132 else bytes(m.uc.mem_read(0xb8000,size*2))
   assert actual==struct.pack('<'+str(size)+'H',*expected),(identity,'video')
   assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096))==bytes(flags)+b'\x55'*(4096-size),(identity,'flags')
   assert bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096))==bytes(values)+b'\x66'*(4096-size),(identity,'values')
   assert bytes(m.uc.mem_read(0xb8000+rows*160,4000-rows*160))==video[rows*160:]
   assert(m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(row,0 if command==b'wrap'or is_line and policy and not protected else col)
   assert m.get('screen_cursor_wrap')==1 and m.get('screen_attribute_checks')==protected
   if cols==132:assert bytes(m.uc.mem_read(address+size*2,8192-size*2))==shadow[size*2:]
   else:assert bytes(m.uc.mem_read(address,8192))==shadow
   cases+=1;repairs+=r
 counted=0;rejections=0;irq_cases=0
 for cols,right,count in itertools.product((80,132),(False,True),(0,1,3,32767,65535,65533,32768)):
  if cols==80 and right:continue
  rows=5;size=rows*cols;top=1;bottom=3;down=bool(count&0x8000)
  m,address=fixture(rows=rows);assert m.call('terminal_native_width',ax=1,limit=2000000)==0
  if cols==80:assert m.call('terminal_native_width',ax=0,limit=2000000)==0
  m.uc.mem_write(m.symbols['screen_line_flags'],bytes(128));m.position(0,cols-1 if right else 0)
  flags=bytearray(size);flags[cols+3]=0x80;flags[2*cols+4]=0x81;values=bytearray(size);cells=[];carry=0x17
  for i in range(size):
   if flags[i]&0x80:carry=0x1e if not flags[i]&1 else 0x2a
   values[i]=carry;cells.append((carry<<8)|(33+i%90))
  m.uc.mem_write(m.symbols['screen_attribute_cells'],bytes(flags)+b'\x55'*(4096-size));m.uc.mem_write(m.symbols['erase_attribute_values'],bytes(values)+b'\x66'*(4096-size))
  offset=m.get('screen_viewport_offset')if cols==132 else 0
  if cols==132:m.uc.mem_write(address,struct.pack('<'+str(size)+'H',*cells)+b'\x5a'*(8192-size*2))
  for y in range(rows):m.uc.mem_write(0xb8000+y*160,struct.pack('<80H',*cells[y*cols+offset:y*cols+offset+80]))
  for name,v in dict(screen_cursor_wrap=1,attributes_normal_value=0xab27,attributes_current=0x9c,attributes_preset_value=0x4e,csi_erase_attribute=0x17).items():m.put(name,v)
  fields=('screen_cursor_row','screen_cursor_column','screen_attribute_offset','screen_visible_column','screen_video_offset','erase_cell_count')
  saved=[m.get(n)for n in fields];expected=cells[:]
  if count:
   magnitude=65536-count if down else count
   for _ in range(min(magnitude,bottom-top+1)):expected,flags,values,_=reference(expected,flags,values,cols,rows,top,bottom,down,0x2a,False)
  else:expected[top*cols:(bottom+1)*cols]=[0x2a20]*((bottom-top+1)*cols)
  fired=[];payload=bytes(range(256))*2
  if not right and count in(1,65535):
   def interrupt(u,at,length,_):
    if fired or at!=m.symbols['scroll_region_repair']:return
    fired.append(True);assert m.get('screen_cursor_row') in(top,top+1)and not m.get('screen_cursor_column')
    assert m.get('erase_cell_count')==(bottom+1)*cols and u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==m.ds
    m.rx.extend(payload);sp=u.reg_read(UC_X86_REG_SP)-6
    u.mem_write(m.ds*16+sp,struct.pack('<3H',u.reg_read(UC_X86_REG_IP),u.reg_read(UC_X86_REG_CS),u.reg_read(UC_X86_REG_EFLAGS)&65535))
    u.reg_write(UC_X86_REG_SP,sp);u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)&~0x300)
    u.reg_write(UC_X86_REG_CS,m.code_segment);u.reg_write(UC_X86_REG_IP,m.symbols['uart_receive_interrupt']-m.code_base)
   m.uc.hook_add(UC_HOOK_CODE,interrupt)
  m.call('csi_service_2530',[0x2a,(bottom<<8)|(cols-1),top<<8,count],cleanup=8,limit=2000000)
  if not right and count in(1,65535):
   assert fired and not m.rx and m.get('uart_rx_count')==512
   assert bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],512))==payload
   irq_cases+=1
  for reg,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds)]:assert m.uc.reg_read(reg)==want
  assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&0x400

  actual=logical(m,address,rows)if cols==132 else bytes(m.uc.mem_read(0xb8000,size*2))
  assert actual==struct.pack('<'+str(size)+'H',*expected),(cols,right,count,'counted video')
  assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096))==bytes(flags)+b'\x55'*(4096-size)
  assert bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096))==bytes(values)+b'\x66'*(4096-size)
  assert[m.get(n)for n in fields]==saved
  counted+=1
 for cols,mutation in itertools.product((80,132),('values','flags','count','width','left','right','top','bottom')):
  m,address=fixture(rows=5);assert m.call('terminal_native_width',ax=1,limit=2000000)==0
  if cols==80:assert m.call('terminal_native_width',ax=0,limit=2000000)==0
  m.position(2,17);m.put('screen_cursor_wrap',1)
  args=[7,(3<<8)|(cols-1),1<<8,1]
  if mutation in ('values','flags','count','width'):
   name,value={'values':('erase_attribute_values_base',0),'flags':('screen_attributes_base',0),'count':('erase_cell_count',1),'width':('screen_attribute_row_bytes',79)}[mutation];m.put(name,value)
  else:
   at,value={'left':(2,(1<<8)|1),'right':(1,(3<<8)|(cols-2)),'top':(2,4<<8),'bottom':(1,(5<<8)|(cols-1))}[mutation];args[at]=value
  planes=[bytes(m.uc.mem_read(m.symbols[n],4096))for n in ('screen_attribute_cells','erase_attribute_values')];video=bytes(m.uc.mem_read(0xb8000,4000));shadow=bytes(m.uc.mem_read(address,8192))
  try:m.call('csi_service_2530',args,cleanup=8,limit=2000000)
  except Abort as error:assert error.args==(0x2d98,)
  else:raise AssertionError(('Missing scroll admission',cols,mutation))
  assert bytes(m.uc.mem_read(0xb8000,4000))==video and bytes(m.uc.mem_read(address,8192))==shadow
  for name,old in zip(('screen_attribute_cells','erase_attribute_values'),planes):assert bytes(m.uc.mem_read(m.symbols[name],4096))==old
  rejections+=1
 result=dict(passed=True,binary_sha256=sha(binary),cases=cases,repairs=repairs,counted_rectangles=counted,pre_mutation_rejections=rejections,transient_descriptor_IRQ_cases=irq_cases,sources=mft['sources'],checker_sha256=sha(Path(__file__)),scope=__doc__+' Bounded near planes, visible/hidden logical cells, inherited first-field repair, both widths, mode flags, margins and status canaries. Hardware modeled; no physical/BBS/full peer-width claim.')
 (binary.parent/'scroll-field-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS scroll fields:',cases,'cases,',repairs,'repairs,',counted,'counted rectangles,',rejections,'refusals,',irq_cases,'descriptor IRQ cases')
if __name__=='__main__':main()
