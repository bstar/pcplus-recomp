#!/usr/bin/env python3
"""Replay current IRQ downloads, exact media and post-transfer BBS interaction."""
import argparse
import json
from pathlib import Path
import socket
import struct
import sys

from build_guarded_helper import ROOT,LOOKUP
from package_special_edition import sha
sys.path.insert(0,str(ROOT/'lab/bbs'))
from audit_zmodem import audit_batch,audit_controls
from test_transfer_dos import timestamp,offset_after
from enigma_key_stream_fixture import pid


def replay(folder,source,name,*,normalize_empty=False,require_post_menu=True):
    data=source.read_bytes();display=(folder/'display.bin').read_bytes();keyboard=(folder/'serial-received.bin').read_bytes()
    trace=json.loads((folder/'trace.json').read_text())
    empty=[event for event in trace if not event['size']]
    if normalize_empty:
        assert empty and all(e['direction']=='bbs'and e['offset']==0 for e in empty)
        trace=[event for event in trace if event['size']]
    else:assert not empty
    for direction,stream in [('bbs',display),('dos',keyboard)]:
        end=0
        for event in (e for e in trace if e['direction']==direction):
            assert event['size']>0 and event['offset']==end
            end+=event['size']
        assert end==len(stream)
    audit=audit_batch(display,{name:data})
    assert len(audit['files'])==1
    file=audit['files'][0];assert file['source']==data and file['length']==len(data)and file['sha256']==sha(source)
    first_time=timestamp(trace,'bbs',audit['start'])
    cut=offset_after(trace,'dos',first_time);assert cut is not None
    request=keyboard[:cut].rfind(name.encode()+b'\r');assert request>=0
    assert timestamp(trace,'dos',request)<=first_time
    last_time=timestamp(trace,'bbs',audit['end']-1)
    tail=offset_after(trace,'dos',last_time);assert tail is not None
    post=keyboard.find(b'S\r',tail);assert post>=0
    post_time=timestamp(trace,'dos',post)
    controls=audit_controls(audit,keyboard,trace,'bbs',post_time)
    bbs_tail=offset_after(trace,'bbs',post_time);assert bbs_tail is not None
    reply=display[bbs_tail:];cursor=0
    divisor,unit=(1048576,'MB')if len(data)>=1048576 else(1024,'KB')
    displayed_size=f'{len(data)/divisor:.2f}'.rstrip('0').rstrip('.')
    post_menu=True
    for token in (name+' ',displayed_size+' ',unit+' '):
        cursor=reply.find(token.encode(),cursor)
        if cursor<0:
            post_menu=False
            break
        cursor+=len(token)
    if require_post_menu:assert post_menu,'Missing ordered postbatch response'
    assert (folder/'RECV'/name).read_bytes()==data
    file.pop('source')
    return dict(file=file,controls=controls,finish=audit['finish'],ignored_negotiation_events=len(empty),
                post_menu_request_offset=post,post_menu_reply_offset=bbs_tail,post_menu=post_menu)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--small-label',required=True);p.add_argument('--large-label',required=True)
    p.add_argument('--large-candidate',type=Path,required=True)
    p.add_argument('--observer-check',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--counterexamples',type=Path,required=True)
    args=p.parse_args()
    terminal=ROOT/'build'/(LOOKUP+'-custom-irq')/'TERMINAL.EXE'
    manifest=json.loads((terminal.parent/'manifest.json').read_text())
    assert manifest['experimental_custom_irq']and sha(terminal)==manifest['binary_sha256']
    sources={};artifacts={}
    def merge(mapping):
        for name,digest in mapping.items():
            assert sha(ROOT/name)==digest and(name not in sources or sources[name]==digest),name
            sources[name]=digest
    merge(manifest['sources'])
    cases=[]
    specs=[(args.small_label,ROOT/'build/bbs-lab/irq-framed-server-01/candidate','PCXTEST.BIN',7,11521),
           (args.large_label,args.large_candidate.resolve(),'IRQDATA.BIN',5,65539)]
    for label,candidate,name,irq,size in specs:
        assert pid(candidate)is None
        folder=ROOT/'build/bbs-lab/results/enigma'/label;wrapper=folder.with_name(label+'-wrapper')
        report=json.loads((folder/'result.json').read_text());experiment=json.loads((wrapper/'experiment.json').read_text())
        assert report['passed']and report['standard_completion']and all(report['checks'].values())
        assert experiment['passed']and experiment['inputs_unchanged']
        assert experiment['message_count_before']==experiment['message_count_after']
        assert report['binary_sha256']==sha(terminal)and report['cpu']=='8086'
        assert report['serial']==dict(com=2,baud=19200,flow='HARD',irq=irq)
        assert report['server_endpoint']==dict(address='127.0.0.1',port=23234)
        assert report['experimental_server_instance']==str(candidate/'instance.json')
        merge(experiment['input_hashes'])
        config=(folder/'dosbox.conf').read_text()
        assert 'cputype=8086\n'in config and f'serial2=nullmodem irq:{irq} 'in config
        prm=(folder/'TEST.PRM').read_bytes();assert struct.unpack_from('<H',prm,0x186)[0]==irq
        assert struct.unpack_from('<H',prm,0x42c)[0]and b'D:\\RECV\\\0'in prm
        source=candidate/'file_base/pcplus_transfer'/name;assert source.stat().st_size==size
        protocol=replay(folder,source,name)
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        assert len((folder/'BEFORE.BIN').read_bytes())==42
        assert set(p.name for p in (folder/'RECV').iterdir())=={name}
        cases.append(dict(label=label,irq=irq,bytes=size,protocol=protocol,checks=report['checks'],
                          message_count_before=experiment['message_count_before'],message_count_after=experiment['message_count_after']))
        for root in (folder,wrapper):
            for path in root.rglob('*'):
                if path.is_file():artifacts[str(path.relative_to(ROOT))]=sha(path)
    fixture=json.loads((args.large_candidate/'irq-transfer-fixture.json').read_text())
    assert fixture['passed']and fixture['bytes']==65539 and fixture['metadata']['fileName']=='IRQDATA.BIN'
    assert int(fixture['metadata']['meta']['byte_size'])==65539
    assert fixture['sha256']==fixture['metadata']['fileSha256']==sha(specs[1][1]/'file_base/pcplus_transfer/IRQDATA.BIN')
    merge(fixture['sources'])
    observer=json.loads(args.observer_check.read_text());assert observer['passed']and observer['cases']==269
    merge(observer['sources'])
    # Earlier failed run remains failed. A diagnostic replay excludes only the
    # three zero-byte negotiation events; its original result is never changed.
    failed=ROOT/'build/bbs-lab/results/enigma/irq7-framed-transfer-01'
    old=json.loads((failed/'result.json').read_text());assert not old['passed']and'Empty observed chunk'in old['errors']
    diagnostic=replay(failed,specs[0][1]/'file_base/pcplus_transfer/PCXTEST.BIN','PCXTEST.BIN',normalize_empty=True)
    assert diagnostic['ignored_negotiation_events']==3
    failed_large=ROOT/'build/bbs-lab/results/enigma/irq5-framed-large-transfer-01'
    old_large=json.loads((failed_large/'result.json').read_text())
    assert not old_large['passed']and old_large['standard_completion']
    assert any('Missing ordered postbatch response'in e and'64.00 'in e for e in old_large['errors'])
    size_diagnostic=replay(failed_large,specs[1][1]/'file_base/pcplus_transfer/IRQDATA.BIN','IRQDATA.BIN')
    retained=[]
    for folder,witness,source_key,error,analysis in [
        (failed,'observer-before-trace-fix.py','lab/bbs/test_transfer_dos.py','Empty observed chunk',diagnostic),
        (failed_large,'driver-before-size-fix.py','lab/bbs/enigma_irq_large_dos.py','Expected64.00; displayed64',size_diagnostic)]:
        wrapper=folder.with_name(folder.name+'-wrapper')
        old_input=json.loads((wrapper/'experiment.json').read_text())['input_hashes'][source_key]
        assert sha(wrapper/witness)==old_input
        retained.append(dict(accepted=False,label=folder.name,error=error,diagnostic_replay=analysis,
                             preserved_producer=str((wrapper/witness).relative_to(ROOT)),producer_sha256=old_input))
        for root in (folder,wrapper):
            for path in root.rglob('*'):
                if path.is_file():artifacts[str(path.relative_to(ROOT))]=sha(path)
    popup=ROOT/'build/bbs-lab/results/enigma/irq5-framed-large-transfer-02'
    popup_report=json.loads((popup/'result.json').read_text())
    assert not popup_report['passed']and popup_report['standard_completion']
    assert any('Missing ordered postbatch response'in e for e in popup_report['errors'])
    assert b'ACHIEVEMENT'in(popup/'display.bin').read_bytes()
    popup_diagnostic=replay(popup,specs[1][1]/'file_base/pcplus_transfer/IRQDATA.BIN','IRQDATA.BIN',require_post_menu=False)
    assert not popup_diagnostic['post_menu']
    popup_wrapper=popup.with_name(popup.name+'-wrapper')
    popup_inputs=json.loads((popup_wrapper/'experiment.json').read_text())
    merge(popup_inputs['input_hashes'])
    retained.append(dict(accepted=False,label=popup.name,error='Achievement popup interrupted timed menu inputs',
                         diagnostic_replay=popup_diagnostic))
    for root in (popup,popup_wrapper):
        for path in root.rglob('*'):
            if path.is_file():artifacts[str(path.relative_to(ROOT))]=sha(path)
    with socket.socket()as check:check.bind(('127.0.0.1',23234))
    for name in ['standalone/record_irq_transfers.py','lab/bbs/audit_zmodem.py']:
        merge({name:sha(ROOT/name)})
    counter=json.loads(args.counterexamples.read_text())
    assert counter['passed']and counter['files_unchanged']and len(counter['cases'])==4
    assert all(case['rejected']for case in counter['cases'])
    assert counter['checker_sha256']==sha(ROOT/'standalone/check_irq_transfer_evidence.py')
    assert counter['verifier_sha256']==sha(ROOT/'standalone/record_irq_transfers.py')
    for name,digest in counter['inputs'].items():assert sha(ROOT/name)==digest,name
    merge({'standalone/check_irq_transfer_evidence.py':counter['checker_sha256']})
    result=dict(outcomes_verified=True,compatibility_complete=False,terminal_sha256=sha(terminal),cases=cases,
                sources=sources,artifacts=artifacts,observer_check=observer,
                retained_failures=retained,
                isolated_servers_stopped=True,counterexamples=counter,
                scope='Two actual DOS8086 current-IRQ downloads after editor discard, exact11521/65539 bytes, '
                'CRC/offset/opposite-handshake replay and same-session post-transfer menus. Trace observer fixed without '
                'changing serial bytes. No upload/reconnect, true saturation, physical/card/LAN or full application claim.')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS IRQ transfer receipt:11521 and65539 bytes, handshake replay, post-menu and retained failed pilot')


if __name__=='__main__':main()
