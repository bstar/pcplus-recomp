#!/usr/bin/env python3
"""Actual protected erase/parser and independent logical field/repair reference."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SP,UC_X86_REG_EFLAGS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES
import check_transport
from check_reset_live import ROOT,fixture
from check_viewport_live import logical
from check_line_edit_live import Abort

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reference(cells,flags,values,cols,row,col,whole,protect):
 cells=list(cells);flags=bytearray(flags);values=bytearray(values);start=row*cols+col
 for i in range(start,len(cells)if whole else(row+1)*cols):
  if flags[i]&0x81:
   if whole:continue
   break
  cells[i]=(cells[i]&0xff00)|32
  if protect:flags[i]|=1
 carry=values[start-1]if start else values[0]if flags[0]&0x80 else 0x17
 for i in range(start,len(cells)):
  if flags[i]&0x80:carry=values[i]
  else:
   values[i]=carry
   paint=(carry&0xf8)|6 if flags[i]&1 and not flags[i]&2 else carry
   cells[i]=(paint<<8)|(cells[i]&255)
 return cells,flags,values

def stage(cols,rows,hidden,profile,right,col,pattern,protect):
 m,address=fixture(profile,0x27,rows=rows,hidden=hidden)
 if cols==132:assert m.call('terminal_native_width',ax=1,limit=3000000)==0
 n=rows*cols;row=rows//2
 cells=[((i%112+7)<<8)|((i*7)%90+33)for i in range(n)]
 flags=bytearray(n);values=bytearray((i*31+0x17)&255 for i in range(n))
 if pattern==1:flags[row*cols+col]=0x81
 if pattern==2:
  for i in range(n):flags[i]=0x80|(i&1)if i%37==0 else i%4
 flags[-1]|=0x80
 m.uc.mem_write(m.symbols['screen_attribute_cells'],bytes(flags)+b'\x55'*(4096-n));m.uc.mem_write(m.symbols['erase_attribute_values'],bytes(values)+b'\x66'*(4096-n))
 m.uc.mem_write(m.symbols['screen_line_flags'],bytes(128))
 backing=bytearray(b'\x5a'*8192)
 if cols==132:
  backing[:n*2]=struct.pack('<'+'H'*n,*cells);m.uc.mem_write(address,bytes(backing))
 for y in range(rows):m.uc.mem_write(0xb8000+y*160,struct.pack('<80H',*cells[y*cols:y*cols+80]))
 m.position(row,cols-1 if right else 0);m.position(row,col)
 for name,value in dict(screen_cursor_wrap=1,screen_attribute_checks=1,erase_protection_mode=protect,attributes_monochrome=0,attributes_current=0x9c,attributes_preset_value=0x4e).items():m.put(name,value)
 m.uc.mem_write(m.symbols['csi_erase_attribute'],b'\x17')
 return m,address,cells,flags,values,row

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args();binary=a.terminal.resolve();mf=json.loads((binary.parent/'manifest.json').read_text())
 assert sha(binary)==mf['binary_sha256']
 for name,digest in mf['sources'].items():assert sha(ROOT/name)==digest,name
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map';cases=0;parser_cases=0
 for (rows,hidden),(cols,right),profile,whole,protect,pattern in itertools.product([(1,0),(5,0),(24,0),(25,1)],[(80,False),(132,False),(132,True)],(4,6),(0,1),(0,1),range(3)):
  col=60 if pattern==0 else 17 if pattern==1 else cols-1
  m,address,cells,flags,values,row=stage(cols,rows,hidden,profile,right,col,pattern,protect);n=rows*cols
  oldvideo=bytes(m.uc.mem_read(0xb8000,4000));oldshadow=bytes(m.uc.mem_read(address,8192));cursor=[m.get(x)for x in ['screen_cursor_row','screen_cursor_column','screen_attribute_offset','screen_video_offset','screen_viewport_active','screen_viewport_offset','screen_visible_column']]
  expected,f,v=reference(cells,flags,values,cols,row,col,whole,protect)
  m.call('erase_complex_protected',[whole],limit=3000000)
  identity=(rows,cols,right,profile,whole,protect,pattern)
  actual=logical(m,address,rows)if cols==132 else bytes(m.uc.mem_read(0xb8000,n*2))
  assert actual==struct.pack('<'+'H'*n,*expected),(identity,'logical display')
  assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096))==bytes(f)+b'\x55'*(4096-n),(identity,'flags')
  assert bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096))==bytes(v)+b'\x66'*(4096-n),(identity,'values')
  assert bytes(m.uc.mem_read(0xb8000+rows*160,4000-rows*160))==oldvideo[rows*160:],(identity,'status/tail')
  assert bytes(m.uc.mem_read(address+n*2,8192-n*2))==oldshadow[n*2:]
  assert [m.get(x)for x in ['screen_cursor_row','screen_cursor_column','screen_attribute_offset','screen_video_offset','screen_viewport_active','screen_viewport_offset','screen_visible_column']]==cursor
  for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_ES,0xb800)]:assert m.uc.reg_read(reg)==value,(identity,'ABI',reg)
  cases+=1
 # Every ED/EL form through the real dispatcher, including EL2's temporary
 # column0 with the original selected right pane/cached actual cursor retained.
 for (cols,right),command,mode,protect,mono in itertools.product([(80,False),(132,False),(132,True)],('J','K'),range(3),(0,1),(0,1)):
  rows=5;col=60;m,address,cells,flags,values,row=stage(cols,rows,0,6,right,col,2,protect);n=rows*cols;cursor=[m.get(x)for x in ['screen_cursor_row','screen_cursor_column','screen_attribute_offset','screen_video_offset','screen_viewport_active','screen_viewport_offset','screen_visible_column']]
  m.put('attributes_monochrome',mono)
  expected=list(cells);f=bytearray(flags);v=bytearray(values)
  if mono and(mode==0 or(command=='K'and mode==2)):
   begin=row*cols+(0 if mode==2 else col);end=n if command=='J'else(row+1)*cols
   for i in range(begin,end):expected[i]=0x9c20;f[i]=protect;v[i]=0x9c
   if command=='J':expected,f,v=reference(expected,f,v,cols,row,col,True,False)
  elif mode==0 or(command=='K'and mode==2):expected,f,v=reference(cells,flags,values,cols,row,0 if mode==2 else col,command=='J',protect)
  else:
   begin=0 if command=='J'else row*cols;end=n if mode==2 else row*cols+col+1
   for i in range(begin,end):expected[i]=((0x9c if mono else 0x17 if mode==2 else 0x27)<<8)|32
   if mode==1:
    for i in range(begin,end):expected[i]=0x2720
  oldvideo=bytes(m.uc.mem_read(0xb8000,4000));oldshadow=bytes(m.uc.mem_read(address,8192))
  m.feed(b'\x1b['+str(mode).encode()+command.encode());actual=logical(m,address,rows)if cols==132 else bytes(m.uc.mem_read(0xb8000,n*2))
  assert actual==struct.pack('<'+'H'*n,*expected),(cols,right,command,mode,protect,'parser display')
  assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],n))==bytes(f)
  assert bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],n))==bytes(v)
  expected_cursor=[0,0,0,0,1 if cols==132 else cursor[4],0,0]if mono and command=='J'and mode==2 else cursor
  assert [m.get(x)for x in ['screen_cursor_row','screen_cursor_column','screen_attribute_offset','screen_video_offset','screen_viewport_active','screen_viewport_offset','screen_visible_column']]==expected_cursor
  assert bytes(m.uc.mem_read(0xb8000+rows*160,4000-rows*160))==oldvideo[rows*160:]
  assert bytes(m.uc.mem_read(address+n*2,8192-n*2))==oldshadow[n*2:]
  parser_cases+=1
 irq_cases=0;payload=bytes(range(256))*2
 for right,command in itertools.product((False,True),('J','K')):
  m,address,cells,flags,values,row=stage(132,5,0,6,right,60,2,1);fired=[]
  m.put('ansi_command',ord(command));m.put('ansi_parameter_count',1);m.put('ansi_parameters',2 if command=='K'else 0)
  def interrupt(u,at,size,_):
   if fired or at!=m.symbols['protected_erase_native']:return
   fired.append(True);m.rx.extend(payload)
   flagsword=u.reg_read(UC_X86_REG_EFLAGS)&65535;assert flagsword&0x200
   sp=u.reg_read(UC_X86_REG_SP)-6;ss=u.reg_read(UC_X86_REG_SS)
   u.mem_write(ss*16+sp,struct.pack('<3H',u.reg_read(UC_X86_REG_IP),u.reg_read(UC_X86_REG_CS),flagsword))
   u.reg_write(UC_X86_REG_SP,sp);u.reg_write(UC_X86_REG_EFLAGS,flagsword&~0x300)
   u.reg_write(UC_X86_REG_CS,m.code_segment);u.reg_write(UC_X86_REG_IP,m.symbols['uart_receive_interrupt']-m.code_base)
  m.uc.hook_add(UC_HOOK_CODE,interrupt)
  expected,f,v=reference(cells,flags,values,132,row,0 if command=='K'else 60,command=='J',True)
  m.call('ansi_dispatch_command',limit=3000000)
  assert fired and m.get('uart_rx_count')==512 and not m.rx
  assert bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],512))==payload
  assert logical(m,address,5)==struct.pack('<660H',*expected)
  assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],660))==f
  assert bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],660))==v
  assert m.get('screen_cursor_column')==60 and m.get('screen_attribute_offset')==row*132+60
  irq_cases+=1
 rejected=0
 for name,value in [('screen_cursor_row',25),('screen_cursor_column',132),('screen_attribute_offset',1),('screen_attributes_base',0xff00),('erase_attribute_values_base',0xff00),('erase_cell_count',1),('screen_cursor_wrap',0),('screen_attribute_checks',0)]:
  m,address,*_=stage(132,5,0,6,True,60,2,1);m.put(name,value)
  before=(bytes(m.uc.mem_read(0xb8000,4000)),bytes(m.uc.mem_read(address,8192)),bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096)),bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096)))
  try:m.call('erase_complex_protected',[1])
  except Abort as e:assert e.args==(0xd05f,)
  else:raise AssertionError(('missing refusal',name))
  after=(bytes(m.uc.mem_read(0xb8000,4000)),bytes(m.uc.mem_read(address,8192)),bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096)),bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096)))
  assert after==before,name
  rejected+=1
 r=dict(passed=True,cases=cases,parser_cases=parser_cases,real_UART_IRQ_cases=irq_cases,pre_mutation_rejections=rejected,binary_sha256=sha(binary),sources=mf['sources'],checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__+' Both widths/panes/profiles,1/5/24/25 rows, visible/hidden status, field stopping/skipping and marking, full logical bytes and canaries. BIOS/UART modeled; actual DOS/ASPECT and physical hardware require separate evidence.')
 (binary.parent/'protected-erase-checks.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS protected erase:',cases,'helpers,',parser_cases,'ED/EL parser cases,',rejected,'pre-mutation refusals')
if __name__=='__main__':main()
