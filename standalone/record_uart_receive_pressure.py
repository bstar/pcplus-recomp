#!/usr/bin/env python3
"""Seal linked receive-pressure coverage without claiming DOS or physical timing."""
import argparse,json,hashlib
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--normal',type=Path,required=True);p.add_argument('--mouse',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();products={};rows=[]
    for label,folder in [('terminal',a.normal),('terminal-mouse',a.mouse)]:
        r=read(folder/'checks.json');assert r['passed'] and len(r['cases'])==13
        assert r['parent_sha256']==sha(folder/'admitted.EXE')==sha(ROOT/'build'/label/'TERMINAL.EXE')
        for name,digest in r['inputs'].items():assert sha(ROOT/name)==sha(folder/'inputs'/name)==digest
        assert r['checker_sha256']==sha(ROOT/'standalone/check_uart_receive_pressure.py')
        cases=[];seen=set()
        for case in r['cases']:
            assert case['passed'];soft=case['soft'];hard=case['hard'];assert (soft,hard) in ((0,1),(1,0),(1,1))
            if case.get('case')=='peer-ignores-pause':
                assert case['offered']==5000 and case['retained']==4096 and case['dropped']==904
                alphabet=bytes(v for v in range(256) if not soft or v not in (17,19));payload=(alphabet*17)[:4096]
                assert case['retained_sha256']==hashlib.sha256(payload).hexdigest()
                seen.add(('overflow',soft,hard));cases.append(case);continue
            key=(soft,hard,case['in_flight_tail_bytes'],case['THRE_stall']);assert key not in seen;seen.add(key)
            assert case['bytes']==65536 and 3073<=case['peak_queued']<=4096 and case['pause_cycles']>=10
            alphabet=bytes(v for v in range(256) if not soft or v not in (17,19));payload=(alphabet*259)[:65536]
            assert case['sha256']==hashlib.sha256(payload).hexdigest()
            if soft:
                assert bytes.fromhex(case['flow_wire_hex'])==b'\x13\x11'*case['pause_cycles'] and case['MCR_write_count']==0 and case['MCR_transitions']==[]
            else:assert case['flow_wire_hex']=='' and case['MCR_transitions']==[9,11]*case['pause_cycles'] and case['MCR_write_count']>=2*case['pause_cycles']
            for event in case['watermark_events']:
                assert 0<=event['received']<=event['sent']<=65536
                if event['event'] in ('XOFF','RTS-low'):assert event['queued']>=3073
                else:assert event['event'] in ('XON','RTS-high') and event['queued']<=128
            cases.append(case)
        expected={('overflow',s,h) for s,h in ((0,1),(1,0),(1,1))}
        expected|={(s,h,tail,stall) for s,h in ((0,1),(1,0),(1,1)) for tail in (0,512) for stall in ((False,True) if s else (False,))}
        assert seen==expected
        products[label]=r['parent_sha256'];rows.append(dict(product=label,report=str(folder/'checks.json'),report_sha256=sha(folder/'checks.json'),cases=cases,inputs=r['inputs']))
    result=dict(passed=True,linked_receive_pressure_accepted=True,actual_DOS_pressure_accepted=False,physical_flow_timing_accepted=False,full_F03_accepted=False,products=products,cases=rows,pressure_cases=20,overflow_cases=6,exact_pressure_bytes=20*65536,auditor_sha256=sha(Path(__file__)),
        scope='Real linked RX IRQ, ring reads, deferred XON/XOFF and RTS with modeled hardware/reactive peer.20 exact65,536-byte streams across normal/mouse, including512-byte late peer tails and a three-step THRE stall on first software pause. BOTH exercises recovered receive-software precedence, with outbound CTS low. Six peers ignoring pause preserve4096 bytes and count904 drops. Not actual DOS foreground throughput, sustained application RX, physical UART/modem, software audio flow pressure or full modem acceptance. The initial normal cohort failed an incorrect one-MCR-write-per-pause expectation; corrected checks retain all transition/data/overflow assertions and account for repeated native RTS-low writes.')
    assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('passed','pressure_cases','overflow_cases','exact_pressure_bytes')}))


if __name__=='__main__':main()
