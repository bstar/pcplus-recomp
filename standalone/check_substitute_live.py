#!/usr/bin/env python3
"""Recovered SUB branch priority and linked cursor/clear consumers.

Only BIOS/UART are modeled. The profile>=20 provider remains an explicit
unsupported boundary; its call argument is observed without supplying a body.
"""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport
from check_reset_live import fixture,Abort
from check_viewport_live import logical
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stage(profile,cols,right,rows,wrap,direct,up,down,row,col):
 m,address=fixture(profile=profile,rows=rows)
 if cols==132:assert m.call('terminal_native_width',ax=1,limit=3000000)==0
 for name,value in dict(screen_cursor_wrap=wrap,render_direct_output=direct,terminal_control_mode_9026=up,
  terminal_newline_mode_9020=down,attributes_current=7,attributes_monochrome=1,csi_origin_row=0).items():m.put(name,value)
 m.uc.mem_write(m.symbols['csi_erase_attribute'],b'\x07');m.uc.mem_write(m.symbols['screen_line_flags'],bytes(128))
 if cols==132:m.position(row,131 if right else 0)
 m.position(row,col)
 return m,address
def check(m,address,cols,rows,wrap,direct,up,down,row,col):
 video=bytes(m.uc.mem_read(0xb8000,4000));shadow=bytes(m.uc.mem_read(address,8192))
 fields=bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096));values=bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096))
 old_logical=logical(m,address,rows)if cols==132 else video[:rows*160]
 m.call('terminal_control_1248',limit=3000000)
 expected_row,expected_col=row,col
 if direct:
  expected_row=expected_col=0
  assert bytes(m.uc.mem_read(0xb8000,rows*160))==b' \x07'*(rows*80)
  if cols==132:assert logical(m,address,rows)==b' \x07'*(rows*132)
  assert bytes(m.uc.mem_read(0xb8000+rows*160,4000-rows*160))==video[rows*160:]
 elif up:expected_row=row-1 if row else rows-1 if wrap else 0
 elif down:expected_row=min(row+1,rows-1)
 if not direct:
  actual=logical(m,address,rows)if cols==132 else bytes(m.uc.mem_read(0xb8000,rows*160))
  assert actual==old_logical
  assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096))==fields
  assert bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096))==values
  if cols==80:assert bytes(m.uc.mem_read(address,8192))==shadow
 assert(m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(expected_row,expected_col)
 assert m.get('screen_attribute_offset')==expected_row*cols+expected_col
 assert m.get('screen_video_offset')==expected_row*160+m.get('screen_visible_column')*2
 for reg,value in[(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:assert m.uc.reg_read(reg)==value,(reg,value)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args();binary=a.terminal.resolve()
 mf=json.loads((binary.parent/'manifest.json').read_text());assert mf['native_reset_transaction']and sha(binary)==mf['binary_sha256']
 for name,digest in mf['sources'].items():assert sha(ROOT/name)==digest,name
 memory=inspect_terminal_memory(binary,binary.parent/'terminal.map');assert memory['substitute_native_bytes_verified']==53 and memory['substitute_native_dependencies_verified']==4
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map';cases=0
 for profile,(cols,right),rows,wrap,direct,up,down in itertools.product((4,6),((80,False),(132,False),(132,True)),(1,5),(0,1),(0,1),(0,1),(0,1)):
  # Both pane origins use their own left/right logical positions.
  left=52 if right else 0;right_col=cols-1 if right or cols==80 else 79
  for row,col in[(0,left),(0,right_col),(rows-1,left),(rows-1,right_col)]:
   m,address=stage(profile,cols,right,rows,wrap,direct,up,down,row,col)
   check(m,address,cols,rows,wrap,direct,up,down,row,col);cases+=1
 signed=0
 for profile,reject in[(19,False),(20,True),(32767,True),(32768,False),(65535,False)]:
  m,address=stage(6,80,False,5,0,0,0,0,2,17);m.put('csi_terminal_id',profile);observed=[]
  def argument(u,at,size,_):
   if at==m.symbols['terminal_substitute_profile_ge20']:
    sp=u.reg_read(UC_X86_REG_SP);ss=u.reg_read(UC_X86_REG_SS)
    observed.append(struct.unpack('<H',u.mem_read(ss*16+sp+2,2))[0])
  m.uc.hook_add(UC_HOOK_CODE,argument);video=bytes(m.uc.mem_read(0xb8000,4000))
  try:m.call('terminal_control_1248')
  except Abort as e:assert reject and e.args==(0xbb77,)
  else:assert not reject
  assert observed==([59]if reject else[])and bytes(m.uc.mem_read(0xb8000,4000))==video;signed+=1
 dispatch=0
 for profile,graphics in itertools.product((4,6),(0,1)):
  m,address=stage(profile,80,False,5,0,0,0,0,2,17)
  m.put('attributes_monochrome',graphics)
  m.call('terminal_receive_character',(26,),limit=3000000)
  assert(m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(2,17+graphics)
  if graphics:assert bytes(m.uc.mem_read(0xb8000+2*160+17*2,2))==b'\x1a\x07'
  else:assert m.get('csi_unimplemented_service')==0
  dispatch+=1
 irq=0;payload=bytes(range(256))*2
 for direct,up,down in[(0,0,0),(1,0,0),(0,1,0),(0,0,1)]:
  m,address=stage(6,132,True,5,1,direct,up,down,2,120);fired=[]
  def interrupt(u,at,size,_):
   if fired or at!=m.symbols['terminal_control_1248']:return
   fired.append(True);m.rx.extend(payload)
   sp=u.reg_read(UC_X86_REG_SP)-6;ss=u.reg_read(UC_X86_REG_SS);flags=u.reg_read(UC_X86_REG_EFLAGS)&65535
   assert ss==u.reg_read(UC_X86_REG_DS)==m.ds and flags&0x200
   u.mem_write(ss*16+sp,struct.pack('<3H',u.reg_read(UC_X86_REG_IP),u.reg_read(UC_X86_REG_CS),flags))
   u.reg_write(UC_X86_REG_SP,sp);u.reg_write(UC_X86_REG_EFLAGS,flags&~0x300);u.reg_write(UC_X86_REG_CS,m.code_segment);u.reg_write(UC_X86_REG_IP,m.symbols['uart_receive_interrupt']-m.code_base)
  m.uc.hook_add(UC_HOOK_CODE,interrupt);check(m,address,132,5,1,direct,up,down,2,120)
  assert fired and m.get('uart_rx_count')==512 and bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],512))==payload;irq+=1
 result=dict(passed=True,cases=cases,signed_profile_cases=signed,dispatcher_cases=dispatch,foreground_UART_IRQ_cases=irq,binary_sha256=sha(binary),sources=mf['sources'],checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__+' Both profiles,80/132 widths and both panes,1/5 rows, wrapping and all direct/up/down flag combinations. Native dependency bodies execute; model-only external profile>=20 boundary is explicit. Actual DOS and hardware acceptance remain separate.')
 (binary.parent/'substitute-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS SUB:',cases,'branch/geometry cases,',signed,'signed profile cases,',dispatch,'control-glyph dispatcher cases,',irq,'foreground IRQ')
if __name__=='__main__':main()
