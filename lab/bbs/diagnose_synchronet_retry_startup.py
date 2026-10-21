#!/usr/bin/env python3
"""Preserve failed retry facts and reproduce receiver-banner startup sensitivity."""
import argparse,json,sys
from pathlib import Path
from audio_synchronet import ROOT,sha
from audio_synchronet_retry import payload
from modem import Telnet
from audit_audio_download import frontend_trace
from test_transfer_dos import packet_at,timestamp

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 assert out.is_relative_to(ROOT/'build') and not (out/'startup-diagnosis.json').exists()
 r=json.loads((out/'result.json').read_text());assert not r['passed'] and r['route']=='xmodem-cancel-retry'
 assert sha(ROOT/'build/terminal/TERMINAL.EXE')==r['frozen_inputs']['build/terminal/TERMINAL.EXE']
 for n,h in r['frozen_inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in r['captures_sha256'].items():assert sha(out/n)==h,n
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 caller=(out/'caller-decoded.bin').read_bytes();assert caller[187:].startswith(display)
 tail=caller[187+len(display):]
 assert tail==b'\r\r\nConnection closed by remote host.\r\r\n\r\r\nCONNECT> '
 # Validate all frontend bytes, including the explicit remote-close bridge
 # suffix. This is diagnostic timing only; the strict application audit fails.
 trace,_=frontend_trace(out,sent,caller[187:],187)
 expected=payload();first=next(at for at in range(len(sent)) if (f:=packet_at(sent,at,True)) and f['number']==1 and f['payload']==expected[:1024])
 at=first;offset=0;frames=[]
 while (f:=packet_at(sent,at,True)):
  assert f['number']==len(frames)+1 and f['payload']==expected[offset:offset+f['size']]
  frames.append({k:v for k,v in f.items() if k!='payload'});offset+=f['size'];at=f['end']
 assert len(frames)==2 and offset==2048 and sent[at:at+2]==b'\x18\x18'
 assert sent[at+2:]==b' USXRUP001.BIN\rySynthetic PCPlus audio retry\r1n'
 assert 'TX timeout' in r['DOS_screen'] and b'SXRUP001.BIN IS ZERO LENGTH' in display
 last_n=timestamp(trace,'dos',len(sent)-1);ready=display.rindex(b'transfer now (Ctrl-X to abort):')
 ready_end=timestamp(trace,'bbs',ready+len(b'transfer now (Ctrl-X to abort):')-1)
 sys.path.insert(0,str(ROOT/'standalone'))
 from check_terminal_upload_live import LiveUpload
 class Startup(LiveUpload):
  def __init__(self,noise):self.startup_noise=noise;super().__init__(b'STARTUP BANNER')
  def interrupt(self,u,n,d):
   offered=self.initial_offered;super().interrupt(u,n,d)
   if not offered and self.initial_offered:
    assert self.rx[-1]==67;self.rx.pop();self.rx.extend(self.startup_noise+b'C')
 cases=[]
 for label,noise,success in [('quiet',b'',True),('short_noise',b'\r\n',True),('receiver_banner',b'\r\nStart XMODEM-1K/CRC transfer now (Ctrl-X to abort):\r\n',False)]:
  m=Startup(noise);m.upload();fault=m.get('terminal_transfer_fault')
  passed=(not fault and bool(m.frames)) if success else (fault==3 and not m.tx)
  cases.append(dict(label=label,passed=passed and not m.handles,fault=fault,physical_TX_bytes=len(m.tx),startup_noise_bytes=len(noise)))
 result=dict(passed=all(c['passed'] for c in cases),actual_retry_passed=False,complete_first_CRC_frames=len(frames),canceled_source_bytes=offset,second_data_bytes=0,
  final_n_seconds=last_n,complete_retry_banner_seconds=ready_end,n_to_complete_banner_seconds=ready_end-last_n,
  modeled_linked_cases=cases,terminal_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),bridge_close_suffix_hex=tail.hex(),
  inputs={n:sha(ROOT/n) for n in ('lab/bbs/diagnose_synchronet_retry_startup.py','lab/bbs/audio_synchronet_retry.py','lab/bbs/audit_audio_download.py','lab/bbs/test_transfer_dos.py','standalone/check_terminal_upload_live.py','standalone/check_terminal_transfer_live.py')},
  captures_sha256={n:sha(out/n) for n in ('result.json','bbs-input.bin','bbs-output.bin','serial-in.bin','serial-out.bin','caller-decoded.bin','serial-input-events.jsonl','serial-write-events.jsonl','SCREEN.BIN')},
  scope='Failed actual audio facts plus separate linked native sender reproduction. The keyboard recipe starts Alt-S three BIOS ticks after n, before waiting for the complete remote banner. Native startup accepts short noise but can exhaust its attempt count on receiver-banner text. Local key/application-consumption timestamps are not captured, so this does not prove the exclusive cause of this failure. A revised workflow must wait for the complete receiver-ready banner and pass a fresh actual run. No raw capture is modified or acceptance gate waived.')
 with (out/'startup-diagnosis.json').open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2));assert result['passed']

if __name__=='__main__':main()
