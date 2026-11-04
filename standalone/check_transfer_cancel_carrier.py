#!/usr/bin/env python3
"""Linked local-cancel/DCD-loss race at the real DOS file-close boundary.
Actual transfer/native UART/UI/storage instructions execute. Only hardware,
keyboard and DOS filesystem boundaries use the declared existing model.
"""
import argparse,hashlib,json
from pathlib import Path
import check_transport as transport
from check_terminal_transfer_live import LiveTransfer
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Race(LiveTransfer):
 def __init__(self,key,observed,drop):
  self.cancel_key=key;self.drop_at_close=drop;self.cancel_queued=False;self.close_boundary_seen=False
  super().__init__(data=bytes(range(128)))
  # Declared coherent25-row/visible-status fixture for the full-height UI.
  for n,v in {'csi_row_count':24,'csi_last_row':23,'screen_last_row':23,'csi_origin_bottom':23,'erase_cell_count':1920}.items():self.put(n,v)
  self.carrier=observed
 def output_port(self,u,port,size,value,data):
  super().output_port(u,port,size,value,data)
  if port==self.get('uart_port_thr') and value==6 and not self.cancel_queued:
   self.cancel_queued=True;self.keys.append(self.cancel_key)
 def interrupt(self,u,number,data):
  from unicorn.x86_const import UC_X86_REG_AX
  request=u.reg_read(UC_X86_REG_AX);result=super().interrupt(u,number,data)
  if number==0x21 and request>>8==0x3e and self.get('terminal_transfer_fault')==2:
   self.close_boundary_seen=True
   if self.drop_at_close:self.carrier=False
  return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);cases=[];images={}
 for label,path in [('baseline',a.baseline.resolve()),('candidate',a.terminal.resolve())]:
  mfest=json.loads((path.parent/'manifest.json').read_text());assert sha(path)==mfest['binary_sha256']
  if label=='baseline':assert sha(path)==json.loads((ROOT/'docs/validation/transfer-row-leases.json').read_text())['images']['ordinary']['sha256']
  else:
   for n,h in mfest['sources'].items():assert sha(ROOT/n)==h,n
  transport.BINARY=path;transport.MAP=path.parent/'terminal.map';images[label]=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),manifest_sha256=sha(path.parent/'manifest.json'))
  for key,name in [(0x011b,'Escape'),(0x2d00,'Alt-X')]:
   for observed,drop in [(True,False),(True,True),(False,True)]:
    m=Race(key,observed,drop);m.receive()
    should_suppress=label=='candidate' and observed and drop
    wanted=b'C\x06'+(b'' if should_suppress else b'\x18\x18')
    assert m.cancel_queued and m.close_boundary_seen and bytes(m.tx)==wanted,(label,name,observed,drop,bytes(m.tx).hex())
    assert m.get('terminal_transfer_fault')==2 and not m.files and not m.handles and m.storage()[0]==4
    assert not m.get('terminal_transfer_active') and not m.get('terminal_transfer_pending')
    assert bool(m.get('terminal_quit'))==(name=='Alt-X')
    cases.append(dict(image=label,key=name,initial_carrier_observed=observed,drop_during_close=drop,wire_hex=bytes(m.tx).hex(),first_fault=2,stage_and_handles_closed=True,late_cancel_suppressed=should_suppress,passed=True))
 for n,h in json.loads((a.terminal.parent/'manifest.json').read_text())['sources'].items():assert sha(ROOT/n)==h,n
 names=['standalone/check_transfer_cancel_carrier.py','standalone/check_terminal_transfer_live.py','standalone/check_program_actions_live.py','standalone/check_meta_actions_live.py','standalone/check_transport.py']
 report=dict(passed=True,cases=cases,inputs=len(cases),images=images,baseline_gap_observed=True,sources={n:sha(ROOT/n) for n in names},scope=__doc__+' Local cancel follows actual first block ACK, then DCD falls at file close. Baseline emits CAN in command mode; candidate preserves first failure and skips late output. High/untracked DCD policies retain CAN. Modeled timing/hardware, not physical or whole-protocol race acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS cancel/carrier race',len(cases),'baseline/candidate inputs')
if __name__=='__main__':main()
