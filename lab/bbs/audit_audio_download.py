#!/usr/bin/env python3
"""Independent actual audio/BBS download, CRC/control, file and resume audit."""
import argparse,hashlib,json
from pathlib import Path
from modem import Telnet
from audit_zmodem import audit_batch,audit_controls
from test_transfer_dos import timestamp
from enigma_transfer import metadata,STORAGE,HELPER


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path)
    out=p.parse_args().cohort.resolve();r=json.loads((out/'result.json').read_text());assert r['route']=='download'
    events=[json.loads(v) for v in (out/'BBS-relay-events.jsonl').read_text().splitlines()]
    raw={'to_bbs':(out/'bbs-input.bin').read_bytes(),'from_bbs':(out/'bbs-output.bin').read_bytes()}
    decoders={d:Telnet() for d in raw};streams={d:bytearray() for d in raw};ends={d:0 for d in raw};trace=[]
    for event in events:
        d=event['direction'];assert event['offset']==ends[d];end=ends[d]+event['count']
        data,_=decoders[d].feed(raw[d][ends[d]:end]);ends[d]=end
        if data:trace.append({'direction':'dos' if d=='to_bbs' else 'bbs','offset':len(streams[d]),'size':len(data),'seconds':event['seconds']})
        streams[d].extend(data)
    assert all(ends[d]==len(raw[d]) for d in raw)
    sent=bytes(streams['to_bbs']);display=bytes(streams['from_bbs'])
    source=STORAGE/'PCXTEST.BIN';expected=source.read_bytes();checks={'post_protocol_search_key_observed':False};errors=[];protocol=None
    checks['source_unchanged']=len(expected)==11521 and sha(source)==r['download']['expected_sha256']
    try:
        protocol=audit_batch(display,{'PCXTEST.BIN':expected})
        end_time=timestamp(trace,'bbs',protocol['end']-1)
        post=next((v for v in trace if v['direction']=='dos' and v['seconds']>end_time and b'S\r' in sent[v['offset']:v['offset']+v['size']+1]),None)
        checks['post_protocol_search_key_observed']=post is not None
        # Preserve the mandatory search-key gate separately from wire finish.
        # If input never resumes, the complete capture bounds control diagnosis;
        # that cannot make the run pass because this added gate remains false.
        protocol['controls']=audit_controls(protocol,sent,trace,'bbs',post['seconds'] if post else max(v['seconds'] for v in trace)+1)
        checks['complete_CRC_ZMODEM_and_opposite_controls']=True
    except Exception as e:
        errors.append(repr(e));checks['complete_CRC_ZMODEM_and_opposite_controls']=False
    target=out/'RECV/PCXTEST.BIN'
    checks['exact_DOS_file']=target.is_file() and target.read_bytes()==expected
    checks['only_expected_DOS_file']={p.name for p in (out/'RECV').iterdir()}=={'PCXTEST.BIN'}
    checks['no_receive_staging']=not any(p.name.startswith(('PCRX.','PCZRX.')) for p in out.rglob('*'))
    rows=[json.loads(v) for v in (out/'server-session.jsonl').read_text().splitlines()]
    executions=[i for i,v in enumerate(rows) if v.get('msg')=='Executing external protocol']
    exits=[i for i,v in enumerate(rows) if v.get('msg')=='Process exited' and v.get('exitCode')==0]
    checks['real_owned_helper']=len(executions)==1 and rows[executions[0]].get('cmd')==str(HELPER)
    checks['real_helper_exit_zero']=len(executions)==len(exits)==1 and executions[0]<exits[0]
    tail=[v.get('menuName') for v in rows[exits[-1]+1:]] if exits else []
    resumed=False
    try:
        first=tail.index('fileBaseMainMenu');search=tail.index('fileBaseSearch',first+1)
        tail.index('fileBaseListEntries',search+1);resumed=True
    except ValueError:pass
    checks['post_helper_keyboard_search_and_list']=resumed
    after=metadata('PCXTEST.BIN');before=r['download']['metadata_before']
    checks['official_file_and_counter']=len(after)==len(before)==1 and after[0]['fileSha256']==sha(source) and Path(after[0]['filePath']).resolve()==source.resolve() and after[0]['meta'].get('dl_count',0)>=before[0]['meta'].get('dl_count',0)+1
    prm=(out/'MODEM.PRM').read_bytes()
    checks['automatic_receive_profile']=prm[0x42c:0x42e]==b'\x01\0' and prm[0x31c:].split(b'\0',1)[0]==b'D:\\RECV\\'
    base=json.loads((out/'independent-audit.json').read_text());io=json.loads((out/'serial-io-audit.json').read_text())
    checks['base_byte_and_cleanup_audit']=base['passed'];checks['frontend_ownership_audit']=io['evidence_consistent']
    checks['no_gateway_errors']=not r['gateway']['errors']
    checks['producer_hashes']=all(sha(out/name)==h for name,h in r['captures_sha256'].items())
    if protocol:
        for file in protocol.get('files',[]):file.pop('source',None)
    result={'passed':all(checks.values()),'checks':checks,'protocol':protocol,'errors':errors,'official_metadata':after,
            'source_bytes':len(expected),'source_sha256':sha(source),'received_sha256':sha(target) if target.is_file() else None,
            'decoded_streams':{'upstream_bytes':len(sent),'downstream_bytes':len(display)},
            'capture_sha256':{name:sha(out/name) for name in ['result.json','BBS-relay-events.jsonl','bbs-input.bin','bbs-output.bin','server-session.jsonl','MODEM.PRM','independent-audit.json','serial-io-audit.json']},
            'auditor_sha256':sha(Path(__file__)),'protocol_auditor_sha256':sha(Path(__file__).with_name('audit_zmodem.py')),
            'scope':'Actual normal audio/stock BBS download: independent passive CRC/sequence/payload/EOF/finish and opposite-direction control audit, exact installed DOS bytes, official server API and post-helper input/menu sequence. No generated protocol replies or altered BBS. Single file/direction only; no upload/cancel/retry/fault/pressure/physical or whole-application claim.'}
    (out/'download-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']


if __name__=='__main__':main()
