#!/usr/bin/env python3
"""Validate real carrier/retry evidence, then reject damaged capture conditions."""
import argparse,copy,hashlib,json
from pathlib import Path
from audit_zmodem import scan,packet,metadata,audit_batch,audit_controls
from test_transfer_dos import timestamp,offset_after
from enigma_key_stream_fixture import ROOT,owned
from enigma_notes_dos import sha


def replay(first,stream,opposite,trace,name,payload,snapshots,notices):
    assert len(snapshots)==2 and snapshots[0]['kind']=='partial-before-interruption'
    partial=snapshots[0];assert 0<partial['bytes']<len(payload)
    assert partial['sha256']==hashlib.sha256(payload[:partial['bytes']]).hexdigest()
    assert partial['first_login_trace']=='STARTAUTHREADY'
    assert snapshots[1]['kind']=='before-second-login' and snapshots[1]['files']==[]
    assert any('carrier lost' in n.lower() for n in notices)
    offer=next(h for h in scan(first) if h['type']==4)
    assert metadata(packet(first,offer['end'],offer['format'])['payload'])==(name,len(payload))
    data=next(h for h in scan(first,offer['end']) if h['type']==10)
    p=packet(first,data['end'],data['format'])['payload'];assert p and p==payload[:len(p)]
    assert not any(h['type']==11 for h in scan(first))
    result=audit_batch(stream,{name:payload})
    tail=offset_after(trace,'dos',timestamp(trace,'bbs',result['end']-1));assert tail is not None
    post=opposite.index(b'n',tail);when=timestamp(trace,'dos',post)
    result['controls']=audit_controls(result,opposite,trace,'bbs',when,False)
    start=offset_after(trace,'bbs',when);assert start is not None
    assert b'NFO | lines 1-15/24' in stream[start:] and b'PCPLUS NFO LINE 01 : synthetic game 01' in stream[start:]
    return result


def main(args):
    assert args.label.replace('-','').replace('_','').isalnum()
    candidate=owned(args.candidate);out=ROOT/'build/bbs-lab/results/enigma'/args.label
    result=json.loads((out/'carrier-checks.json').read_text());assert result['passed'] and all(result['checks'].values())
    fixture=json.loads((candidate/'search-instance.json').read_text());archive=fixture['archives'][1]
    source=candidate/'file_base/pcplus_games'/archive['name'];assert sha(source)==archive['sha256']
    name=archive['name'].upper();payload=source.read_bytes()
    first=(out/'connection-1/display.bin').read_bytes();stream=(out/'connection-2/display.bin').read_bytes()
    opposite=(out/'connection-2/serial-received.bin').read_bytes();trace=json.loads((out/'connection-2/trace.json').read_text())
    snapshots=result['snapshots'];notices=result['notices']
    validated=replay(first,stream,opposite,trace,name,payload,snapshots,notices);cases=[]
    def reject(label,interrupted=first,bbs=stream,dos=opposite,times=trace,expected=payload,files=snapshots,screen=notices):
        try:replay(interrupted,bbs,dos,times,name,expected,files,screen)
        except (AssertionError,ValueError,TypeError,StopIteration) as e:cases.append(dict(case=label,rejected=True,reason=str(e)))
        else:raise AssertionError('Corrupted carrier capture passed: '+label)
    def damage(data,at):
        value=bytearray(data);value[at]^=1;return bytes(value)
    first_data=next(h for h in scan(first) if h['type']==10)
    reject('CRC-corrupt-first-transfer-data',interrupted=damage(first,first_data['end']))
    reject('CRC-corrupt-retry-data',bbs=damage(stream,validated['files'][0]['packets'][0]['offset']))
    reject('wrong-source-bytes',expected=damage(payload,0))
    broken=copy.deepcopy(snapshots);broken[0]['sha256']='0'*64;reject('wrong-partial-prefix-hash',files=broken)
    broken=copy.deepcopy(snapshots);broken[1]['files']=['PCRX.$$$'];reject('stage-survives-redial',files=broken)
    reject('missing-carrier-notice',screen=[])
    broken=bytearray(stream)
    for h in scan(stream):
        if h['type']==11:broken[h['offset']+4]^=1
    reject('missing-verified-EOF',bbs=bytes(broken))
    broken=bytearray(opposite)
    for h in scan(opposite):
        if h['type']==8:broken[h['offset']+4]^=1
    reject('missing-receiver-ZFIN',dos=bytes(broken))
    reject('missing-literal-OO',bbs=damage(stream,validated['end']-2))
    first_ack=next(h for h in scan(opposite) if h['type']==3)
    from check_zmodem import h as encode_header
    future=encode_header(3,len(payload)+1)
    assert len(future)==first_ack['end']-first_ack['offset']
    altered=opposite[:first_ack['offset']]+future+opposite[first_ack['end']:]
    reject('CRC-valid-ACK-beyond-verified-source',dos=altered)
    late=copy.deepcopy(trace);finish=next(h for h in scan(opposite) if h['type']==8)
    entry=next(e for e in late if e['direction']=='dos' and e['offset']<=finish['offset']<e['offset']+e['size'])
    entry['seconds']=timestamp(trace,'bbs',validated['end']-2)+.001
    reject('receiver-ZFIN-arrives-after-OO',times=late)
    at=stream.index(b'NFO | lines',validated['end']);reject('missing-post-retry-NFO',bbs=damage(stream,at))
    report=dict(passed=True,cases=cases,checker_sha256=sha(Path(__file__)),auditor_sha256=sha(ROOT/'lab/bbs/audit_zmodem.py'),
        capture_hashes={p:sha(out/p) for p in ('carrier-checks.json','connection-1/display.bin','connection-2/display.bin','connection-2/serial-received.bin','connection-2/trace.json')},
        scope='Actual retained interrupted receive/reconnect/retry capture; each CRC/source/storage/carrier/finish/menu corruption must reject. No socket or DOS execution in this replay.')
    (out/'carrier-audit-negative-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Carrier audit:',len(cases),'corruptions rejected')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True)
    main(p.parse_args())
