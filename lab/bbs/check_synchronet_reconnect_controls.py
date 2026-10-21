#!/usr/bin/env python3
"""Reject damaged retained audio/adapter evidence and premature transfer ACKs."""
import argparse,copy,json,struct
from pathlib import Path
from audio_synchronet import ROOT,sha
from audio_synchronet_download import source
from audit_synchronet_reconnect_audio import verify_streams,verify_stop_boundary,verify_notices
from audit_audio_download import frontend_trace
from test_transfer_dos import audit_protocol,audit_controls,timestamp
from synthmodem_gateway import records
from modem import Telnet

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--diagnostic',action='store_true',help='Use the scoped diagnostic audit; does not accept compatibility');a=p.parse_args()
    cohort=a.cohort.resolve();out=a.output.resolve()
    assert cohort.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    audit=cohort/('reconnect-diagnostic-audit.json' if a.diagnostic else 'reconnect-audit.json')
    accepted=json.loads(audit.read_text())
    if a.diagnostic:assert not accepted['passed'] and accepted['diagnostic_verification_passed'] and accepted['unverified_producer_checks']==['carrier_loss_observed']
    else:assert accepted['passed']
    r=json.loads((cohort/'result.json').read_text())
    decoder=next(h for n,h in r['runtime_inputs'].items() if n.endswith('/src/dsp/protocols/V22Demodulator.js'))
    call=cohort/'call-2';bbs=cohort/'bbs-2';expected=source().read_bytes();cases=[];out.mkdir(parents=True)
    positive=verify_streams(call,bbs,complete=True,decoder_sha=decoder)
    def reject(name,fn):
        try:fn()
        except (AssertionError,ValueError,KeyError,StopIteration) as e:cases.append(dict(case=name,rejected=True,reason=str(e)))
        else:raise AssertionError('Damaged audio reconnect evidence accepted: '+name)
    if not a.diagnostic:
        raw=(cohort/'LABELS.BIN').read_bytes();notices=verify_notices(raw,r['notices'])
        loss=next(i for i,s in enumerate(notices) if 'RX carrier lost' in s or 'Carrier lost' in s)
        complete=next(i for i,s in enumerate(notices) if 'RX complete' in s)
        def rows(indices):
            changed=bytearray(raw[:6]+bytes(2560));struct.pack_into('<H',changed,2,len(indices))
            for index,original in enumerate(indices):changed[6+index*160:6+(index+1)*160]=raw[6+original*160:6+(original+1)*160]
            return bytes(changed),[notices[i] for i in indices]
        for name,indices in [('missing-loss-notice',[complete]),('missing-completion-notice',[loss]),('completion-before-loss',[complete,loss])]:
            damaged,claimed=rows(indices)
            reject(name,lambda damaged=damaged,claimed=claimed:verify_notices(damaged,claimed))
        reject('notice-claims-disagree-with-raw',lambda:verify_notices(raw,notices+['fabricated']))
        reject('truncated-notice-capture',lambda:verify_notices(raw[:-1],notices))
        for name,offset,value in [('wrong-notice-magic',0,0),('empty-notice-count',2,0),('oversized-notice-count',2,17)]:
            damaged=bytearray(raw);struct.pack_into('<H',damaged,offset,value)
            reject(name,lambda damaged=bytes(damaged):verify_notices(damaged,notices))
    def mutate(name,leaf,data,remote=False):
        folder=out/name;folder.mkdir();c=folder/'call';b=folder/'bbs';c.mkdir();b.mkdir()
        for src,dst in ((call,c),(bbs,b)):
            for file in src.iterdir():
                if file.is_file():(dst/file.name).symlink_to(file)
        target=(b if remote else c)/leaf;target.unlink();target.write_bytes(data)
        reject(name,lambda:verify_streams(c,b,complete=True,decoder_sha=decoder))
    mutate('missing-adapter-input-byte','adapter-up.bin',(call/'adapter-up.bin').read_bytes()[:-1])
    mutate('extra-adapter-output-byte','adapter-down.bin',(call/'adapter-down.bin').read_bytes()+b'X')
    mutate('invalid-local-result-prefix','serial-out.bin',b'X'+(call/'serial-out.bin').read_bytes()[1:])
    mutate('extra-decoded-audio-byte','caller-decoded.bin',(call/'caller-decoded.bin').read_bytes()+b'X')
    mutate('extra-Telnet-input-byte','input.bin',(bbs/'input.bin').read_bytes()+b'X',True)
    mutate('extra-Telnet-output-byte','output.bin',(bbs/'output.bin').read_bytes()+b'X',True)
    offline=json.loads((call/'offline-caller.json').read_text());offline['decoder_sha256']='0'*64
    mutate('wrong-offline-decoder','offline-caller.json',json.dumps(offline).encode())
    sip=[v for v in records((call/'sip-to-caller.bin').read_bytes()) if not v.startswith(b'BYE ')]
    mutate('missing-real-SIP-BYE','sip-to-caller.bin',b''.join(struct.pack('<I',len(v))+v for v in sip))
    rtp=bytearray((call/'rtp-from-caller.bin').read_bytes());rtp[4+172+4+3]^=1
    mutate('noncontinuous-actual-RTP','rtp-from-caller.bin',bytes(rtp))
    first=cohort/'call-1'
    first_adapter=json.loads((first/'adapter.json').read_text())
    first_online=(first/'adapter-up.bin').read_bytes()
    first_sent,_=Telnet().feed((cohort/'bbs-1/input.bin').read_bytes())
    partial=r['partials'][0]
    stop=verify_stop_boundary(first_adapter,partial,first_online,first_sent)
    def boundary_damage(name,change):
        adapter=copy.deepcopy(first_adapter);observed=copy.deepcopy(partial)
        change(adapter,observed)
        reject(name,lambda:verify_stop_boundary(adapter,observed,first_online,first_sent))
    def change_claim(adapter,partial,key,value):
        partial['acknowledged_prefix'][key]=value
        next(e for e in adapter['events'] if e['event']=='acknowledged-prefix-before-stop')[key]=value
    boundary_damage('missing-stop-barrier',lambda a,p:a.update(events=[e for e in a['events'] if e['event']!='acknowledged-prefix-before-stop']))
    boundary_damage('duplicate-stop-barrier',lambda a,p:a['events'].append(copy.deepcopy(next(e for e in a['events'] if e['event']=='acknowledged-prefix-before-stop'))))
    boundary_damage('barrier-after-SIGTERM',lambda a,p:next(e for e in a['events'] if e['event']=='acknowledged-prefix-before-stop').update(monotonic_ns=str(stop+1)))
    boundary_damage('partial-after-barrier',lambda a,p:p.update(monotonic_ns=str(stop+1)))
    boundary_damage('partial-before-DSP-CONNECT',lambda a,p:p.update(monotonic_ns=str(int(next(e for e in a['events'] if e['event']=='both-DSP-CONNECT')['monotonic_ns'])-1)))
    boundary_damage('wrong-observed-online-hash',lambda a,p:change_claim(a,p,'online_sha256','0'*64))
    boundary_damage('wrong-observed-BBS-length',lambda a,p:change_claim(a,p,'bbs_online_bytes',len(first_sent)-1))
    reject('inflight-ACK-still-missing',lambda:verify_stop_boundary(first_adapter,partial,first_online,first_sent[:-1]))
    reject('extra-authored-ACK-after-boundary',lambda:verify_stop_boundary(first_adapter,partial,first_online+b'\x06',first_sent))
    sent,display,_,bridge,_,_=positive
    protocol=audit_protocol(display,expected);changed=bytearray(display)
    changed[protocol['frames'][0]['offset']+3]^=1
    reject('CRC-damaged-source-block',lambda:audit_protocol(bytes(changed),expected))
    changed=bytearray(expected);changed[0]^=1
    reject('wrong-expected-source',lambda:audit_protocol(display,bytes(changed)))
    trace,_=frontend_trace(call,sent,display,bridge);end=timestamp(trace,'bbs',protocol['end']-1)
    post=next(v for v in trace if v['direction']=='dos' and v['seconds']>end and b' ' in sent[v['offset']:v['offset']+v['size']])
    audit_controls(protocol,display,sent,trace,'bbs',post['seconds'],ack_timeout=30)
    final=len(sent)-3;first=sent.index(b'\x06')
    for name,offset,when in [('early-final-ACK',final,end-.001),('late-final-ACK',final,post['seconds']+.001),
            ('early-block-ACK',first,timestamp(trace,'bbs',protocol['frames'][0]['end']-1)-.001)]:
        altered=[]
        for row in trace:
            start=row['offset'];stop=start+row['size']
            if row['direction']!='dos' or not start<=offset<stop:altered.append(dict(row));continue
            if start<offset:altered.append(dict(row,size=offset-start))
            altered.append(dict(row,offset=offset,size=1,seconds=when))
            if offset+1<stop:altered.append(dict(row,offset=offset+1,size=stop-offset-1))
        reject(name,lambda:audit_controls(protocol,display,sent,altered,'bbs',post['seconds'],ack_timeout=30))
    result=dict(passed=True,diagnostic=a.diagnostic,compatibility_accepted=False,cases=cases,cohort=str(cohort.relative_to(ROOT)),
        inputs={n:sha(ROOT/n) for n in ('lab/bbs/check_synchronet_reconnect_controls.py','lab/bbs/audit_synchronet_reconnect_audio.py','lab/bbs/test_transfer_dos.py','lab/bbs/audit_audio_download.py')},
        accepted_audit_sha256=sha(audit),
        scope='Read-only replay of accepted call2 plus isolated damaged symlink-copy fixtures, mandatory loss/completion notices and interrupted-call stop-boundary controls. Missing/reversed/invalid notices, missing/extra adapter/audio/Telnet bytes, wrong decoder, missing actual BYE, broken RTP sequence, missing/duplicate/late stop barriers, changed observed prefixes, CRC/source corruption and early/late ACK timing must reject. Original captures remain unchanged; no new DOS/audio execution.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,rejected=len(cases))))

if __name__=='__main__':main()
