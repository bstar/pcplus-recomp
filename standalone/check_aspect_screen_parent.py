#!/usr/bin/env python3
"""Actual cap27 parent bridge/RPC/native screen replay; DOS/BIOS/policy peers explicit."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE
import check_terminal_query_parent as query
from check_terminal_query_parent import Parent,ROOT,CHILD_PSP,CHILD_DS,CLIENT,CHILD_STOP,sha


class ScreenParent(Parent):
 operations=0
 def __init__(self,product):
  self.product=product;self.bios=[];self.trace=[];self.native_ds_windows=[]
  self.lifecycle=False;self.inject_abort=False;self.screen_writes=[]
  super().__init__(product,capability=27)
  self.phase='screen'
  retire=self.symbols['terminal_screen_retire'];body=bytes(self.uc.mem_read(retire,15))
  assert body[:3]==bytes.fromhex('2ec706') and body[7:10]==bytes.fromhex('2ec706') and body[-1]==0xc3
  self.stage=self.aspect_segment*16+struct.unpack_from('<H',body,3)[0]
  assert self.aspect_segment*16+struct.unpack_from('<H',body,10)[0]==self.stage+4
  self.initialize_screen()
 def initialize_screen(self):
  values=dict(screen_columns=80,ui_window_rows=25,screen_video_row_bytes=160,
   screen_attribute_row_bytes=80,text_video_segment=0xb800,text_cga_status_port=0,
   screen_use_bios_cursor=1,screen_viewport_enabled=0,screen_viewport_active=0,
   screen_viewport_left=0,screen_viewport_offset=0,screen_viewport_right=79,
   screen_visible_column=0,screen_video_offset=0,screen_previous_column=0,
   screen_attribute_offset=0,screen_cursor_column=0,screen_previous_row=0,screen_cursor_row=0,
   screen_attribute_checks=0,csi_last_row=23,csi_last_column=79,csi_origin_row=0,
   attributes_normal_value=7,attributes_current=0x70,terminal_parser_active=0,
   terminal_ansi_wait_active=0,terminal_aspect_active=0,erase_lineflags_enabled=0,screen_cursor_wrap=0)
  for name,value in values.items():self.put(name,value)
 def staged(self):return bytes(self.uc.mem_read(self.stage,14))
 def code(self,u,address,size,unused):
  if address==CHILD_PSP*16+CHILD_STOP:self.stopped=True;u.emu_stop();return
  if address==self.code_base+self.return_offset:return
  if address==self.symbols['_aspect_render_admit']:
   self.events.append(('pure-admission-model',u.reg_read(UC_X86_REG_BX)))
   u.reg_write(UC_X86_REG_BX,0xbad5);self.ret(self.admit_result);return
  if address==self.symbols['terminal_script_field']:
   assert self.phase=='setup' or self.lifecycle
   assert u.reg_read(UC_X86_REG_AX)==5 and u.reg_read(UC_X86_REG_BX)==1
   self.events.append(('field-retirement-model',0));self.ret(0,far=True);return
  if self.lifecycle and address in (self.symbols['_compiler_overlay_retire'],self.symbols['terminal_break_ui']):
   self.events.append(('revoke-external-retirement-model',address));self.ret(0,far=True);return
  if self.inject_abort and address==self.symbols['terminal_screen_reset_attribute']:
   self.inject_abort=False;u.reg_write(UC_X86_REG_AX,7)
   u.reg_write(UC_X86_REG_IP,self.symbols['terminal_render_typed_abort']-self.aspect_segment*16)
   self.events.append(('injected-platform-typed-abort',7));return
  banned={self.symbols[n]:n for n in ['resident_bridge_callback','terminal_receive_character_native',
   'terminal_render_read','terminal_render_read_now','terminal_render_unread','terminal_render_send',
   'terminal_render_poll','terminal_render_control','terminal_render_command','terminal_render_string',
   'terminal_render_set_modes','terminal_render_reset_modes','terminal_render_failure_notice']}
  assert address not in banned,('unexpected callback/parser/transport',banned.get(address))
  # Execute the actual ASPECT bank. All cross-bank entries are narrowly listed.
  bank=self.aspect_segment*16
  text=[('terminal_screen_resident_begin',23),('attributes_reset',7),
        ('screen_cursor_output',74),('screen_cursor_pack',17),('screen_set_cursor',168),
        ('erase_scroll_up',25),('terminal_clear_home',36),('terminal_control_home',25),
        ('text_write_char',47),('ui_read_byte',47),('csi_service_2530',64),('terminal_rectangle_native',695),
        ('attribute_screen_set_cursor_far',4)]
  allowed=bank<=address<bank+0x5000 or any(self.symbols[n]<=address<self.symbols[n]+length for n,length in text)
  allowed=allowed or self.symbols['_compiler_overlay_loaned']<=address<self.symbols['_compiler_overlay_loaned']+5
  assert allowed,('unexpected external instruction',hex(address))
  assert bytes(u.mem_read(address,1))[0] not in (0xe4,0xe5,0xe6,0xe7,0xec,0xed,0xee,0xef,0x6c,0x6d,0x6e,0x6f),('unexpected port IO',hex(address))
  if address==self.symbols['_aspect_render_client_admit']:self.events.append(('actual-client-auth',0))
  if address in [self.symbols[n] for n in ['terminal_screen_request','terminal_screen_retire','terminal_screen_scope_begin',
      'terminal_screen_scope_end','terminal_screen_scroll','terminal_screen_draw_box','terminal_screen_clear_home',
      'terminal_screen_set_cursor','terminal_screen_reset_attribute','terminal_screen_read_attribute',
      'terminal_screen_write_attribute','terminal_screen_home']]:
   self.trace.append(address)
  if self.phase!='setup' and u.reg_read(UC_X86_REG_EFLAGS)&0x200 and u.reg_read(UC_X86_REG_DS)!=u.reg_read(UC_X86_REG_SS):
   assert self.symbols['ui_read_byte']<=address<self.symbols['ui_read_byte']+47
   assert u.reg_read(UC_X86_REG_DS)==0xb800
   self.native_ds_windows.append(address)
 def interrupt(self,u,number,unused):
  ax=u.reg_read(UC_X86_REG_AX)
  if number==0x21:return super().interrupt(u,number,unused)
  assert number==0x10 and ax>>8 in (2,6),('unexpected BIOS',number,hex(ax))
  if ax>>8==2:
   self.bios.append(('cursor',u.reg_read(UC_X86_REG_DX)));u.mem_write(0x450,struct.pack('<H',u.reg_read(UC_X86_REG_DX)));return
  count,attr=ax&255,u.reg_read(UC_X86_REG_BX)>>8
  top,bottom=u.reg_read(UC_X86_REG_CX),u.reg_read(UC_X86_REG_DX)
  self.bios.append(('scroll',attr,bottom,top,count))
  t,l,b,r=top>>8,top&255,bottom>>8,bottom&255
  assert 0<=t<=b<25 and 0<=l<=r<80
  before=bytes(u.mem_read(0xb8000,4000));after=bytearray(before)
  for row in range(t,b+1):
   for col in range(l,r+1):
    at=row*160+col*2
    after[at:at+2]=before[(row+count)*160+col*2:(row+count)*160+col*2+2] if count and row+count<=b else bytes((32,attr))
  u.mem_write(0xb8000,bytes(after))
 def write(self,u,access,address,size,value,unused):
  if self.phase!='setup' and 0xb8000<=address<0xc8000:self.screen_writes.append((address,size,value))
 def request(self,*args,**kwargs):
  ScreenParent.operations+=1
  self.bios=[];self.trace=[];self.screen_writes=[]
  old=self.lifecycle
  if args and args[0]==2:self.lifecycle=True
  try:
   result=super().request(*args,**kwargs)
   if self.symbols['terminal_screen_request'] in self.trace:
    assert sum(event[0]=='actual-client-auth' for event in self.events)==1
   return result
  finally:self.lifecycle=old
 def transaction(self,primitive,args):
  assert self.request(33,primitive)==0
  for arg in args:assert self.request(34,arg)==0
  return self.request(35,0)
 def invoke_lifecycle(self,name):
  self.lifecycle=True
  u=self.uc;sp=self.offset('terminal_stack_top')-64
  u.mem_write(self.data_base+sp,struct.pack('<HH',self.return_offset,self.code_segment))
  for r,v in [(UC_X86_REG_CS,self.aspect_segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
  self.returned=False;u.emu_start(self.symbols[name],0,count=100000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4
  self.lifecycle=False


def handshake(child):
 """Real linked child descriptor/client validation, controlled ABSENT UART."""
 import check_aspect_render_client as fixture
 fixture.q.BINARY,fixture.q.MAP=child/'ASPECT.EXE',child/'ASPECT.map'
 text=fixture.q.MAP.read_text();code=re.search(r'^_TEXT\s+CODE\s+\S+\s+([0-9a-f]+):',text,re.M|re.I)
 stack=re.search(r'^STACK\s+STACK\s+DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',text,re.M|re.I)
 class Child(fixture.Client):
  def __init__(self):
   super().__init__();self.low=self.base+int(stack[1],16)*16+int(stack[2],16)-self.data_base;self.top=self.low+int(stack[3],16)
   self.put('__STACKLOW',self.low);self.put('__STACKTOP',self.top)
   self.option=self.low+2304;self.uc.mem_write(self.data_base+self.option,b'/S1:0003:03:N:6200:0100\0');self.backend=0
  def _code(self,u,address,size,unused):
   if hasattr(self,'stop') and address==self.stop:self.returned=True;u.emu_stop();return
   if address==self.symbols.get('_aspect_serial_backend_open'):
    self.backend+=1;sp=u.reg_read(UC_X86_REG_SP);ip=int.from_bytes(u.mem_read(self.data_base+sp,2),'little')
    u.reg_write(UC_X86_REG_AX,3);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ip);return
   super()._code(u,address,size,unused)
  def open(self):
   u=self.uc;segment=self.base_segment+int(code[1],16);self.stop=segment*16+0xfffe
   sp=self.top-68;u.mem_write(self.data_base+sp,struct.pack('<HH',0xfffe,self.option))
   for r,v in [(UC_X86_REG_CS,segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
   self.returned=False;u.emu_start(self.symbols['_aspect_serial_open'],0,count=250000)
   assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+2
   return u.reg_read(UC_X86_REG_AX)
 result=[]
 for version in (0,25,26,27,28,65535):
  m=Child();m.words[22]=version;m.publish();value=m.open()
  assert value==(3 if version==27 else 1) and m.backend==(version==27)
  assert not m.writes and not m.requests and not m.get('_aspect_serial_active')
  result.append(dict(version=version,result=value,reached_absent_backend=bool(m.backend)))
 return result


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--product',type=Path,required=True);p.add_argument('--child',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 product=a.product.resolve();child=a.child.resolve();manifest=json.loads((product/'manifest.json').read_text());cm=json.loads((child/'manifest.json').read_text())
 assert sha(product/'TERMINAL.EXE')==manifest['binary_sha256'] and sha(child/'ASPECT.EXE')==cm['binary_sha256']
 text=(product/'terminal.map').read_text();assert 'W1027' not in text
 ScreenParent._aspect_segment=0x1000+int(re.search(r'^([0-9a-f]{4}):[0-9a-f]{4}[*+ ]+\s+render_body\s*$',text,re.M|re.I)[1],16)
 sources=['standalone/check_aspect_screen_parent.py','standalone/check_terminal_query_parent.py','standalone/dos_image.py']
 relevant=['src/terminal/script_screen_rpc.asm','src/terminal/script_screen_platform.asm','src/terminal/aspect_renderer.asm','src/aspect/resident_bridge.asm','src/aspect/renderer_client.c']
 for n in relevant:assert sha(ROOT/n)==manifest['sources'][n],('stale product source',n)
 cases=[]
 def done(name):cases.append(dict(case=name,passed=True))
 m=ScreenParent(product)
 for value in query.WORDS:
  m.put('attributes_normal_value',value)
  assert m.request(33,0)==0 and m.request(34,0xbeef)==0;before=m.staged()
  for high in (0,1):assert m.request(32,high<<8)==0xf000|((value>>(8*high))&255) and m.staged()==before
  assert m.request(36,0)==0
 done('normal-metadata-WORDs-and-staged-argument-preservation')
 m.initialize_screen()
 for index,value in [(1,0),(2,25),(3,24),(4,79),(5,160)]:
  for high in (0,1):assert m.request(32,index|(high<<8))==0xf000|((value>>(8*high))&255)
 m.put('screen_attribute_row_bytes',132);assert m.request(32,1)==0xf001;m.put('screen_attribute_row_bytes',80)
 done('physical-and-wide-metadata')
 for parser,wait in [(0,0),(5,7)]:
  m.put('terminal_parser_active',parser);m.put('terminal_ansi_wait_active',wait)
  assert m.transaction(2,[0x1e])==0 and m.get('attributes_normal_value')==m.get('attributes_current')==0x1e
  assert m.get('terminal_parser_active')==parser and m.get('terminal_ansi_wait_active')==wait and m.get('terminal_aspect_active')==0
 done('actual-normal-attribute-and-captured-scope-restoration')
 m.initialize_screen();before=bytes(m.uc.mem_read(0xb8000,4000));m.put('csi_origin_row',2)
 assert m.transaction(3,[])==0 and m.bios==[('scroll',7,0x174f,0,0),('cursor',0x0200)]
 assert bytes(m.uc.mem_read(0xb8000,3840))==b' \x07'*1920 and bytes(m.uc.mem_read(0xb8000+3840,160))==before[3840:]
 done('actual-clear-home-rectangle-native-cursor-and-retained-status-row')
 assert m.transaction(4,[24,79])==0 and m.get('screen_cursor_row')==24 and m.get('screen_cursor_column')==79
 assert m.get('screen_video_offset')==3998 and m.get('screen_attribute_offset')==1999
 m.uc.mem_write(0xb8000+3998,b'Q\x11');assert m.transaction(6,[3999,0xa5])==0
 assert bytes(m.uc.mem_read(0xb8000+3998,2))==b'Q\xa5' and m.transaction(5,[3999])==0xf0a5
 assert m.native_ds_windows and m.transaction(7,[])==0 and m.get('screen_cursor_row')==m.get('screen_cursor_column')==0
 done('physical-status-row-cursor-get-put-and-actual-HOME')
 m.initialize_screen();before=bytes((i*37+11)&255 for i in range(4000));m.uc.mem_write(0xb8000,before)
 assert m.transaction(0,[0x47,0x070b,0x0203,0])==0 and m.transaction(1,[0x47,0x070b,0x0203])==0
 expected=bytearray(before);glyph=bytes.fromhex('c9cdbbbabccdc8ba')
 for row in range(2,8):
  for col in range(3,12):
   c=32
   if row in (2,7):c=glyph[1 if row==2 else 5]
   if col in (3,11):c=glyph[7 if col==3 else 3]
   if row==2 and col==3:c=glyph[0]
   if row==2 and col==11:c=glyph[2]
   if row==7 and col==11:c=glyph[4]
   if row==7 and col==3:c=glyph[6]
   expected[row*160+col*2:row*160+col*2+2]=bytes((c,0x47))
 assert bytes(m.uc.mem_read(0xb8000,4000))==expected
 done('actual-BOX-clear-and-native-double-border-pixels')
 before=bytes(m.uc.mem_read(0xb8000,4000))
 assert m.transaction(0,[0x47,0x184f,0x1700,0])==0 and m.transaction(1,[0x47,0x184f,0x1700])==0
 expected=bytearray(before)
 for row,characters in [(23,bytes([0xc9])+bytes([0xcd])*78+bytes([0xbb])),(24,bytes([0xc8])+bytes([0xcd])*78+bytes([0xbc]))]:
  for column,char in enumerate(characters):expected[row*160+column*2:row*160+column*2+2]=bytes((char,0x47))
 assert bytes(m.uc.mem_read(0xb8000,4000))==expected
 native_evidence=dict(frame_sha256=hashlib.sha256(expected).hexdigest(),
  raw_read_DS_video_instruction_sites=sorted(set(hex(at) for at in m.native_ds_windows)),
  raw_read_DS_video_instruction_count=len(m.native_ds_windows))
 done('native-BOX-physical-last-row-pixels')
 controls=['inactive-program','wrong-kind','wrong-PSP','wrong-DS','DS-ne-SS','bad-magic','bad-token','bad-version','callback-change','bad-MCB','MCB-owner','MCB-empty','descriptor-token','descriptor-version']
 for control in controls:
  m=ScreenParent(product);ds=ss=None
  if control=='inactive-program':m.put('terminal_program_active',0)
  elif control=='wrong-kind':m.put('terminal_program_kind',3)
  elif control=='wrong-PSP':m.current_psp=CHILD_PSP+1
  elif control=='wrong-DS':ds=ss=CHILD_DS+1
  elif control=='DS-ne-SS':ss=CHILD_DS+1
  elif control=='bad-magic':m.client_words[0]^=1;m.publish_client()
  elif control=='bad-token':m.client_words[2]^=1;m.publish_client()
  elif control=='bad-version':m.client_words[1]=26;m.publish_client()
  elif control=='callback-change':m.client_words[3]+=1;m.publish_client()
  elif control=='bad-MCB':m.uc.mem_write((CHILD_PSP-1)*16,b'Q')
  elif control=='MCB-owner':m.uc.mem_write((CHILD_PSP-1)*16+1,b'\x34\x12')
  elif control=='MCB-empty':m.uc.mem_write((CHILD_PSP-1)*16+3,b'\0\0')
  elif control=='descriptor-token':m.put('_script_render_token',m.get('_script_render_token')^1)
  elif control=='descriptor-version':m.put('_script_render_version',26)
  before=m.staged();status=m.request(33,0,ds=ds,ss=ss,flags=0x443 if control=='DS-ne-SS' else 0x643)
  assert status==(0xfffc if control=='DS-ne-SS' else 10) and m.staged()==before
  assert m.symbols['terminal_screen_request'] not in m.trace
  done('outer-auth-'+control)
 for kind in ('client-token','descriptor-version'):
  m=ScreenParent(product);assert m.request(33,0)==0 and m.request(34,7)==0;before=m.staged()
  if kind=='client-token':m.client_words[2]^=1;m.publish_client()
  else:m.put('_script_render_version',26)
  assert m.request(34,0xbeef)==10 and m.staged()==before and m.symbols['terminal_screen_request'] not in m.trace
  done('active-stage-auth-rejection-does-not-write-'+kind)
 owner_observations=[]
 for owner in ['render_program_owned','render_snapshot_owned','terminal_script_window_active','terminal_script_confirm_active','terminal_script_field_active']:
  m=ScreenParent(product);assert m.request(33,0)==0;m.put(owner,1)
  assert m.request(34,7)==10
  owner_observations.append(dict(owner=owner,stage_retained_before_cancel=m.staged()[:2]!=b'\0\0'))
  m.put(owner,0)
  # Early outer owner checks may reject before reaching the broker.
  assert m.request(36,0)==0 and m.staged()[:2]==b'\0\0';done('owner-refusal-and-cancel-'+owner)
 for status in (3,7,10,14):
  m=ScreenParent(product);assert m.request(33,0)==0;m.admit_result=status
  assert m.request(34,7)==status and m.staged()[:2]==b'\0\0';done('policy-refusal-retires-'+str(status))
 for operation in (2,29):
  m=ScreenParent(product);assert m.request(33,0)==0
  result=m.request(operation,0);assert result==0xe000 if operation==2 else result&0xff00==0xf000
  assert m.staged()[:2]==b'\0\0';done('competing-operation-retires-'+str(operation))
 m=ScreenParent(product);assert m.request(33,0)==0;m.invoke_lifecycle('terminal_render_revoke');assert m.staged()[:2]==b'\0\0';done('actual-revoke-prefix-retires')
 m=ScreenParent(product);assert m.request(33,0)==0;m.invoke_lifecycle('terminal_render_prepare');assert m.staged()[:2]==b'\0\0';done('new-prepare-retires')
 m=ScreenParent(product);assert m.transaction(2,[256])==7 and m.staged()[:2]==b'\0\0';done('typed-operand-failure-retires')
 m=ScreenParent(product);m.inject_abort=True
 assert m.transaction(2,[7])==7 and m.staged()[:2]==b'\0\0' and not m.get('terminal_aspect_active')
 done('actual-nonlocal-typed-abort-from-injected-platform-failure')
 m=ScreenParent(product);assert m.request(33,0)==0
 entry=m.symbols['_compiler_overlay_loaned'];body=bytes(m.uc.mem_read(entry,5));assert body[:2]==bytes.fromhex('2ea1') and body[-1]==0xcb
 segment=0x1000+int(re.search(r'^([0-9a-f]{4}):[0-9a-f]{4}[*+ ]+\s+_compiler_overlay_loaned\s*$',text,re.M|re.I)[1],16)
 active=segment*16+struct.unpack_from('<H',body,2)[0];m.uc.mem_write(active,b'\x01\0')
 assert m.request(34,7)==10 and m.symbols['terminal_screen_request'] not in m.trace
 compiler_stage_retained=m.staged()[:2]!=b'\0\0'
 m.uc.mem_write(active,b'\0\0');assert m.request(36,0)==0;done('actual-compiler-loan-refusal-and-cancel')
 m=ScreenParent(product);assert m.request(33,0)==0;m.uc.mem_write(m.symbols['_script_handoff']+22,b'\x01\0')
 assert m.request(34,7)==14 and m.staged()[:2]==b'\0\0';done('returned-UART-refusal-retires')
 child_cases=handshake(child)
 result=dict(passed=True,cases=cases,parent_operations=ScreenParent.operations,child_handshake=child_cases,
  native_platform_evidence=native_evidence,owner_refusal_stage_observations=owner_observations,
  compiler_loan_stage_retained_before_cancel=compiler_stage_retained,
  parent_sha256=sha(product/'TERMINAL.EXE'),parent_manifest_sha256=sha(product/'manifest.json'),
  child_sha256=sha(child/'ASPECT.EXE'),child_manifest_sha256=sha(child/'manifest.json'),original_inputs=[],
  sources={n:sha(ROOT/n) for n in sources+relevant},scope=__doc__,
  limitations=['Pure C renderer policy admission is modeled with deliberate BX clobber; actual current-PSP/client/descriptor/MCB authentication and broker owner gates execute.',
   'DOS62 PSP and BIOS02/06 screen operations are explicit models. Frame/read/write/reset/cursor/clear/HOME platform instructions are the actual linked product.',
   'Setup/revoke field retirement and compiler overlay retire/break notice are controlled external lifecycle boundaries; no live UART, child callback, parser output, actual DOS EXEC or physical hardware claim.',
   'Early outer PROGRAM-owner/compiler-loan refusals can retain an existing stage until cancel/END/revoke; broker-level typed failures retire. Bad outer authentication precludes broker/stage writes.',
   'Whole-parent mutation checks use mode3/page0/80x25 with direct video and attribute checking disabled;132-column viewport mutation and HOME attribute-boundary repair are not exercised here.',
   'Raw physical video-read primitive has a bounded native DS=video window before restoring DS; outer bridge restores all caller registers/FLAGS and DS=SS.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'linked screen parent cases;',len(child_cases),'child handshakes')


if __name__=='__main__':main()
