#!/usr/bin/env python3
"""Re-audit the binary/empty upload and reject damaged wire/catalog evidence."""
import argparse,copy,hashlib,json
from functools import lru_cache
from unittest.mock import patch
from pathlib import Path
from audit_zmodem import scan,audit_batch,audit_controls
from test_transfer_dos import timestamp,offset_after
from enigma_key_stream_fixture import ROOT,owned
from enigma_notes_dos import sha


def replay(stream,opposite,trace,expected):
    audit=audit_batch(stream,expected)
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


def catalog(rows,expected,candidate):
    assert {r['name'] for r in rows}==set(expected)
    for row in rows:
        name=row['name'];assert len(row['entries'])==1;e=row['entries'][0]
        assert e['fileName']==name and e['areaTag']==e['storageTag']=='pcplus_upload'
        path=Path(e['filePath']);assert path.resolve().parent==candidate/'file_base/pcplus_upload'
        assert path.read_bytes()==expected[name] and e['fileSha256']==hashlib.sha256(expected[name]).hexdigest()
        assert e['meta']['byte_size']==len(expected[name]) and e['meta']['upload_by_username']=='loclab'
        assert e['desc']==Path(name).stem,'Upload details were changed unintentionally'


def main(args):
    assert args.label.replace('-','').replace('_','').isalnum()
    candidate=owned(args.candidate);out=ROOT/'build/bbs-lab/results/enigma'/args.label
    result=json.loads((out/'upload-checks.json').read_text());assert result['passed'] and all(result['checks'].values())
    expected={p.name:p.read_bytes() for p in (out/'SEND').iterdir()};assert any(not v for v in expected.values()) and any(v for v in expected.values())
    stream=(out/'serial-received.bin').read_bytes();opposite=(out/'display.bin').read_bytes();trace=json.loads((out/'trace.json').read_text())
    audited=replay(stream,opposite,trace,expected);rows=json.loads((out/'server-upload-metadata.json').read_text());catalog(rows,expected,candidate)
    cases=[]
    def reject(label,sent=stream,received=opposite,times=trace,source=expected,entries=rows):
        try:replay(sent,received,times,source);catalog(entries,source,candidate)
        except (AssertionError,ValueError,TypeError,KeyError,OSError) as e:cases.append(dict(case=label,rejected=True,reason=str(e)))
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
    report=dict(passed=True,cases=cases,checker_sha256=sha(Path(__file__)),auditor_sha256=sha(ROOT/'lab/bbs/audit_zmodem.py'),
        capture_hashes={p:sha(out/p) for p in ('upload-checks.json','serial-received.bin','display.bin','trace.json','server-upload-metadata.json')},
        scope='Actual retained two-file upload wire and official FileEntry metadata; each payload/empty-file/finish/timing/menu/catalog corruption must reject. No protocol replies generated.')
    (out/'upload-audit-negative-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Upload audit:',len(cases),'corruptions rejected')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True)
    main(p.parse_args())
