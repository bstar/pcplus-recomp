#!/usr/bin/env python3
"""Actual linked sender must emit Escape cancellation between complete frames."""
import hashlib,json
from check_terminal_upload_live import LiveUpload,ROOT,BINARY

class CancelDuringSecondFrame(LiveUpload):
 def __init__(self,at,crc=True):
  self.cancel_at=at;self.injected=False
  super().__init__(bytes(range(256))*12,crc=crc)
 def output_port(self,u,port,size,value,data):
  wire=port==self.get('uart_port_thr') and not self.lcr&0x80
  super().output_port(u,port,size,value,data)
  if wire and not self.injected and self.accepted==1 and len(self.packet)==self.cancel_at:
   self.keys.append(0x011b);self.injected=True

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
     read_only_source=bytes(model.files['SEND.BIN'])==model.source)
   except Exception as exc:error=repr(exc);checks={'native_case_completed':False}
   cases.append(dict(crc=crc,cancel_after_second_frame_bytes=at,passed=all(checks.values()),checks=checks,error=error,
    complete_frames=len(model.frames),incomplete_frame_bytes=len(model.packet),accepted_by_peer=model.accepted,wire_bytes=len(model.tx),wire_sha256=hashlib.sha256(bytes(model.tx)).hexdigest()))
 result=dict(passed=all(c['passed'] for c in cases),binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=cases,
  inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [__import__('pathlib').Path(__file__).resolve(),ROOT/'standalone/check_terminal_upload_live.py',ROOT/'standalone/check_terminal_transfer_live.py']},
  scope='Actual source-built linked native sender/UI/read-only file owner/UARTISR, with modeled hardware/kernel and independent physical-byte peer. Escape after one peer-ACKed frame at second header/payload/checksum/CRC edges must leave only complete frames before CAN. No product callback is patched or skipped. Not real DOS/audio/physical proof.')
 out=ROOT/'build/terminal/terminal-upload-cancel-boundary.json';out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':result['passed'],'cases':len(cases),'failed':sum(not c['passed'] for c in cases),'output':str(out)}));assert result['passed']

if __name__=='__main__':main()
