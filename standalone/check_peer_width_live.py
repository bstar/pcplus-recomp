#!/usr/bin/env python3
"""Normal peer mode3 parsing and controlled ASPECT transaction ownership.

Only BIOS/UART/kernel boundaries are modeled. Controlled owner bits test
admission; they do not establish a genuine ASPECT RPC/PSP lease.
"""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EFLAGS
import check_transport
from check_reset_live import fixture,near,inject

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def owners(m):
 for n,v in dict(terminal_program_active=1,terminal_program_kind=4,terminal_aspect_active=1,
  terminal_parser_active=1,render_attached=1,resident_bridge_busy=1,terminal_script_overlay_visible=0).items():m.put(n,v)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args();binary=a.terminal.resolve()
 root=Path(__file__).resolve().parents[1];mf=json.loads((binary.parent/'manifest.json').read_text());assert mf['native_reset_transaction']and sha(binary)==mf['binary_sha256']
 for name,digest in mf['sources'].items():assert sha(root/name)==digest,name
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map'
 parser=0
 for profile,rows,hidden in itertools.product((4,6),(1,5,24,25),(0,1)):
  m,shadow=fixture(profile=profile,rows=rows,hidden=hidden);target=24 if rows==25 and not hidden else rows
  for request in(1,0,1,0):
   m.feed(b'\x1b[?3'+(b'h'if request else b'l'))
   width=132 if request else 80
   assert(m.get('screen_attribute_row_bytes'),m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(width,0,0)
   assert(m.get('csi_row_count'),m.get('csi_column_count'),m.get('erase_cell_count'))==(target,width,target*width)
   assert bytes(m.uc.mem_read(0xb8000,target*160))==b' \x07'*(target*80)
   m.feed(b'\x1b[1;'+str(width-5).encode()+b'HREMOTE\x1b[6n');m.drain()
   assert b'\x1b[1;'+str(width).encode()+b'R'in bytes(m.tx)
   parser+=1
  # Non-private mode3 retains native ignore semantics.
  video=bytes(m.uc.mem_read(0xb8000,4000));m.feed(b'\x1b[3h')
  assert m.get('screen_attribute_row_bytes')==80 and bytes(m.uc.mem_read(0xb8000,4000))==video
 names=['terminal_program_active','terminal_program_kind','terminal_aspect_active','render_attached','resident_bridge_busy',
  'terminal_script_overlay_visible','_redisplay_active','_command_menu_active','_redisplay_live_ready']
 matrix=accepted=0;m,shadow=fixture()
 for active,kind in itertools.product((1,2),(0,4,5)):
  for bits in itertools.product((0,1),repeat=7):
   state=[active,kind,*bits]
   for name,value in zip(names,state):m.put(name,value)
   m.put('terminal_parser_active',1)
   before=near(m);video=bytes(m.uc.mem_read(0xb8000,4000));saved=bytes(m.uc.mem_read(m.symbols['program_screen'],4000))
   result=m.call('terminal_native_width',ax=1,limit=3000000)
   expected=state==[1,4,1,1,1,0,0,0,0]
   assert result==int(not expected),(state,result)
   assert bytes(m.uc.mem_read(m.symbols['program_screen'],4000))==saved
   if not expected:assert near(m)==before and bytes(m.uc.mem_read(0xb8000,4000))==video
   assert[m.get(n)for n in names]==state
   matrix+=1;accepted+=expected
 checks=0
 for name,value,width in [('terminal_parser_active',0,2),('terminal_parser_active',17,2),
  ('terminal_browser_screen_owned',1,1),('terminal_editor_screen_owned',1,1)]:
  m,_=fixture();owners(m);m.put(name,value,width);before=near(m)
  assert m.call('terminal_native_width',ax=1)==1 and near(m)==before;checks+=1
 # A valid renderer owner does not grant cold bank use or arbitrary live entry.
 for request in(0,1,0x100,0x101):
  m,_=fixture();owners(m);before=near(m);cache=m.base+mf['memory_layout']['native_reset_bank_start'];saved=bytes(m.uc.mem_read(cache,65504))
  assert m.call('reset_bank_call',ax=request)==1 and near(m)==before
  assert bytes(m.uc.mem_read(cache,65504))==saved;checks+=1
 irq_cases=rollbacks=0;payload=bytes(range(256))*2
 for request,fault in itertools.product((0,1),(False,True)):
  m,shadow=fixture();assert m.call('terminal_native_width',ax=1-request,limit=3000000)==0
  owners(m);program=bytes(m.uc.mem_read(m.symbols['program_screen'],4000));video=bytes(m.uc.mem_read(0xb8000,4000))
  old_width=m.get('screen_attribute_row_bytes');fired=inject(m,payload,'reset_live_prepare');corrupted=[]
  def corrupt(u,at,size,_):
   if not fault or corrupted or at!=m.symbols['reset_live_validate']:return
   corrupted.append(True);bank=m.base+mf['memory_layout']['native_reset_bank_start']
   u.mem_write(bank+m.symbols['nreset_screen_attribute_row_bytes']-m.base,struct.pack('<H',133))
  m.uc.hook_add(UC_HOOK_CODE,corrupt)
  result=m.call('terminal_native_width',ax=request,limit=3000000)
  assert result==(3 if fault else 0),(request,fault,result)
  assert fired and m.get('uart_rx_count')==512 and bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],512))==payload
  assert bytes(m.uc.mem_read(m.symbols['program_screen'],4000))==program
  if fault:
   assert corrupted and m.get('screen_attribute_row_bytes')==old_width and bytes(m.uc.mem_read(0xb8000,4000))==video;rollbacks+=1
  irq_cases+=1
 report=dict(passed=True,parser_commits=parser,ownership_cases=matrix,admitted_states=accepted,additional_refusals=checks,
  private_stack_IRQ_cases=irq_cases,ASPECT_rollbacks=rollbacks,binary_sha256=sha(binary),sources=mf['sources'],checker_sha256=sha(Path(__file__)),
  original_inputs=[],scope=__doc__+' Mode3 ABI/parser, row/status geometry, exact CPR, PROGRAM backup retention, cold-bank rejection and failure rollback. Actual DOS attachment and BBS/hardware acceptance are separate.')
 (binary.parent/'peer-width-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS peer width:',parser,'parser commits,',matrix,'ownership states,',irq_cases,'private-stack IRQ,',rollbacks,'ASPECT rollbacks')
if __name__=='__main__':main()
