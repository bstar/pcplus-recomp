#!/usr/bin/env python3
"""Execute staged captured-RIS row updates. No complete live geometry transaction.
The linked component changes captured defaults only; BIOS/UART inputs modeled.
"""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
import check_transport as transport
from check_recording_ui_live import UI
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ROWS=('screen_first_row','screen_last_row','csi_origin_row','csi_origin_bottom','screen_cursor_row','screen_previous_row','csi_saved_row')
CHANGES=set(ROWS)|{'csi_row_count','csi_last_row','erase_cell_count','screen_video_offset','screen_attribute_offset'}

class Defaults(UI):
 def captured(self):
  first=self.symbols['reset_word_addresses'];end=self.symbols['reset_word_addresses_end'];values=self.symbols['reset_words']
  result={}
  for i,at in enumerate(range(first,end,2)):
   offset=int.from_bytes(self.uc.mem_read(at,2),'little');assert offset not in result
   result[offset]=(values+2*i,int.from_bytes(self.uc.mem_read(values+2*i,2),'little'))
  return result
 def values(self):return {offset:value for offset,(_,value) in self.captured().items()}
 def set_baseline(self,name,value):
  at,_=self.captured()[self.offset(name)];self.uc.mem_write(at,struct.pack('<H',value))
 def value(self,name):return self.values()[self.offset(name)]
 def profile(self,rows=24,stride=80,cursor=0,custom=False):
  col,visible=(60,8) if stride==132 else (17,17)
  fields=dict(csi_row_count=rows,csi_last_row=rows-1,erase_cell_count=rows*stride,
    screen_attribute_row_bytes=stride,screen_last_column=stride-1,screen_columns=80,
    screen_video_row_bytes=160,screen_cursor_column=col,screen_visible_column=visible,
    screen_cursor_row=cursor,screen_previous_row=cursor,csi_saved_row=cursor,
    screen_first_row=2 if custom else 0,screen_last_row=rows-3 if custom else rows-1,
    csi_origin_row=1 if custom else 0,csi_origin_bottom=rows-2 if custom else rows-1,
    screen_video_offset=cursor*160+visible*2,screen_attribute_offset=cursor*stride+col)
  for name,value in fields.items():self.set_baseline(name,value)
 def resize(self,rows,flags=0x202,ss_delta=0):
  u=self.uc;manifest=json.loads((transport.BINARY.parent/'manifest.json').read_text())
  segment=self.base_segment+next(s['relative_segment'] for s in manifest['memory_layout']['code_segments'] if s['name']=='CONFIG_CODE')
  sp=self.offset('terminal_stack_top')-4;ss=self.ds+ss_delta
  keep={UC_X86_REG_BP:0xbabe,UC_X86_REG_BX:0x2345,UC_X86_REG_CX:0x3456,UC_X86_REG_DX:0x4567,UC_X86_REG_SI:0x5678,UC_X86_REG_DI:0x6789,UC_X86_REG_ES:0x1357}
  for reg,value in {**keep,UC_X86_REG_CS:segment,UC_X86_REG_DS:self.ds,UC_X86_REG_SS:ss,UC_X86_REG_SP:sp,UC_X86_REG_AX:rows,UC_X86_REG_EFLAGS:flags}.items():u.reg_write(reg,value)
  u.mem_write(ss*16+sp,struct.pack('<HH',self.return_offset,self.code_segment));u.mem_write(ss*16+sp-256,b'GUARD!')
  self.baseline_writes=[]
  first=self.symbols['reset_words'];last=first+self.symbols['reset_word_addresses_end']-self.symbols['reset_word_addresses']
  def write(uc,access,at,size,value,data):
   if first<=at and at+size<=last:self.baseline_writes.append((at,size,value))
   else:assert ss*16+sp-128<=at and at+size<=ss*16+sp+4,('unexpected write',hex(at),size)
  hook=u.hook_add(UC_HOOK_MEM_WRITE,write)
  self.returned=False
  try:u.emu_start(self.symbols['terminal_reset_resize_rows_far'],0,count=200000)
  finally:u.hook_del(hook)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4
  assert u.reg_read(UC_X86_REG_DS)==self.ds and u.reg_read(UC_X86_REG_SS)==ss
  assert u.reg_read(UC_X86_REG_EFLAGS)&0xffff==flags
  assert bytes(u.mem_read(ss*16+sp-256,6))==b'GUARD!'
  for reg,value in keep.items():assert u.reg_read(reg)==value,reg
  result=u.reg_read(UC_X86_REG_AX)
  if result:assert not self.baseline_writes,'Refusal wrote captured defaults'
  return result


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 transport.BINARY=a.terminal.resolve();transport.MAP=transport.BINARY.parent/'terminal.map'
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((transport.BINARY.parent/'manifest.json').read_text());assert manifest['experimental_reset_row_owner']
 cases=[];composed=0
 for old,new,stride,custom,flags in itertools.product((24,25,28),(1,24,25,28,43,50),(80,132),(False,True),(0x202,0x247,0x602)):
  m=Defaults();m.profile(old,stride,old-1,custom);before=m.values();video=bytes(m.uc.mem_read(0xb8000,4000))
  live={name:m.get(name) for name in CHANGES};result=m.resize(new,flags)
  if new*stride>4096:
   assert result==3 and m.values()==before
  else:
   assert result==0;expected=dict(before)
   expected[m.offset('csi_row_count')]=new;expected[m.offset('csi_last_row')]=new-1
   expected[m.offset('erase_cell_count')]=new*stride
   for field in ROWS:
    value=before[m.offset(field)]
    expected[m.offset(field)]=new-1 if field in ('screen_last_row','csi_origin_bottom') and value==old-1 else min(value,new-1)
   row=expected[m.offset('screen_cursor_row')]
   expected[m.offset('screen_video_offset')]=row*160+2*before[m.offset('screen_visible_column')]
   expected[m.offset('screen_attribute_offset')]=row*stride+before[m.offset('screen_cursor_column')]
   assert m.values()==expected,(old,new,stride,custom)
  assert {name:m.get(name) for name in CHANGES}==live and bytes(m.uc.mem_read(0xb8000,4000))==video and not m.tx
  composed+=1
 cases.append(dict(case='captured-only-rows-margins-cursors-offsets-and-capacity',inputs=composed,passed=True));print('PASS composed:',composed,flush=True)
 rejected=0
 for field,value in [('csi_row_count',0),('csi_row_count',51),('csi_last_row',99),('screen_columns',40),('screen_video_row_bytes',264),('screen_attribute_row_bytes',81),('screen_last_column',132),('erase_cell_count',0),('screen_cursor_column',80),('screen_visible_column',80),('screen_cursor_row',24),('screen_previous_row',24),('csi_saved_row',24),('screen_first_row',24),('csi_origin_row',24),('screen_video_offset',2),('screen_attribute_offset',1),('screen_first_row',23),('csi_origin_row',23)]:
  m=Defaults();m.profile()
  if field=='screen_first_row' and value==23:m.set_baseline('screen_last_row',10)
  if field=='csi_origin_row' and value==23:m.set_baseline('csi_origin_bottom',10)
  m.set_baseline(field,value);before=m.values();assert m.resize(25)==3 and m.values()==before,(field,value);rejected+=1
 for rows in (0,51,0x8000,0xffff):
  m=Defaults();before=m.values();assert m.resize(rows)==3 and m.values()==before;rejected+=1
 for ready in (0,2,0xffff):
  m=Defaults();m.put('reset_ready',ready);before=m.values();assert m.resize(25)==2 and m.values()==before;rejected+=1
 m=Defaults();before=m.values();assert m.resize(25,ss_delta=0x100)==3 and m.values()==before;rejected+=1
 m=Defaults();m.profile(50,132);before=m.values();assert m.resize(25)==3 and m.values()==before;rejected+=1
 # A late lookup failure must not commit the previously staged words.
 m=Defaults();at=m.symbols['reset_word_addresses'];end=m.symbols['reset_word_addresses_end']
 for pointer in range(at,end,2):
  if int.from_bytes(m.uc.mem_read(pointer,2),'little')==m.offset('csi_saved_row'):
   m.uc.mem_write(pointer,struct.pack('<H',0xffff));break
 else:raise AssertionError('field missing before corruption')
 values=bytes(m.uc.mem_read(m.symbols['reset_words'],end-at));assert m.resize(25)==3
 assert bytes(m.uc.mem_read(m.symbols['reset_words'],end-at))==values;rejected+=1
 cases.append(dict(case='invalid-request-baseline-ABI-and-late-failure-atomicity',inputs=rejected,passed=True));print('PASS transactional refusals:',rejected,flush=True)
 m=Defaults();original_tabs=bytes(m.uc.mem_read(m.symbols['terminal_tab_stops'],30));original_keys=bytes(m.uc.mem_read(m.symbols['terminal_keymap'],948))
 saved_color=m.get('attributes_current');saved_duplex=m.get('modes_value_1d1a')
 for new in (25,24,25):
  m.put('attributes_current',0x4e);m.put('modes_value_1d1a',1);m.uc.mem_write(m.symbols['terminal_tab_stops'],b'\0'*30);m.uc.mem_write(m.symbols['terminal_keymap'],b'\x55'*948)
  assert m.resize(new)==0
  # The eventual live transaction must set canonical visibility and geometry;
  # here only the subsequent real RIS consumption of its defaults is tested.
  m.put('ui_flow_suppressed',int(new==25));m.call('csi_reset_terminal',limit=1000000)
  assert m.get('csi_row_count')==new and m.get('csi_last_row')==m.get('screen_last_row')==m.get('csi_origin_bottom')==new-1
  assert m.get('erase_cell_count')==new*80 and m.get('screen_cursor_row')==0
  assert m.get('attributes_current')==saved_color and m.get('modes_value_1d1a')==saved_duplex
  assert bytes(m.uc.mem_read(m.symbols['terminal_tab_stops'],30))==original_tabs and bytes(m.uc.mem_read(m.symbols['terminal_keymap'],948))==original_keys
 cases.append(dict(case='real-RIS-uses-row-defaults-without-capturing-peer-state',inputs=3,passed=True));print('PASS actual linked RIS consumption',flush=True)
 for f,d in manifest['sources'].items():assert sha(ROOT/f)==d,f
 result=dict(passed=True,terminal_sha256=sha(transport.BINARY),manifest_sha256=sha(transport.BINARY.parent/'manifest.json'),cases=cases,sources_verified=len(manifest['sources']),sources={f:sha(ROOT/f) for f in ('src/terminal/reset_rows.asm','src/terminal/terminal_reset.asm','standalone/build_terminal.py','standalone/check_reset_rows_live.py')},scope=__doc__+' Actual far API, captured table and RIS instructions; staged failure atomicity, DS=SS, register/flag/stack guards. No live geometry commit, key/menu binding, BIOS resize, full frame/history/bridge-size transaction, DOS/BBS/package/physical acceptance or deployment.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
