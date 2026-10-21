#!/usr/bin/env python3
"""Actual linked sender must emit Escape cancellation between complete frames."""
import hashlib,json
from pathlib import Path
from check_terminal_upload_live import LiveUpload,ROOT,BINARY
from check_terminal_transfer_live import DAY

class CancelDuringSecondFrame(LiveUpload):
 def __init__(self,at,crc=True,fault=None):
  self.cancel_at=at;self.injected=False
  self.physical_fault=fault;self.fault_at_tick=None;self.pending_seen=False
  super().__init__(bytes(range(256))*12,crc=crc)
  if fault=='cts':self.put('uart_hardware_flow',1)
 def output_port(self,u,port,size,value,data):
  wire=port==self.get('uart_port_thr') and not self.lcr&0x80
  super().output_port(u,port,size,value,data)
  if wire and not self.injected and self.accepted==1 and len(self.packet)==self.cancel_at:
   self.keys.append(0x011b);self.injected=True
  elif wire and self.injected and self.fault_at_tick is None and self.physical_fault and len(self.packet)==self.cancel_at+8:
   self.pending_seen=bool(self.get('terminal_upload_cancel_pending'))
   self.fault_at_tick=self.tick
   if self.physical_fault=='cts':self.cts=False
   elif self.physical_fault=='thre':self.thre=False
   elif self.physical_fault=='carrier':self.carrier=False
   elif self.physical_fault=='overflow':self.rx.extend(b'X'*4097)
   elif self.physical_fault=='deadline':self.tick=(self.tick+self.get('transfer_progress_budget')+2)%DAY;self.fault_at_tick=self.tick
   elif self.physical_fault=='altx':self.keys.append(0x2d00)

def main():
 cases=[]
 for crc in (True,False):
  packet_bytes=1029 if crc else 1028
  for at in (1,2,3,4,78,1025,packet_bytes-2,packet_bytes-1):
   model=CancelDuringSecondFrame(at,crc);error=None
   try:
    model.upload()
    checks=dict(Escape_injected_after_first_peer_ACK=model.injected,
     local_cancel_and_source_closed=model.get('terminal_transfer_fault')==2 and not model.handles,
     no_EOT=model.eots==0,native_CAN_pair=bytes(model.tx).endswith(b'\x18\x18'),
     complete_frame_before_CAN=not model.packet,
     no_extra_third_frame=len(model.frames)<=2,
     read_only_source=bytes(model.files['SEND.BIN'])==model.source,
     deferred_state_retired=model.get('terminal_upload_frame_active')==model.get('terminal_upload_cancel_pending')==0)
   except Exception as exc:error=repr(exc);checks={'native_case_completed':False}
   cases.append(dict(crc=crc,cancel_after_second_frame_bytes=at,passed=all(checks.values()),checks=checks,error=error,
    complete_frames=len(model.frames),incomplete_frame_bytes=len(model.packet),accepted_by_peer=model.accepted,wire_bytes=len(model.tx),wire_sha256=hashlib.sha256(bytes(model.tx)).hexdigest()))
 for initial in (0,0xfff0,DAY-20):
  for fault,want in [('cts',6),('thre',6),('carrier',4),('overflow',5),('deadline',3),('altx',2)]:
   model=CancelDuringSecondFrame(78,fault=fault);model.tick=initial;error=None
   try:
    model.upload()
    checks=dict(pending_Escape_existed_before_fault=model.injected and model.pending_seen,
     physical_fault_wins=model.get('terminal_transfer_fault')==want,
     bounded_abort=model.fault_at_tick is not None and (model.tick-model.fault_at_tick)%DAY<180,
     source_closed_no_EOT=not model.handles and not model.eots,
     read_only_source=bytes(model.files['SEND.BIN'])==model.source,
     deferred_state_retired=model.get('terminal_upload_frame_active')==model.get('terminal_upload_cancel_pending')==0)
   except Exception as exc:error=repr(exc);checks={'native_case_completed':False}
   cases.append(dict(fault=fault,initial_tick=initial,passed=all(checks.values()),checks=checks,error=error))
 for initial in (0,0xfff0,DAY-20):
  model=CancelDuringSecondFrame(78);model.tick=initial;model.upload()
  pending=model.get('uart_rx_count')+len(model.rx)
  # Retain actual UART/ring state and the second peer ACK across admission.
  # Only the independent peer/file fixture is changed for this new session.
  model.source=b'AFTER CANCEL';model.files['SEND.BIN']=bytearray(model.source)
  model.filename_sent=False;model.initial_offered=False;model.frames.clear()
  model.packet_size=0;model.accepted=0;model.peer_offset=0;model.eots=0;model.rejected=0
  model.tx.clear();model.fs_calls.clear();model.events.clear();model.keys.clear()
  model.upload()
  checks=dict(late_ACK_retained_before_next_session=pending==1,
   next_upload_success=not model.get('terminal_transfer_fault') and len(model.frames)==model.accepted==model.eots==1,
   no_stale_deferred_cancel=model.get('terminal_upload_frame_active')==model.get('terminal_upload_cancel_pending')==0,
   source_closed=not model.handles,late_ACK_consumed=not model.rx and not model.get('uart_rx_count'))
  cases.append(dict(next_session_initial_tick=initial,passed=all(checks.values()),checks=checks,error=None))
 result=dict(passed=all(c['passed'] for c in cases),binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=cases,
  inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),ROOT/'standalone/check_terminal_upload_live.py',ROOT/'standalone/check_terminal_transfer_live.py',ROOT/'src/terminal/upload_actions.asm',ROOT/'src/terminal/transfer_actions.asm']},
  scope='Actual source-built linked native sender/UI/read-only file owner/UARTISR, with modeled hardware/kernel and independent physical-byte peer. Escape after one peer-ACKed frame at second header/payload/checksum/CRC edges must leave only complete frames before CAN. No product callback is patched or skipped. Not real DOS/audio/physical proof.')
 out=ROOT/'build/terminal/terminal-upload-cancel-boundary.json';out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':result['passed'],'cases':len(cases),'failed':sum(not c['passed'] for c in cases),'output':str(out)}));assert result['passed']

if __name__=='__main__':main()
