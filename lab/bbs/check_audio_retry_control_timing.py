#!/usr/bin/env python3
"""Retry control-time negatives; keep the separate minimum-hold failure explicit."""
import argparse,hashlib,json
from pathlib import Path
from modem import Telnet
from audit_audio_download import frontend_trace
from audit_zmodem import audit_controls,scan
from test_transfer_dos import timestamp


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path)
    p.add_argument('--output',type=Path,help='Fresh result path inside the cohort; existing evidence is never overwritten.')
    p.add_argument('--protocol-only',action='store_true',help='Test a validated protocol even when a separate transfer acceptance gate failed; grants no transfer acceptance.')
    a=p.parse_args();out=a.cohort.resolve()
    result_path=a.output.resolve() if a.output else out/'retry-control-timing-verifier.json'
    assert result_path.is_relative_to(out) and not result_path.exists()
    route=json.loads((out/'result.json').read_text())['route'];assert route in ('download','upload')
    assert route=='upload'
    receipt='upload-retry-audit-v2.json'
    sender='dos' if route=='upload' else 'bbs';other='bbs' if sender=='dos' else 'dos'
    r=json.loads((out/receipt).read_text())
    assert a.protocol_only and not r['passed'] and r['checks']['complete_retry_CRC_controls_FIN_OO']
    assert {k for k,v in r['checks'].items() if not v}=={'whole_stream_and_cleanup'}
    sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
    base=json.loads((out/'independent-audit.json').read_text())
    trace,_=frontend_trace(out,sent,display,base['payloads']['expected_bridge_bytes']);protocol=r['retry_protocol']
    opposite=display if route=='upload' else sent
    end=timestamp(trace,sender,protocol['end']-1)
    post=next(e['seconds'] for e in trace if e['direction']=='dos' and e['seconds']>end and b'S\r' in sent[e['offset']:e['offset']+e['size']+1])
    actual=audit_controls(protocol,opposite,trace,sender,post);rows=[]
    first=protocol['files'][0]['packets'][0]
    for name,kind,pos,before in [
        ('ACK-before-delivered-packet-CRC',3,first['position'],timestamp(trace,sender,first['crc_end']-1)-1),
        ('ZFIN-before-delivered-sender-ZFIN',8,0,timestamp(trace,sender,protocol['finish']['offset'])-1)]:
        # Move every matching valid control, including duplicate replies. A
        # later untouched duplicate must not make the negative case pass.
        headers=[h for h in scan(opposite) if h['type']==kind and h['position']==pos]
        assert headers
        mutated=[dict(e) for e in trace]
        changed=0
        for event in mutated:
            if event['direction']==other and any(event['offset']<h['end'] and h['offset']<event['offset']+event['size'] for h in headers):
                event['seconds']=before;changed+=1
        assert changed
        try:audit_controls(protocol,opposite,mutated,sender,post)
        except AssertionError as error:
            detail=str(error)
            assert ('No ACK or verified-position recovery' in detail if kind==3 else 'Missing opposite header' in detail),detail
            rows.append({'case':name,'rejected':True,'failure':detail,'controls_moved':len(headers),'trace_chunks_moved':changed})
        else:raise AssertionError(('Premature control accepted',name))
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    result={'passed':True,'route':route,'sender':sender,'protocol_only':a.protocol_only,
        'input_transfer_audit_passed':r['passed'],'baseline_control_records':len(actual),'negative_cases':rows,
        'checker_sha256':sha(Path(__file__)),'auditor_sha256':sha(Path(__file__).with_name('audit_audio_download.py')),
        'protocol_auditor_sha256':sha(Path(__file__).with_name('audit_zmodem.py')),
        'capture_sha256':{name:sha(out/name) for name in [receipt,'independent-audit.json','bbs-input.bin','bbs-output.bin','serial-input-events.jsonl','serial-write-events.jsonl','serial-in.bin','serial-out.bin','node-result.json']},
        'scope':'Retry verifier only; overall minimum-hold failure remains unaccepted. Original successful bytes/capture files are unchanged; only copied in-memory control-event times move before observed decoded-data delivery. Real baseline must pass and both premature replies must fail. No new product, BBS or hardware run.'}
    with result_path.open('x') as output:output.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'actual_control_records':len(actual),'rejected_negative_cases':len(rows)}))


if __name__=='__main__':main()
