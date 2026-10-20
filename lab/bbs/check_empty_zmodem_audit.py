#!/usr/bin/env python3
"""An empty first data packet is not a replay; its real ACK remains required."""
import argparse,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'standalone'))
from check_zmodem import h,offer,payload
from audit_zmodem import audit_batch,audit_controls
from enigma_notes_dos import sha


def main(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    out=ROOT/'build/bbs-lab/empty-zmodem-audit'/args.label;out.mkdir(parents=True,exist_ok=False)
    bbs=bytearray();dos=bytearray();trace=[]
    def append(direction,data,time):
        target=bbs if direction=='bbs' else dos
        trace.append(dict(direction=direction,offset=len(target),size=len(data),seconds=time));target.extend(data)
    append('bbs',offer('EMPTY.BIN',0),1);append('dos',h(9),1.5)
    append('bbs',payload(b'',0),2);append('dos',h(3,0),3)
    append('bbs',h(11,0),4);append('dos',h(1,0x23002000),5)
    append('bbs',h(8),6);append('dos',h(8),7);append('bbs',b'OO',8)
    audit=audit_batch(bytes(bbs),{'EMPTY.BIN':b''});assert len(audit['files'])==1 and audit['files'][0]['length']==0
    audit_controls(audit,bytes(dos),trace,'bbs',9,False)
    assert not audit['files'][0]['packets'][0].get('replayed')
    cases=[dict(case='empty-first-data-with-real-ACK',passed=True)]
    broken=bytearray(dos);ack=next(e for e in trace if e['direction']=='dos' and e['seconds']==3);broken[ack['offset']+4]^=1
    try:audit_controls(audit,bytes(broken),trace,'bbs',9,False)
    except AssertionError:cases.append(dict(case='missing-empty-data-ACK-rejects',passed=True))
    else:raise AssertionError('Missing empty-data ACK accepted')
    report=dict(passed=True,cases=cases,checker_sha256=sha(Path(__file__)),auditor_sha256=sha(ROOT/'lab/bbs/audit_zmodem.py'),
        scope='Synthetic CRC-valid empty-file wire and explicit cross-direction times; no DOS, peer or physical transfer claim.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Empty-file audit: PASS')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);main(p.parse_args())
