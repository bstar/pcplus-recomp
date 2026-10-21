#!/usr/bin/env python3
"""Verifier negatives using immutable successful audio bytes and copied times."""
import argparse,hashlib,json
from pathlib import Path
from modem import Telnet
from audit_audio_download import frontend_trace
from audit_zmodem import audit_controls,scan
from test_transfer_dos import timestamp


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path)
    out=p.parse_args().cohort.resolve();r=json.loads((out/'download-audit.json').read_text());assert r['passed']
    sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
    base=json.loads((out/'independent-audit.json').read_text())
    trace,_=frontend_trace(out,sent,display,base['payloads']['expected_bridge_bytes']);protocol=r['protocol']
    end=timestamp(trace,'bbs',protocol['end']-1)
    post=next(e['seconds'] for e in trace if e['direction']=='dos' and e['seconds']>end and b'S\r' in sent[e['offset']:e['offset']+e['size']+1])
    actual=audit_controls(protocol,sent,trace,'bbs',post);rows=[]
    first=protocol['files'][0]['packets'][0]
    for name,kind,pos,before in [
        ('ACK-before-delivered-packet-CRC',3,first['position'],timestamp(trace,'bbs',first['crc_end']-1)-1),
        ('ZFIN-before-delivered-sender-ZFIN',8,0,timestamp(trace,'bbs',protocol['finish']['offset'])-1)]:
        header=next(h for h in scan(sent) if h['type']==kind and h['position']==pos)
        mutated=[dict(e) for e in trace]
        event=next(e for e in mutated if e['direction']=='dos' and e['offset']<=header['offset']<e['offset']+e['size'])
        event['seconds']=before
        try:audit_controls(protocol,sent,mutated,'bbs',post)
        except AssertionError as error:
            detail=str(error)
            assert ('No ACK or verified-position recovery' in detail if kind==3 else 'Missing opposite header' in detail),detail
            rows.append({'case':name,'rejected':True,'failure':detail})
        else:raise AssertionError(('Premature control accepted',name))
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    result={'passed':True,'baseline_control_records':len(actual),'negative_cases':rows,
        'checker_sha256':sha(Path(__file__)),'auditor_sha256':sha(Path(__file__).with_name('audit_audio_download.py')),
        'protocol_auditor_sha256':sha(Path(__file__).with_name('audit_zmodem.py')),
        'capture_sha256':{name:sha(out/name) for name in ['download-audit.json','independent-audit.json','bbs-input.bin','bbs-output.bin','serial-input-events.jsonl','serial-write-events.jsonl','serial-in.bin','serial-out.bin','node-result.json']},
        'scope':'Verifier test only. Original successful bytes/capture files are unchanged; only copied in-memory control-event times move before observed decoded-data delivery. Real baseline must pass and both premature replies must fail. No new product, BBS or hardware run.'}
    (out/'control-timing-verifier.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'actual_control_records':len(actual),'rejected_negative_cases':len(rows)}))


if __name__=='__main__':main()
