#!/usr/bin/env python3
"""Independent actual audio upload wire, storage, official metadata and resume."""
import argparse,datetime,hashlib,json
from pathlib import Path
import enigma
from enigma_transfer import STORAGE,HELPER
from enigma_upload_dos import metadata
from modem import Telnet
from audit_audio_download import frontend_trace
from audit_zmodem import audit_batch,audit_controls,scan
from test_transfer_dos import timestamp


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
    read=lambda name:json.loads((out/name).read_text())
    r=read('result.json');assert r['route']=='upload'
    base=read('independent-audit.json');io=read('serial-io-audit.json')
    before=r['upload']['prepared'];source=out/'SEND/AUDIOUP.BIN';expected=source.read_bytes()
    sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
    checks={'fresh_owned_name':before['metadata_before']==[],
        'source_identity':source.resolve()==Path(before['source_path']).resolve() and len(expected)==11521 and sha(source)==before['source_sha256'],
        'source_stat_preserved':[source.stat().st_ino,source.stat().st_size,source.stat().st_mtime_ns]==before['source_stat'],
        'frontend_timing_complete':False,'post_protocol_search_key_observed':False}
    errors=[];protocol=None;timing=None;trace=[]
    try:
        trace,timing=frontend_trace(out,sent,display,base['payloads']['expected_bridge_bytes'])
        checks['frontend_timing_complete']=True
        protocol=audit_batch(sent,{'AUDIOUP.BIN':expected})
        end=timestamp(trace,'dos',protocol['end']-1)
        post=next((e for e in trace if e['direction']=='dos' and e['seconds']>end and b'S\r' in sent[e['offset']:e['offset']+e['size']+1]),None)
        checks['post_protocol_search_key_observed']=post is not None
        protocol['controls']=audit_controls(protocol,display,trace,'dos',post['seconds'] if post else max(e['seconds'] for e in trace)+1)
        checks['complete_CRC_ZMODEM_and_opposite_controls']=True
    except Exception as error:
        errors.append(repr(error));checks['complete_CRC_ZMODEM_and_opposite_controls']=False
    entries=metadata(enigma.SOURCE,['AUDIOUP.BIN']);assert len(entries)==1
    entries=entries[0]['entries'];target=STORAGE/'AUDIOUP.BIN'
    checks['one_official_entry']=len(entries)==1
    checks['exact_installed_server_file']=target.is_file() and target.read_bytes()==expected
    checks['official_metadata_matches']=len(entries)==1 and entries[0]['fileName']=='AUDIOUP.BIN' and entries[0]['areaTag']==entries[0]['storageTag']=='pcplus_transfer' and Path(entries[0]['filePath']).resolve()==target.resolve() and entries[0]['fileSha256']==sha(source) and entries[0]['meta'].get('byte_size')==len(expected) and entries[0]['meta'].get('upload_by_username')=='loclab'
    anchors=r['clock_anchors'];start=int(anchors[0]['wall_ns']);end=int(anchors[-1]['wall_ns'])
    checks['stored_time_not_invented_or_future']=target.is_file() and start-2_000_000_000<=target.stat().st_mtime_ns<=end+2_000_000_000
    rows=[json.loads(s) for s in (out/'server-session.jsonl').read_text().splitlines()]
    executes=[i for i,e in enumerate(rows) if e.get('msg')=='Executing external protocol']
    exits=[i for i,e in enumerate(rows) if e.get('msg')=='Process exited' and e.get('exitCode')==0]
    checks['actual_owned_receiver_helper']=len(executes)==1 and rows[executes[0]].get('cmd')==str(HELPER) and rows[executes[0]].get('direction')=='recv'
    checks['helper_exit_zero']=len(executes)==len(exits)==1 and executes[0]<exits[0]
    tail=[e.get('menuName') for e in rows[exits[-1]+1:]] if exits else []
    resumed=False
    try:
        first=tail.index('fileBaseMainMenu');search=tail.index('fileBaseSearch',first+1);tail.index('fileBaseListEntries',search+1);resumed=True
    except ValueError:pass
    checks['postupload_keyboard_search_and_list']=resumed
    late=None
    if protocol and checks['helper_exit_zero'] and timing:
        exitms=datetime.datetime.fromisoformat(rows[exits[0]]['time'].replace('Z','+00:00')).timestamp()*1000
        inputs=[json.loads(s) for s in (out/'serial-input-events.jsonl').read_text().splitlines()];prefix=timing['directions']['dos']['raw_prefix_bytes'];late=[]
        extra=list(scan(sent,protocol['end']))
        checks['no_extra_protocol_frames_after_finish']=not extra
        headers=[e for e in protocol['events'] if e['kind']=='header']+extra
        for header in headers:
            event=next(e for e in inputs if e['offset']<=prefix+header['offset']<e['offset']+e['length'])
            if event['wallTimeMs']>exitms:late.append(header)
        oo=next(e for e in inputs if e['offset']<=prefix+protocol['end']-1<e['offset']+e['length'])
        checks['no_protocol_tail_after_helper_exit']=not late and oo['wallTimeMs']<=exitms
    else:
        checks['no_protocol_tail_after_helper_exit']=False
        checks['no_extra_protocol_frames_after_finish']=False
    checks['base_byte_and_cleanup_audit']=base['passed'];checks['frontend_ownership_audit']=io['evidence_consistent']
    checks['no_gateway_errors']=not r['gateway']['errors']
    checks['producer_capture_hashes']=all(sha(out/name)==value for name,value in r['captures_sha256'].items())
    if protocol:
        for file in protocol['files']:file.pop('source',None)
    names=['result.json','independent-audit.json','serial-io-audit.json','bbs-input.bin','bbs-output.bin','server-session.jsonl','serial-in.bin','serial-out.bin','serial-input-events.jsonl','serial-write-events.jsonl','node-result.json','caller-decoded.bin']
    report={'passed':all(checks.values()),'checks':checks,'protocol':protocol,'errors':errors,'control_timing':timing,
        'official_metadata':entries,'source_bytes':len(expected),'source_sha256':sha(source),'stored_sha256':sha(target) if target.is_file() else None,
        'late_protocol_controls':late,'capture_sha256':{name:sha(out/name) for name in names},
        'auditor_sha256':sha(Path(__file__)),'protocol_auditor_sha256':sha(Path(__file__).with_name('audit_zmodem.py')),
        'scope':'Single actual DOS-to-stock-ENiGMA upload through software SIP/RTP/DSP. Independent passive CRC/payload/offset/EOF/opposite-controls/FIN/OO, exact official storage and timestamp, preserved source, post-form search/list, transport identity and DOS cleanup. No synthetic peer replies or changed server. No cancellation/loss/pressure/physical or whole-application acceptance.'}
    (out/'upload-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']


if __name__=='__main__':main()
