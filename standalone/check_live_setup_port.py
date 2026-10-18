#!/usr/bin/env python3
"""Real AltF10/EXEC/settings transaction and COM commit on independent UARTs."""
import hashlib,json,struct
from unicorn.x86_const import UC_X86_REG_AX
from check_port_handoff import Ports,BASES,IRQS,ROOT,BINARY
from check_directory_live import word
from check_modem_import import expected as modem_expected
from check_scroll import Scroll

class Moves(Ports):
 def cells(self):return list(struct.unpack('<2000H',self.uc.mem_read(0xb8000,4000)))
 def __init__(self):
  self.choice_count=0;self.inject_choice=None;self.inject_target=2;self.inject_kind='rx'
  super().__init__();self.prompt_key_sent=True
 def interrupt(self,u,number,data):
  if number==0x10 and u.reg_read(UC_X86_REG_AX)>>8 in (6,7):return Scroll.interrupt(self,u,number,data)
  choice=number==0x16 and u.reg_read(UC_X86_REG_AX)>>8 in (0,16) and self.get('terminal_program_active')
  result=super().interrupt(u,number,data)
  if choice:
   self.choice_count+=1
   if self.choice_count==self.inject_choice:
    if self.inject_kind=='rx':self.devices[BASES[self.inject_target-1]]['rx'].append(ord('R'))
    else:self.devices[BASES[self.inject_target-1]]['carrier']=True
  return result
 def launch(self,raw,answers=(ord('Y'),),ack=False):
  self.after_raw=raw;self.keys.extend([0x7100,*answers]+([13] if ack else []))
  self.poll();assert self.get('terminal_program_pending')
  for _ in range(6):
   self.safe()
   if not self.get('terminal_program_pending'):break
  assert not self.get('terminal_program_active') and not self.keys
 def outcome(self):return struct.unpack('<4H',self.uc.mem_read(self.symbols['terminal_setup_outcome'],8))
 def hardware_ready(self,port,rate=19200,line=3):
  dev=self.devices[BASES[port-1]]
  assert self.get('terminal_port_number')==port and self.get('uart_port_rbr')==BASES[port-1]
  assert self.get('terminal_irq_vector')==IRQS[port-1]+8 and self.vector_at(IRQS[port-1])==self.parent_vector
  assert (dev['dll']|(dev['dlm']<<8),dev['lcr'],dev['ier'],dev['mcr'])==(115200//rate,line,1,11)
  assert self.get('terminal_baud_low')==rate&65535 and self.get('terminal_baud_high')==rate>>16
  assert self.get('connection_state')==0 and self.get('terminal_setup_link_status')==1
  assert not self.pic&(1<<IRQS[port-1])

def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 count=0
 for source in range(1,5):
  for target in range(1,5):
   if source==target:continue
   m=Moves()
   if source!=1:m.launch(word(m.raw,0,source-1));m.hardware_ready(source,1200)
   old=m.get('uart_port_rbr');before=m.choice_count
   raw=word(word(m.raw,0,target-1),2,5);m.launch(raw);m.hardware_ready(target)
   assert m.choice_count==before+1 and b'Move to saved COM' in m.local_text
   assert m.hardware()[old]==m.originals[old] and m.outcome()==(0,0,3,0)
   assert bytes(m.uc.mem_read(0xb8000,4000))==m.original_screen
   m.devices[BASES[target-1]]['rx'].append(0xa5);m.call('uart_receive_interrupt',irq=True)
   assert m.call('uart_receive_byte')==0xa5
   m.enqueue(b'q');m.poll();assert m.wire==[(BASES[target-1],ord('q'))]
   m.shutdown();count+=1
 done('all-directed-port-pairs-through-real-foreground-owner-choice-commit-and-native-restoration',count)
 for choice in [ord('N'),27,32,13]:
  m=Moves();raw=word(word(word(word(m.raw,0,1),2,5),0x194,6),0x1ae,30)
  m.launch(raw,answers=(choice,));assert m.outcome()==(0,0,32,19)
  assert m.get('terminal_port_number')==1 and m.get('terminal_baud_low')==38400 and m.get('csi_terminal_id')==4
  assert m.get('terminal_setup_link_status')==2 and m.choice_count==1
  assert m.get('attributes_normal_value')==30
  m.shutdown()
 done('decline-keys-defer-whole-port-serial-profile-group-but-apply-independent-color',4)
 for problem in ['online','source-rbr','source-ring','target-rbr','target-carrier','missing-bios','parser']:
  m=Moves();raw=word(word(word(word(m.raw,0,1),2,5),0x194,6),0x1ae,30)
  if problem=='online':m.put('connection_state',6);m.carrier=True
  elif problem=='source-rbr':m.rx.append(ord('R'))
  elif problem=='source-ring':m.receive_irq(b'R')
  elif problem=='target-rbr':m.devices[BASES[1]]['rx'].append(ord('T'))
  elif problem=='target-carrier':m.devices[BASES[1]]['carrier']=True
  elif problem=='missing-bios':m.uc.mem_write(0x402,b'\0\0')
  else:m.put('terminal_parser_active',1)
  m.launch(raw,ack=True);assert m.outcome()==(0,0,32,19),problem
  assert m.get('terminal_port_number')==1 and m.get('terminal_baud_low')==38400 and m.get('csi_terminal_id')==4
  assert m.get('terminal_setup_link_status')==3 and b'COM not available' in m.local_text
  assert m.get('attributes_normal_value')==30 and m.choice_count==2
  if problem=='online':assert m.get('connection_state')==6 and not m.wire
  if problem=='source-rbr':assert bytes(m.rx)==b'R'
  if problem=='source-ring':assert m.get('uart_rx_count')==1
  if problem=='target-rbr':assert bytes(m.devices[BASES[1]]['rx'])==b'T'
  m.shutdown()
 done('busy-line-carrier-queued-input-missing-BIOS-and-parser-reject-move-with-independent-edits-intact',7)
 for profile_answer in [ord('Y'),ord('N')]:
  m=Moves();raw=word(word(word(m.raw,0,1),2,5),0x194,6)
  m.launch(raw,answers=(ord('Y'),profile_answer));m.hardware_ready(2)
  assert m.get('csi_terminal_id')==(6 if profile_answer==ord('Y') else 4)
  assert m.outcome()==(0,0,19 if profile_answer==ord('Y') else 3,0 if profile_answer==ord('Y') else 16)
  assert m.choice_count==2;m.shutdown()
 done('COM-confirmation-and-supported-profile-reset-have-independent-choices',2)
 m=Moves();m.inject_choice=2
 raw=word(word(word(word(word(m.raw,0,1),2,5),0x194,6),0x1ae,30),0xa,46)
 m.launch(raw,answers=(ord('Y'),ord('Y')),ack=True)
 assert m.outcome()==(0,0,32|128,19) and m.get('csi_terminal_id')==4 and m.get('terminal_baud_low')==38400
 assert m.get('terminal_setup_link_status')==3 and m.choice_count==3
 assert bytes(m.uc.mem_read(m.symbols['terminal_modem_settings'],368))==modem_expected(raw)
 assert m.get('attributes_normal_value')==30 and bytes(m.devices[BASES[1]]['rx'])==b'R'
 assert m.get('terminal_port_number')==1 and m.get('terminal_setup_profile_ready')==0
 done('byte-arriving-during-profile-question-cancels-port-and-profile-retains-color-and-modem-edits',1)
 m.devices[BASES[1]]['rx'].clear();m.launch(raw,answers=(ord('Y'),ord('Y')));m.hardware_ready(2)
 assert m.get('csi_terminal_id')==6;m.shutdown()
 done('failed-acquisition-can-retry-same-saved-port-profile-and-baud-without-restart',1)
 m=Moves();m.inject_choice=2;m.inject_kind='carrier'
 m.launch(word(word(word(m.raw,0,1),2,5),0x194,6),answers=(ord('Y'),ord('Y')),ack=True)
 assert m.outcome()==(0,0,0,19) and m.get('terminal_port_number')==1 and m.get('csi_terminal_id')==4
 m.shutdown();done('carrier-asserted-during-profile-question-rejects-at-commit-without-moving-port',1)
 m=Moves();m.put('terminal_option_mask',m.get('terminal_option_mask')|512);m.put('terminal_setup_keyboard_bound',0)
 m.launch(word(word(word(m.raw,0,1),2,5),0x194,6),ack=True);m.hardware_ready(2)
 assert m.outcome()==(0,0,3,16) and m.get('csi_terminal_id')==4 and m.get('terminal_setup_profile_status')==3
 assert b'Could not load profile keyboard' in m.local_text
 m.shutdown();done('unavailable-profile-keyboard-retains-profile-and-still-applies-confirmed-COM-move',1)
 for oldsoft in [0,1]:
  m=Moves();m.put('uart_software_flow',oldsoft);m.put('uart_tx_paused',1)
  raw=word(word(word(word(m.raw,0,1),2,5),0x198,1),0x19a,0);m.launch(raw);m.hardware_ready(2)
  assert m.get('uart_tx_paused')==0 and m.get('uart_flow_pending',1)==17
  assert m.wire==([(BASES[0],19),(BASES[0],17)] if oldsoft else [])
  m.enqueue(b'q');m.poll();m.poll()
  assert m.wire[-2:]==[(BASES[1],17),(BASES[1],ord('q'))]
  m.shutdown()
 done('old-pause-released-at-old-port-and-new-SOFT-port-announces-XON-before-payload',2)
 m=Moves();m.receive_irq(b'R'*129);m.put('uart_software_flow',1)
 raw=word(word(word(m.raw,0,1),2,5),0x198,1);m.launch(raw,ack=True)
 assert m.get('terminal_port_number')==1 and m.get('uart_rx_count')==129
 assert m.get('uart_flow_pending',1)==19 and m.get('uart_xoff_sent',1)==1
 assert m.wire==[(BASES[0],19),(BASES[0],17)]
 m.shutdown();done('rejected-COM-move-reestablishes-old-RX-watermark-pause-after-physical-XON',1)
 m=Moves();m.put('terminal_option_mask',m.get('terminal_option_mask')|1)
 m.launch(word(word(m.raw,0,1),2,5));m.hardware_ready(1)
 assert not m.get('terminal_setup_port_requested') and b'Apply current-port' in m.local_text
 m.shutdown();done('explicit-CLI-port-category-keeps-current-port-with-ordinary-baud-choice',1)
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),inputs=sum(c['inputs'] for c in cases),cases=cases,
  sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['standalone/check_live_setup_port.py','standalone/check_port_handoff.py','standalone/check_program_actions_live.py']},
  scope='Actual linked AltF10 scheduling, PROGRAM/EXEC return, C policy, COM/profile choices, repeat-at-commit preflight, serial/command rollback, target flow, native UART/ISR traffic and final all-port restoration. Four independent UARTs; only DOS/BIOS/hardware boundaries modeled. Actual DOS and physical modem tests are separate.')
 (ROOT/'build/terminal/live-setup-port-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
