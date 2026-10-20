#!/usr/bin/env python3
"""Replay real cancellation/retry evidence and reject single-condition damage."""
import argparse,copy,json
from pathlib import Path
from audit_zmodem import scan,packet,audit_batch,audit_controls
from test_transfer_dos import timestamp,offset_after
from enigma_key_stream_fixture import ROOT,owned
from enigma_notes_dos import sha


def replay(stream,opposite,trace,name,payload):
    cancel=opposite.index(b'\x18'*8+b'\x08'*10)
    cancel_time=timestamp(trace,'dos',cancel)
    headers=list(scan(stream));first=next(h for h in headers if h['type']==10 and timestamp(trace,'bbs',h['offset'])<cancel_time)
    data=packet(stream,first['end'],first['format'])['payload']
    assert data and data==payload[:len(data)]
    assert not any(h['type']==11 and timestamp(trace,'bbs',h['offset'])<cancel_time for h in headers)
    post=opposite.index(b'n',cancel+18);tail=offset_after(trace,'bbs',timestamp(trace,'dos',post));assert tail is not None
    retry=audit_batch(stream,{name:payload},tail)
    assert b'NFO | lines 1-15/24' in stream[tail:retry['start']]
    next_post=opposite.index(b'n',offset_after(trace,'dos',timestamp(trace,'bbs',retry['end']-1)))
    when=timestamp(trace,'dos',next_post)
    controls=audit_controls(retry,opposite,trace,'bbs',when,False)
    after=offset_after(trace,'bbs',when);assert after is not None
    assert b'NFO | lines 1-15/24' in stream[after:] and b'PCPLUS NFO LINE 01 : synthetic game 01' in stream[after:]
    return retry,controls,first,tail,after


def main(args):
    assert args.label.replace('-','').replace('_','').isalnum()
    candidate=owned(args.candidate);out=ROOT/'build/bbs-lab/results/enigma'/args.label
    positive=json.loads((out/'cancel-checks.json').read_text());assert positive['passed'] and all(positive['checks'].values())
    fixture=json.loads((candidate/'search-instance.json').read_text());archive=fixture['archives'][1]
    source=candidate/'file_base/pcplus_games'/archive['name'];assert sha(source)==archive['sha256']
    payload=source.read_bytes();name=archive['name'].upper()
    stream=(out/'display.bin').read_bytes();opposite=(out/'serial-received.bin').read_bytes();trace=json.loads((out/'trace.json').read_text())
    retry,controls,first,tail,after=replay(stream,opposite,trace,name,payload);cases=[]
    def reject(label,bbs=stream,dos=opposite,times=trace,expected=payload):
        try:replay(bbs,dos,times,name,expected)
        except (AssertionError,ValueError,TypeError,StopIteration) as e:cases.append(dict(case=label,rejected=True,reason=str(e)))
        else:raise AssertionError('Corruption passed: '+label)
    def damage(b,at):
        data=bytearray(b);data[at]^=1;return bytes(data)
    at=opposite.index(b'\x18'*8+b'\x08'*10);reject('missing-full-local-cancel-burst',dos=damage(opposite,at))
    reject('CRC-corrupt-data-before-cancel',bbs=damage(stream,first['end']))
    reject('CRC-corrupt-retry-data',bbs=damage(stream,retry['files'][0]['packets'][0]['offset']))
    reject('wrong-expected-source',expected=damage(payload,0))
    for kind,label in [(11,'missing-verified-EOF'),(8,'missing-initial-sender-ZFIN')]:
        data=bytearray(stream)
        for h in scan(stream,retry['start']):
            if h['type']==kind:data[h['offset']+4]^=1
        reject(label,bbs=bytes(data))
    eof_time=timestamp(trace,'bbs',retry['files'][0]['end']-1)
    for kind,label in [(1,'missing-post-EOF-receiver-ZRINIT'),(8,'missing-receiver-ZFIN')]:
        data=bytearray(opposite)
        for h in scan(opposite):
            if h['type']==kind and timestamp(trace,'dos',h['offset'])>=eof_time:data[h['offset']+4]^=1
        reject(label,dos=bytes(data))
    reject('missing-literal-OO',bbs=damage(stream,retry['end']-2))
    late=copy.deepcopy(trace);finish=next(h for h in scan(opposite) if h['type']==8 and timestamp(trace,'dos',h['offset'])>=eof_time)
    entry=next(e for e in late if e['direction']=='dos' and e['offset']<=finish['offset']<e['offset']+e['size'])
    entry['seconds']=timestamp(trace,'bbs',retry['end']-2)+.001
    reject('receiver-ZFIN-arrives-after-OO',times=late)
    at=stream.index(b'NFO | lines',tail,retry['start']);reject('missing-NFO-after-cancel',bbs=damage(stream,at))
    at=stream.index(b'NFO | lines',after);reject('missing-NFO-after-retry',bbs=damage(stream,at))
    replay_packets=[p for p in retry['files'][0]['packets'] if p.get('after_eof')]
    if replay_packets:reject('corrupt-late-source-replay',bbs=damage(stream,replay_packets[0]['offset']))
    report=dict(passed=True,cases=cases,post_EOF_replays=len(replay_packets),finish=retry['finish'],
        checker_sha256=sha(Path(__file__)),auditor_sha256=sha(ROOT/'lab/bbs/audit_zmodem.py'),
        capture_hashes={p:sha(out/p) for p in ('display.bin','serial-received.bin','trace.json','cancel-checks.json')},
        scope='Actual retained cancellation/retry capture; CRC, exact source, EOF, receiver completion, full cancel burst, final retries/OO and menu responses. Each damaged condition must reject; no protocol replies generated.')
    (out/'cancel-audit-negative-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Cancellation audit:',len(cases),'corruptions rejected')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True)
    main(p.parse_args())
