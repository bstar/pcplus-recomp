#!/usr/bin/env python3
"""Check parser line edits and scrolling after a real explicit width transaction."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport
from check_reset_live import fixture,ROOT
from check_viewport_live import logical

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text())
 assert manifest['native_reset_transaction']and sha(binary)==manifest['binary_sha256']
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map'
 cases=0
 for rows,hidden in [(1,0),(5,0),(24,0),(25,1)]:
  for profile,col,command in itertools.product((4,6),(0,79,80,131),(b'\x1b[2L',b'\x1b[2M',b'\x1bD',b'\x1bM',b'\n')):
   m,address=fixture(profile,rows=rows,hidden=hidden)
   assert m.call('terminal_native_width',ax=1,limit=2000000)==0
   source=[0x700|((row*7+c)%90+33)for row in range(rows)for c in range(132)]
   backing=bytearray(b'\x5a'*8192);backing[:rows*264]=struct.pack('<'+str(rows*132)+'H',*source)
   m.uc.mem_write(address,bytes(backing))
   for row in range(rows):m.uc.mem_write(0xb8000+row*160,struct.pack('<80H',*source[row*132:row*132+80]))
   # Real margin parser and cursor/pane calls precede every operation.
   top,bottom=(1,rows-2)if rows>3 else(0,rows-1)
   m.feed(b'\x1b['+str(top+1).encode()+b';'+str(bottom+1).encode()+b'r')
   insert=command in (b'\x1b[2L',b'\x1bM')
   row=top if command==b'\x1bM'else bottom if command in(b'\x1bD',b'\n')else(top+bottom)//2
   m.position(row,col);before=bytes(m.uc.mem_read(0xb8000,4000));expected=source[:]
   first=row if command.endswith((b'L',b'[2M'))else top
   count=min(2,bottom-row+1)if command in(b'\x1b[2L',b'\x1b[2M')else 1
   for y in range(first,bottom+1):
    origin=y-count if insert else y+count
    expected[y*132:(y+1)*132]=source[origin*132:(origin+1)*132]if first<=origin<=bottom else[0x0720]*132
   m.feed(command)
   actual=logical(m,address,rows)
   assert actual==struct.pack('<'+str(rows*132)+'H',*expected),(rows,hidden,profile,col,command,'logical')
   assert(m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(row,col),(rows,col,command,'cursor')
   assert bytes(m.uc.mem_read(0xb8000+rows*160,4000-rows*160))==before[rows*160:]
   assert bytes(m.uc.mem_read(address+rows*264,8192-rows*264))==backing[rows*264:]
   cases+=1
 character_cases=0;refusals=0;narrow_cases=0
 for rows,hidden in [(1,0),(5,0),(24,0),(25,1)]:
  for profile,col,unit,insert,count in itertools.product((4,6),(0,51,52,79,80,130,131),(1,2),(False,True),(1,3,65535)):
   if unit==2 and col%2:continue
   m,address=fixture(profile,rows=rows,hidden=hidden);assert m.call('terminal_native_width',ax=1,limit=2000000)==0
   row=rows//2;source=[(((i*5)%0x70+7)<<8)|((i*7)%90+33)for i in range(rows*132)]
   backing=bytearray(b'\x5a'*8192);backing[:rows*264]=struct.pack('<'+str(rows*132)+'H',*source)
   m.uc.mem_write(address,bytes(backing))
   for y in range(rows):m.uc.mem_write(0xb8000+y*160,struct.pack('<80H',*source[y*132:y*132+80]))
   m.uc.mem_write(m.symbols['screen_line_flags'],bytes(128))
   if unit==2:m.uc.mem_write(m.symbols['screen_line_flags']+row,b'\x40')
   m.position(row,col);video=bytes(m.uc.mem_read(0xb8000,4000))
   planes=[bytes(m.uc.mem_read(m.symbols[name],4096))for name in ('screen_attribute_cells','erase_attribute_values')]
   start=row*132+col;end=(row+1)*132;n=min((1 if count>32767 else count)*unit,end-start)
   fill=(source[start]&0xff00 if insert else 0x0700)|32;expected=source[:]
   if insert:expected[start:end]=[fill]*n+source[start:end-n]
   else:expected[start:end]=source[start+n:end]+[fill]*n
   m.feed(b'\x1b['+str(count).encode()+(b'@'if insert else b'P'))
   assert logical(m,address,rows)==struct.pack('<'+str(rows*132)+'H',*expected),(rows,profile,col,unit,insert,count,'character')
   assert(m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(row,col)
   assert bytes(m.uc.mem_read(0xb8000+rows*160,4000-rows*160))==video[rows*160:]
   assert bytes(m.uc.mem_read(address+rows*264,8192-rows*264))==backing[rows*264:]
   for name,old in zip(('screen_attribute_cells','erase_attribute_values'),planes):assert bytes(m.uc.mem_read(m.symbols[name],4096))==old
   for reg,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds)]:assert m.uc.reg_read(reg)==want
   assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&0x400
   character_cases+=1
 # Returning to80 leaves the recovered active flag1, an ordinary coherent
 # width state. Its native character helpers must remain reachable.
 for insert in (False,True):
  m,address=fixture();assert m.call('terminal_native_width',ax=1,limit=2000000)==0
  assert m.call('terminal_native_width',ax=0,limit=2000000)==0
  m.position(5,17);old=bytes(m.uc.mem_read(0xb8000,4000));m.feed(b'ABCDEFGHIJKLMNOPQRSTUVWXYZ');m.position(5,17)
  old=list(struct.unpack('<2000H',m.uc.mem_read(0xb8000,4000)));expected=old[:];start=5*80+17;end=6*80
  if insert:expected[start:end]=[0x0720]*3+old[start:end-3]
  else:expected[start:end]=old[start+3:end]+[0x0720]*3
  m.feed(b'\x1b[3'+(b'@'if insert else b'P'))
  assert bytes(m.uc.mem_read(0xb8000,4000))==struct.pack('<2000H',*expected)
  narrow_cases+=1
 for field,value in [('_command_menu_active',1),('screen_attributes_base',0),('screen_attribute_offset',1),('screen_video_offset',1),('erase_shadow_segment',0),('screen_viewport_offset',1)]:
  for command in (b'@',b'P'):
   m,address=fixture();assert m.call('terminal_native_width',ax=1,limit=2000000)==0
   m.position(5,17);m.put(field,value);shadow=bytes(m.uc.mem_read(address,8192));video=bytes(m.uc.mem_read(0xb8000,4000))
   m.feed(b'\x1b[32767'+command)
   assert bytes(m.uc.mem_read(address,8192))==shadow and bytes(m.uc.mem_read(0xb8000,4000))==video,(field,command)
   assert m.get('ansi_parameters')==1
   refusals+=1
 irq_cases=0
 for insert,col in itertools.product((False,True),(51,80)):
  m,address=fixture(rows=25,hidden=1);assert m.call('terminal_native_width',ax=1,limit=2000000)==0
  m.uc.mem_write(m.symbols['screen_line_flags'],bytes(128));m.position(12,col);m.put('ansi_parameters',1)
  payload=bytes(range(256))*2;fired=[]
  target=m.symbols['character_wide_insert_copy'if insert else'character_wide_delete_copy']
  def interrupt(u,at,size,_):
   if fired or at!=target:return
   fired.append(True);assert u.reg_read(UC_X86_REG_DS)!=m.ds and u.reg_read(UC_X86_REG_SS)==m.ds
   assert bool(u.reg_read(UC_X86_REG_EFLAGS)&0x400)==insert
   m.rx.extend(payload);sp=u.reg_read(UC_X86_REG_SP)-6
   u.mem_write(m.ds*16+sp,struct.pack('<3H',u.reg_read(UC_X86_REG_IP),u.reg_read(UC_X86_REG_CS),u.reg_read(UC_X86_REG_EFLAGS)&65535))
   u.reg_write(UC_X86_REG_SP,sp);u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)&~0x300)
   u.reg_write(UC_X86_REG_CS,m.code_segment);u.reg_write(UC_X86_REG_IP,m.symbols['uart_receive_interrupt']-m.code_base)
  m.uc.hook_add(UC_HOOK_CODE,interrupt)
  m.call('csi_service_d270'if insert else'csi_service_d440',limit=2000000)
  assert fired and not m.rx and m.get('uart_rx_count')==512
  assert bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],512))==payload
  assert m.uc.reg_read(UC_X86_REG_DS)==m.uc.reg_read(UC_X86_REG_SS)==m.ds and not m.uc.reg_read(UC_X86_REG_EFLAGS)&0x400
  irq_cases+=1
 report=dict(passed=True,binary_sha256=sha(binary),cases=cases,character_cases=character_cases,narrow_return_cases=narrow_cases,character_refusals=refusals,foreign_DS_UART_cases=irq_cases,sources=manifest['sources'],checker_sha256=sha(Path(__file__)),
  scope=__doc__+' Plain profiles4/6, NETWORK IL/DL, IND/RI/LF at margins, both panes and status ownership. Hardware modeled; no protected fields, DOS/BBS or UI acceptance.')
 (binary.parent/'width-edit-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS width edits:',cases,'line/scroll,',character_cases,'characters,',narrow_cases,'narrow returns,',refusals,'character refusals,',irq_cases,'foreign-DS IRQ cases')
if __name__=='__main__':main()
