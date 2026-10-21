#!/usr/bin/env python3
"""Reject damaged retained audio/adapter evidence and premature transfer ACKs."""
import argparse,copy,json,struct
from pathlib import Path
from audio_synchronet import ROOT,sha
from audio_synchronet_download import source
from audit_synchronet_reconnect_audio import verify_streams
from audit_audio_download import frontend_trace
from test_transfer_dos import audit_protocol,audit_controls,timestamp
from synthmodem_gateway import records

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    cohort=a.cohort.resolve();out=a.output.resolve()
    assert cohort.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    accepted=json.loads((cohort/'reconnect-audit.json').read_text());assert accepted['passed']
    r=json.loads((cohort/'result.json').read_text())
    decoder=next(h for n,h in r['runtime_inputs'].items() if n.endswith('/src/dsp/protocols/V22Demodulator.js'))
    call=cohort/'call-2';bbs=cohort/'bbs-2';expected=source().read_bytes();cases=[];out.mkdir(parents=True)
    positive=verify_streams(call,bbs,complete=True,decoder_sha=decoder)
    def reject(name,fn):
        try:fn()
        except (AssertionError,ValueError,KeyError,StopIteration) as e:cases.append(dict(case=name,rejected=True,reason=str(e)))
        else:raise AssertionError('Damaged audio reconnect evidence accepted: '+name)
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
    result=dict(passed=True,cases=cases,cohort=str(cohort.relative_to(ROOT)),
        inputs={n:sha(ROOT/n) for n in ('lab/bbs/check_synchronet_reconnect_controls.py','lab/bbs/audit_synchronet_reconnect_audio.py','lab/bbs/test_transfer_dos.py','lab/bbs/audit_audio_download.py')},
        accepted_audit_sha256=sha(cohort/'reconnect-audit.json'),
        scope='Read-only replay of accepted call2 plus isolated damaged symlink-copy fixtures. Missing/extra adapter/audio/Telnet bytes, wrong decoder, missing actual BYE, broken RTP sequence, CRC/source corruption and early/late ACK timing must reject. Original captures remain unchanged; no new DOS/audio execution.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,rejected=len(cases))))

if __name__=='__main__':main()
