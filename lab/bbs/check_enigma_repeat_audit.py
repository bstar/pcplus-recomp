#!/usr/bin/env python3
"""Reject corrupted captures instead of letting repeated-transfer audit pass."""
import argparse,copy,hashlib,json
from pathlib import Path
from enigma_repeat_download_dos import ROOT,audit
from enigma_key_stream_fixture import owned


def main(candidate,label):
    assert label.replace('-','').replace('_','').isalnum()
    candidate=owned(candidate)
    out=ROOT/'build/bbs-lab/results/enigma'/label
    positive=json.loads((out/'repeat-checks.json').read_text());assert positive['passed']
    setup=json.loads((candidate.resolve()/'search-instance.json').read_text())
    archives=setup['archives'][1:3];names=[a['name'].upper() for a in archives]
    payloads={a['name'].upper():(candidate.resolve()/'file_base/pcplus_games'/a['name']).read_bytes() for a in archives}
    stream=(out/'display.bin').read_bytes();opposite=(out/'serial-received.bin').read_bytes();trace=json.loads((out/'trace.json').read_text())
    transactions=audit(stream,opposite,trace,names,payloads);cases=[]
    def reject(name,bbs=stream,dos=opposite,times=trace,expected=payloads):
        try:audit(bbs,dos,times,names,expected)
        except (AssertionError,ValueError,UnicodeError) as e:cases.append(dict(case=name,rejected=True,reason=str(e)))
        else:raise AssertionError('Corrupted capture passed: '+name)
    damaged=bytearray(stream);damaged[transactions[0]['protocol']['files'][0]['packets'][0]['offset']]^=1
    reject('CRC-corrupt-first-payload',bbs=bytes(damaged))
    damaged=bytearray(opposite);damaged[transactions[1]['skip']['offset']+4]^=1
    reject('CRC-corrupt-ZSKIP',dos=bytes(damaged))
    damaged=bytearray(opposite);damaged[transactions[1]['finish_reply']['offset']+4]^=1
    reject('CRC-corrupt-skip-ZFIN-reply',dos=bytes(damaged))
    damaged=bytearray(stream);damaged[transactions[1]['finish']['end']+1]=ord('X')
    reject('missing-skip-OO',bbs=bytes(damaged))
    damaged=bytearray(stream);at=damaged.find(b'NFO | lines',transactions[1]['finish']['end']+2);assert at>=0;damaged[at]=ord('X')
    reject('missing-post-skip-NFO-response',bbs=bytes(damaged))
    expected=dict(payloads);first=bytearray(expected[names[0]]);first[0]^=1;expected[names[0]]=bytes(first)
    reject('CRC-valid-wire-wrong-source-bytes',expected=expected)
    times=copy.deepcopy(trace);offset=transactions[1]['skip']['offset']
    entries=[e for e in times if e['direction']=='dos' and e['offset']<=offset<e['offset']+e['size']];assert len(entries)==1
    entries[0]['seconds']=0
    reject('ZSKIP-before-offer-chronology',times=times)
    report=dict(passed=True,cases=cases,checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        auditor_sha256=hashlib.sha256((ROOT/'lab/bbs/enigma_repeat_download_dos.py').read_bytes()).hexdigest(),
        shared_auditor_sha256=hashlib.sha256((ROOT/'lab/bbs/audit_zmodem.py').read_bytes()).hexdigest(),
        capture_hashes={p:hashlib.sha256((out/p).read_bytes()).hexdigest() for p in ('display.bin','serial-received.bin','trace.json')},
        scope='Replays the actual retained three-transfer capture, then changes one payload/control/finish/menu/source/chronology condition at a time. Every negative must reject; no network or DOS session is started.')
    (out/'audit-negative-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Repeated-transfer audit:',len(cases),'corruptions rejected')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True)
    a=p.parse_args();main(a.candidate,a.label)
