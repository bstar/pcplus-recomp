#!/usr/bin/env python3
"""Live AltF10 -> real owner/decoders/native expansion -> selective application."""
import hashlib,json,struct
from unicorn.x86_const import UC_X86_REG_ES,UC_X86_REG_EFLAGS
from live_setup_kernel import LiveSettings
from check_setup_model import image
from check_directory_live import word,text
from check_program_actions_live import ROOT,BINARY
from check_terminal_reset_live import prepare,WORDS,BYTES,read,write
TRANSPORT=['terminal_port_number','terminal_baud_low','terminal_baud_high','terminal_parity','terminal_data_bits','terminal_stop_bits','uart_port_rbr','uart_irq_indices','terminal_irq_vector','uart_software_flow','uart_hardware_flow','csi_terminal_id','connection_state']
def snapshot(m):return {n:m.get(n) for n in TRANSPORT}
def launch(m,new=None):
 m.after_raw=new;m.keys.append(0x7100);m.poll();assert m.get('terminal_program_pending')
 m.safe();assert not m.get('terminal_program_pending') and not m.get('terminal_program_active')
def intact(m,before):
 assert snapshot(m)==before
 assert m.vector_value()==m.parent_vector and (m.lcr,m.mcr,m.ier,m.dll,m.dlm)==(3,0xb,1,3,0)
 assert not m.pic&0x10 and bytes(m.uc.mem_read(0xb8000,4000))==m.original_screen
 assert {n:m.get(n,1 if n.startswith('uart_saved_') else 2) for n in m.baseline}==m.baseline
 assert m.data_reads==0 and bytes(m.rx)==b'R'
def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 fields=[(0x1ae,30,'attributes_normal_value',30,32),(0x1b0,47,'attributes_bold_value',47,32),(0x1b2,53,'attributes_preset_value',53,32),(0x1b4,97,'attributes_reverse_value',97,32),(0x1b6,72,'attributes_underline_value',72,32),(0x19c,0,'render_autowrap',0,32),(0x19e,0,'scroll_enabled',0,32),(0x1e4,31,'terminal_macro_character_delay_units',31,64|128),(0xa,46,'terminal_modem_settings',46,128),(0x1a4,65535,'terminal_break_delay_units',65535,512)]
 for at,value,name,want,mask in fields:
  m=LiveSettings();before=snapshot(m);launch(m,word(m.raw,at,value))
  assert m.get('terminal_setup_apply_status')==0 and m.get(name)==want,(hex(at),name,m.get(name))
  assert struct.unpack('<4H',m.uc.mem_read(m.symbols['terminal_setup_outcome'],8))==(0,0,mask,0)
  assert b'Settings applied.' in m.local_text and [c for c in m.file_calls if c[0]=='open']==[('open',b'D:\\WORK\\TEST.PRM')]
  intact(m,before)
 done('configured-palette-wrap-scroll-pacing-modem-and-BREAK-adopted-after-child',len(fields))
 m=LiveSettings();before=snapshot(m);raw=bytearray(m.raw);raw[0x1e2]=ord('!');launch(m,bytes(raw))
 assert m.get('terminal_macro_pause_character',1)==ord('!') and m.get('terminal_modem_pause',1)==ord('!');intact(m,before)
 done('pause-character-adopted-by-both-key-mapping-and-prepared-modem',1)
 for at,value,mask in [(0,1,3),(2,8,2),(4,1,4),(0x198,1,8),(0x194,6,16)]:
  m=LiveSettings();before=snapshot(m);raw=word(word(m.raw,at,value),0x1a4,65535);launch(m,raw)
  assert m.get('terminal_setup_apply_status')==0 and m.get('terminal_break_delay_units')==65535
  assert struct.unpack('<4H',m.uc.mem_read(m.symbols['terminal_setup_outcome'],8))==(0,0,512,mask)
  assert b'link/profile changes need restart' in m.local_text;intact(m,before)
 done('mixed-saves-apply-independent-settings-and-defer-each-link-profile-category',5)
 for kind in ['open','read','close','short','invalid']:
  m=LiveSettings();before=snapshot(m);cfg=bytes(m.uc.mem_read(m.symbols['terminal_configuration_values'],40));modem=bytes(m.uc.mem_read(m.symbols['terminal_modem_settings'],368))
  if kind in ('open','read','close'):setattr(m,kind+'_error',5)
  raw=m.raw[:-1] if kind=='short' else word(m.raw,0x194,5) if kind=='invalid' else m.raw
  launch(m,raw)
  assert m.get('terminal_setup_apply_status')!=0 and b'Active settings unchanged' in m.local_text
  assert bytes(m.uc.mem_read(m.symbols['terminal_configuration_values'],40))==cfg and bytes(m.uc.mem_read(m.symbols['terminal_modem_settings'],368))==modem
  intact(m,before)
 done('file-open-read-close-truncation-and-decoder-failures-leave-active-settings-intact',5)
 m=LiveSettings();before=snapshot(m);m.keys.append(0x7100);m.poll();m.cwd=b'D:\\OTHER';m.safe()
 assert not m.children and m.get('terminal_program_status')==5 and m.get('terminal_setup_apply_status')==3
 assert b'could not run' in m.local_text
 # No child means the modeled hardware was not mutated and no RBR was added.
 assert snapshot(m)==before and m.vector_value()==m.parent_vector and not m.rx
 m=LiveSettings();before=snapshot(m);m.child_cwd=b'D:\\OTHER';launch(m,word(m.raw,0x1a4,65535))
 assert m.get('terminal_break_delay_units')==65535 and ('open',b'D:\\WORK\\TEST.PRM') in m.file_calls;intact(m,before)
 done('namespace-change-before-EXEC-denied-and-child-namespace-cannot-retarget-adoption',2)
 m=LiveSettings();before=snapshot(m);launch(m,text(m.raw,0x18,47,b'ATE0^M'))
 assert m.get('terminal_setup_apply_status')==0;intact(m,before)
 m.carrier=False;m.call('terminal_connection_start')
 for _ in range(400):
  m.poll(m.tick+1)
  if bytes(m.tx).startswith(b'ATE0\r'):break
 assert bytes(m.tx).startswith(b'ATE0\r'),'Future connection did not use newly prepared initialization'
 done('next-modem-action-uses-newly-expanded-command-through-real-sender-and-UART',1)
 for kind in ['responses','mixed-profile']:
  m=LiveSettings();m.put('connection_state',6);before=snapshot(m)
  new=text(m.raw,0xc4,16,b'ONLINE') if kind=='responses' else word(word(m.raw,0x194,6),0x1a4,65535)
  launch(m,new);intact(m,before)
  assert not m.tx,'Applying connected settings transmitted a modem command'
  if kind=='responses':assert bytes(m.uc.mem_read(m.symbols['modem_response_slots'],7))==b'ONLINE\0'
  else:assert m.get('terminal_setup_outcome',2)==0 and m.get('terminal_setup_outcome',8)>>48==16
  m.call('uart_receive_interrupt',irq=True);byte=m.call('uart_receive_byte');assert byte==ord('R')
  m.call('terminal_connection_receive',ax=byte)
  assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&1 and m.get('connection_state')==6
 done('established-modem-session-keeps-carrier-state-and-pending-input-with-no-command-transmission',2)
 # Independent renderer/RIS model, no child or file stubs: patch configured
 # reset defaults while retaining all transient peer state/keymap/tabs.
 t=prepare(4);old=image();from check_startup_import import terminal_expected
 write(t,'terminal_configuration_values',terminal_expected(old));t.put('terminal_option_mask',16);t.call('terminal_apply_configuration');t.call('terminal_reset_capture')
 reset_tabs=read(t,'terminal_tab_stops',30);reset_keys=read(t,'terminal_keymap',948)
 t.position(6,17);t.put('csi_origin_row',3);t.put('csi_origin_bottom',20);t.put('csi_origin_mode',1)
 t.put('attributes_current',0x2f);t.put('attributes_bold_active',1);t.put('render_autowrap',0)
 write(t,'terminal_tab_stops',b'\xaa'*30);write(t,'terminal_keymap',b'\xbb'*948)
 peer={n:t.get(n) for n in WORDS};peerbytes={n:read(t,n,1) for n in BYTES};video=t.cells()
 new=terminal_expected(word(old,0x1ae,30));ptr=t.stage_near(new);t.call('terminal_apply_live_configuration',ax=ptr)
 changed={'attributes_normal_value'}
 for n,value in peer.items():assert t.get(n)==(30 if n in changed else value),(n,t.get(n),value)
 assert {n:read(t,n,1) for n in BYTES}==peerbytes and t.cells()==video
 assert read(t,'terminal_tab_stops',30)==b'\xaa'*30 and read(t,'terminal_keymap',948)==b'\xbb'*948
 t.call('csi_reset_terminal',[1],limit=1500000)
 assert t.get('attributes_normal_value')==t.get('attributes_current')==t.get('cursor_state_saved_1f70')==30
 assert t.get('render_autowrap')==1 and t.get('attributes_bold_active')==0 and t.get('screen_cursor_row')==t.get('screen_cursor_column')==0
 assert read(t,'terminal_tab_stops',30)==reset_tabs and read(t,'terminal_keymap',948)==reset_keys
 assert read(t,'csi_erase_attribute',1)==b'\x1e'
 done('selective-RIS-default-update-does-not-capture-peer-SGR-cursor-modes-tabs-or-keymap',1)
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),inputs=sum(c['inputs'] for c in cases),cases=cases,scope='Actual linked AltF10, DOS process owner, C file read/canonicalization, candidate owner/decoders, native expansion, modem preparation and selective application. Only DOS kernel/BIOS/UART boundaries modeled. Independent renderer/RIS test executes the real reset and screen code. All serial/profile changes remain explicitly deferred; real DOS production editor tests are separate.')
 (ROOT/'build/terminal/live-setup-apply-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
