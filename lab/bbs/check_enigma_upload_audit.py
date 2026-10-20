#!/usr/bin/env python3
"""Re-audit the binary/empty upload and reject damaged wire/catalog evidence."""
import argparse,copy,hashlib,json
from functools import lru_cache
from unittest.mock import patch
from pathlib import Path
from audit_zmodem import scan,packet,audit_batch,audit_controls
from test_transfer_dos import timestamp,offset_after
from enigma_key_stream_fixture import ROOT,owned
from enigma_notes_dos import sha


def unknown_times(stream,expected):
    seen=set()
    for h in scan(stream):
        if h['type']!=4:continue
        raw=packet(stream,h['end'],h['format'])['payload']
        name,attrs=raw.split(b'\0',1);name=name.decode('ascii').upper()
        assert name in expected and len(raw)==128
        value,padding=attrs.split(b'\0',1)
        assert value==str(len(expected[name])).encode()+b' 0' and not any(padding),'ZFILE time is not explicitly unknown'
        seen.add(name)
    assert seen==set(expected)


def canceled_prefix(stream,opposite,trace,expected):
    cancel_at=stream.index(b'\x18'*8+b'\x08'*10);when=timestamp(trace,'dos',cancel_at)
    first=next(h for h in scan(stream) if h['type']==4)
    meta=packet(stream,first['end'],first['format'])
    from audit_zmodem import metadata
    assert metadata(meta['payload'])==('PCUP01.BIN',len(expected['PCUP01.BIN']))
    data=next(h for h in scan(stream,meta['end']) if h['type']==10)
    body=packet(stream,data['end'],data['format'])
    assert body['payload'] and body['payload']==expected['PCUP01.BIN'][:body['length']]
    assert body['end']<cancel_at and not any(h['type']==11 and h['offset']<cancel_at for h in scan(stream))
    ack=next(h for h in scan(opposite) if h['type']==3 and h['position']>=1024 and timestamp(trace,'bbs',h['offset'])<when)
    search=stream.index(b'S\r',cancel_at+18)
    return dict(offset=cancel_at,first_offer=first,first_data={k:v for k,v in body.items() if k!='payload'},ack=ack,first_search=search)


def canceled_snapshot(snapshot):
    assert len(snapshot)==1 and not snapshot[0]['installed']
    assert all(not r['entries'] for r in snapshot[0]['entries'])
    assert not snapshot[0]['temporary_files'] and snapshot[0]['source_files_unchanged']


def replay(stream,opposite,trace,expected,require_unknown=False,cancel_first=False):
    cancel=canceled_prefix(stream,opposite,trace,expected) if cancel_first else None
    audit=audit_batch(stream,expected,cancel['first_search']+2 if cancel else 0)
    if cancel:
        first=offset_after(trace,'bbs',timestamp(trace,'dos',cancel['first_search']))
        retry=offset_after(trace,'bbs',timestamp(trace,'dos',audit['start']))
        assert first is not None and retry is not None
        assert b'NFO | lines 1-15/24' in opposite[first:retry] and b'PCPLUS NFO LINE 01 : synthetic game 01' in opposite[first:retry],'No NFO between cancel and retry'
    if require_unknown:unknown_times(stream,expected)
    post=stream.index(b'S\r',offset_after(trace,'dos',timestamp(trace,'dos',audit['end']-1)))
    when=timestamp(trace,'dos',post)
    # The auditor asks for the same chunk times thousands of times. Each
    # replay owns one immutable trace, including a fresh trace for late-FIN
    # corruption. Cache the canonical linear lookup; do not alter its result,
    # packet/control validation or the on-disk capture.
    @lru_cache(maxsize=None)
    def lookup(direction,offset):return timestamp(trace,direction,offset)
    def indexed(actual,direction,offset):
        assert actual is trace
        return lookup(direction,offset)
    with patch('test_transfer_dos.timestamp',indexed):
        audit_controls(audit,opposite,trace,'dos',when,False)
    start=offset_after(trace,'bbs',when);assert start is not None
    assert b'PCPLUS PROBE 01 (1991).ZIP' in opposite[start:] and b'NFO | lines 1-15/24' in opposite[start:] and b'PCPLUS NFO LINE 01 : synthetic game 01' in opposite[start:]
    return audit


def catalog(rows,expected,candidate,date_bounds=None):
    assert {r['name'] for r in rows}==set(expected)
    for row in rows:
        name=row['name'];assert len(row['entries'])==1;e=row['entries'][0]
        assert e['fileName']==name and e['areaTag']==e['storageTag']=='pcplus_upload'
        path=Path(e['filePath']);assert path.resolve().parent==candidate/'file_base/pcplus_upload'
        assert path.read_bytes()==expected[name] and e['fileSha256']==hashlib.sha256(expected[name]).hexdigest()
        assert e['meta']['byte_size']==len(expected[name]) and e['meta']['upload_by_username']=='loclab'
        assert e['desc']==Path(name).stem,'Upload details were changed unintentionally'
        if date_bounds is not None:
            assert date_bounds[0]<=path.stat().st_mtime_ns<=date_bounds[1],'Received filesystem date is not a current creation date'


def main(args):
    assert args.label.replace('-','').replace('_','').isalnum()
    candidate=owned(args.candidate);out=ROOT/'build/bbs-lab/results/enigma'/args.label
    result=json.loads((out/'upload-checks.json').read_text());assert result['passed'] and all(result['checks'].values())
    expected={p.name:p.read_bytes() for p in (out/'SEND').iterdir()};assert any(not v for v in expected.values()) and any(v for v in expected.values())
    stream=(out/'serial-received.bin').read_bytes();opposite=(out/'display.bin').read_bytes();trace=json.loads((out/'trace.json').read_text())
    bounds=result.get('received_date_bounds_ns');require_unknown=bounds is not None
    cancel_first=result.get('cancel_first',False)
    snapshot=json.loads((out/'cancel-upload-snapshots.json').read_text()) if cancel_first else None
    if cancel_first:canceled_snapshot(snapshot)
    audited=replay(stream,opposite,trace,expected,require_unknown,cancel_first);rows=json.loads((out/'server-upload-metadata.json').read_text());catalog(rows,expected,candidate,bounds)
    cases=[]
    def reject(label,sent=stream,received=opposite,times=trace,source=expected,entries=rows,cancel_snapshot=snapshot):
        try:
            replay(sent,received,times,source,require_unknown,cancel_first);catalog(entries,source,candidate,bounds)
            if cancel_first:canceled_snapshot(cancel_snapshot)
        except (AssertionError,ValueError,TypeError,KeyError,OSError,StopIteration) as e:cases.append(dict(case=label,rejected=True,reason=str(e)))
        else:raise AssertionError('Damaged upload evidence passed: '+label)
    def damage(data,at):
        changed=bytearray(data);changed[at]^=1;return bytes(changed)
    nonempty=next(f for f in audited['files'] if f['length']);empty=next(f for f in audited['files'] if not f['length'])
    reject('CRC-corrupt-binary-data',sent=damage(stream,nonempty['packets'][0]['offset']))
    changed=dict(expected);changed[nonempty['name']]=damage(changed[nonempty['name']],0);reject('wrong-source-bytes',source=changed)
    reject('missing-empty-file-offer',sent=damage(stream,empty['start']+4))
    broken=bytearray(stream)
    for h in scan(stream,empty['start']):
        if h['type']==11 and h['offset']<empty['end']:broken[h['offset']+4]^=1
    reject('missing-empty-file-EOF',sent=bytes(broken))
    broken=bytearray(opposite)
    for h in scan(opposite):
        if h['type']==8:broken[h['offset']+4]^=1
    reject('missing-receiver-ZFIN',received=bytes(broken))
    reject('missing-literal-OO',sent=damage(stream,audited['end']-2))
    finish=next(h for h in scan(opposite) if h['type']==8);late=copy.deepcopy(trace)
    entry=next(e for e in late if e['direction']=='bbs' and e['offset']<=finish['offset']<e['offset']+e['size'])
    entry['seconds']=timestamp(trace,'dos',audited['end']-2)+.001;reject('receiver-ZFIN-after-OO',times=late)
    at=opposite.rindex(b'NFO | lines');reject('missing-post-upload-NFO',received=damage(opposite,at))
    for field,value,label in [('byte_size',1,'wrong-empty-size'),('upload_by_username','locadmin','wrong-uploader')]:
        changed=copy.deepcopy(rows);row=next(r for r in changed if not expected[r['name']]);row['entries'][0]['meta'][field]=value;reject(label,entries=changed)
    changed=copy.deepcopy(rows);changed[0]['entries'][0]['fileSha256']='0'*64;reject('wrong-catalog-hash',entries=changed)
    changed=copy.deepcopy(rows);changed[0]['entries'][0]['areaTag']='pcplus_games';reject('wrong-area',entries=changed)
    changed=copy.deepcopy(rows);changed[0]['entries'][0]['desc']='UNRELATED';reject('wrong-description',entries=changed)
    if require_unknown:
        # Keep a valid data CRC. The date policy must reject this independently
        # of damaged framing or a changed transfer length.
        from check_zmodem_wire import packet as encode_packet
        h=next(h for h in scan(stream) if h['type']==4);p=packet(stream,h['end'],h['format'])
        raw=p['payload'];at=raw.index(b'\0')+1;end=raw.index(b'\0',at)
        changed=raw[:end-1]+b'1'+raw[end:]
        altered=stream[:h['end']]+encode_packet(changed,h['format'],p['ending'],0)+stream[p['end']:]
        reject('valid-CRC-nonzero-invented-time',sent=altered)
    if cancel_first:
        cancel=canceled_prefix(stream,opposite,trace,expected)
        reject('missing-cancel-burst',sent=damage(stream,cancel['offset']))
        changed=bytearray(opposite)
        for h in scan(opposite):
            if h['type']==3 and timestamp(trace,'bbs',h['offset'])<timestamp(trace,'dos',cancel['offset']):changed[h['offset']+4]^=1
        reject('no-peer-ACK-before-Escape',received=bytes(changed))
        start=offset_after(trace,'bbs',timestamp(trace,'dos',cancel['first_search']))
        reject('missing-between-cancel-retry-NFO',received=damage(opposite,opposite.index(b'NFO | lines',start)))
        for field,value,label in [('installed',['PCUP01.BIN'],'canceled-file-installed'),('temporary_files',['retained/PCUP01.BIN'],'canceled-temp-retained'),('source_files_unchanged',False,'source-modified-after-cancel')]:
            changed=copy.deepcopy(snapshot);changed[0][field]=value;reject(label,cancel_snapshot=changed)
        changed=copy.deepcopy(snapshot);changed[0]['entries'][0]['entries']=[{'fileName':'PCUP01.BIN'}];reject('canceled-catalog-entry',cancel_snapshot=changed)
        reject('cancel-without-confirmed-retry',sent=stream[:cancel['first_search']+2])
    report=dict(passed=True,cases=cases,checker_sha256=sha(Path(__file__)),auditor_sha256=sha(ROOT/'lab/bbs/audit_zmodem.py'),
        capture_hashes={p:sha(out/p) for p in ('upload-checks.json','serial-received.bin','display.bin','trace.json','server-upload-metadata.json',*(['cancel-upload-snapshots.json'] if cancel_first else []))},
        scope='Actual retained two-file upload wire and official FileEntry metadata; each payload/empty-file/finish/timing/menu/catalog corruption must reject. No protocol replies generated.')
    (out/'upload-audit-negative-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Upload audit:',len(cases),'corruptions rejected')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True)
    main(p.parse_args())
