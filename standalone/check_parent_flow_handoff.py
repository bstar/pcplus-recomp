#!/usr/bin/env python3
"""Execute v6 parent staging and guarded completion; model child publication."""
import argparse,json,shutil,struct
from pathlib import Path
from check_script_launch_live import Script,ROOT,BINARY
sha=lambda p:__import__('hashlib').sha256(p.read_bytes()).hexdigest()


def prepare(soft,hard,paused,enabled=0,direct=0,seen=0):
    m=Script();m.install_program_name();m.child_status=0
    m.uc.mem_write(m.symbols['_command_menu_script'],b'TEST.ASX\0')
    m.put('uart_software_flow',soft);m.put('uart_hardware_flow',hard);m.put('uart_tx_paused',paused)
    m.put('connection_enabled',enabled,1);m.put('terminal_directory_mode',direct);m.put('connection_carrier_seen',seen,1)
    assert m.call('terminal_script_start')==0
    m.put('terminal_program_pending',0);m.put('terminal_program_active',1)
    result=m.call('terminal_script_prepare')
    return m,result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    rows=[]
    for hard in (0,1):
      for initial in (0,1):
       for returned in (0,1):
        m,result=prepare(1,hard,initial);assert result==0
        at=m.symbols['_script_handoff'];w=struct.unpack('<I23H',m.uc.mem_read(at,50))
        assert w[1:3]==(6,50) and w[23]==initial
        guard=w[3]^w[4]^w[5]^0xa510
        for i in [7,8,*range(11,24)]:guard^=w[i]
        assert w[9]==guard
        m.uc.mem_write(at+16,struct.pack('<2H',0,0));m.uc.mem_write(at+22,b'\x01\0');m.uc.mem_write(at+48,struct.pack('<H',returned))
        writes=len(m.port_writes);m.call('terminal_script_complete')
        assert m.get('terminal_program_status')!=5 and m.get('uart_tx_paused')==returned
        assert len(m.port_writes)==writes
        rows.append(dict(case='soft1-hard%d-in%d-out%d'%(hard,initial,returned),passed=True))
    for paused in (2,65535):
        m,result=prepare(1,0,paused);assert result==1 and not m.children
        rows.append(dict(case='reject-invalid-initial-pause'+str(paused),passed=True))
    for soft,returned in [(0,1),(1,2),(1,65535)]:
        m,result=prepare(soft,1,0);assert result==0;at=m.symbols['_script_handoff']
        m.uc.mem_write(at+16,struct.pack('<2H',0,0));m.uc.mem_write(at+22,b'\x01\0');m.uc.mem_write(at+48,struct.pack('<H',returned))
        m.call('terminal_script_complete');assert m.get('terminal_program_status')==5 and m.get('uart_tx_paused')==0
        rows.append(dict(case='reject-output-soft%d-flag%d'%(soft,returned),passed=True))
    manifest=json.loads((BINARY.parent/'manifest.json').read_text());assert sha(BINARY)==manifest['binary_sha256']
    inputs={**manifest['sources'],str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),
            'standalone/check_script_launch_live.py':sha(ROOT/'standalone/check_script_launch_live.py')}
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    result=dict(passed=True,cases=rows,parent_sha256=sha(BINARY),inputs=inputs,
                scope=__doc__+' Actual near/far DS=SS code and guard math execute. Valid0/1 output is adopted before parent UART restoration; original input participates in guard independently of changed output. Invalid output retains original pause. UART/DOS/child boundary modeled; actual child/peer timing requires separate tests.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
