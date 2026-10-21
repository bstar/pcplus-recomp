#!/usr/bin/env python3
"""Probe post-XMODEM auto-script queuing; not a reproduction of live audio stall."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'standalone'))
from check_terminal_transfer_live import LiveTransfer
from synchronet_transfer import PAYLOAD
from audio_synchronet import sha

class Interrupted(LiveTransfer):
    def output_port(self,u,p,s,v,d):
        super().output_port(u,p,s,v,d)
        if self.peer_state==1 and self.block_index>=10:self.carrier=False;self.rx.clear()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    out=p.parse_args().output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    cases=[]
    for interrupted in (False,True):
        model=Interrupted if interrupted else LiveTransfer
        blocks=[PAYLOAD[i:i+1024] for i in range(0,11264,1024)]+[PAYLOAD[11264:11392],PAYLOAD[11392:11520],PAYLOAD[11520:]+b'\x1a'*127]
        m=model(data=blocks)
        m.uc.mem_write(0x449,b'\x03'+struct.pack('<H',80));m.uc.mem_write(0x462,b'\0');m.uc.mem_write(0x484,b'\x18')
        for init in ['_capture_file_initialize','_snapshot_file_initialize','_monitor_file_initialize','_capture_session_initialize','_printer_device_initialize','terminal_reset_capture']:assert m.call(init)==0
        m.receive()
        state={n:m.get(n) for n in ['terminal_transfer_fault','uart_rx_dropped','terminal_parser_active','terminal_ansi_wait_active','terminal_program_active','terminal_program_pending','_command_menu_active','_redisplay_active']}
        assert state['terminal_transfer_fault']==(4 if interrupted else 0)
        m.put('terminal_directory_context_valid',1);m.put('connection_state',6)
        m.uc.mem_write(m.symbols['terminal_directory_context'],struct.pack('<H',1))
        m.uc.mem_write(m.symbols['terminal_directory_context']+252+52,b'AUDIO\0')
        m.carrier=True;m.call('terminal_directory_script_connected')
        queued=m.get('terminal_program_pending')==1;assert queued
        cases.append(dict(interrupted=interrupted,state_before_connect=state,script_queued=queued))
    names=['lab/bbs/diagnose_reconnect_script_queue.py','standalone/check_terminal_transfer_live.py','standalone/check_program_actions_live.py','lab/bbs/synchronet_transfer.py']
    result=dict(source_queue_probe_passed=True,actual_live_failure_reproduced=False,cases=cases,
        terminal_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),inputs={n:sha(ROOT/n) for n in names},
        scope='Actual linked transfer owner/engine and script queue code with modeled UART/BIOS/DOS calls. One full download and one DCD drop after ten ACKs; both queue the directory script afterward. This does not run the second ASPECT child, real DOS, SIP or audio and does not establish the live stall cause or a fix.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
