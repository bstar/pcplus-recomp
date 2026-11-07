#!/usr/bin/env python3
"""Independent current-image DCD loss/redial/retry and raw-proxy capture audit."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
from product_inputs import ROOT,sha,select_product,companions
from audit_zmodem import scan,packet,metadata,audit_batch,audit_controls
from test_transfer_dos import timestamp,offset_after
from audit_size_probe_screen import telnet
from test_proxy_carrier_dos import keyboard_source
from carrier_notice_watch import SAMPLER
from directory_test_support import accounting_check
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('capture','bridge','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();cap,bridge,out=[v.resolve() for v in (a.capture,a.bridge,a.output)]
    assert all(v.is_relative_to(ROOT/'build') for v in (cap,bridge,out));out.mkdir(parents=True,exist_ok=False)
    r=json.loads((cap/'carrier-checks.json').read_text());assert r['passed'] and all(r['checks'].values()) and not r['errors']
    for n,h in r['sources'].items():assert sha(ROOT/n)==h,n
    for leaf,product in r['products'].items():assert sha(cap/'program'/leaf)==sha(ROOT/product['path'])==product['sha256']
    parent=r['products']['TERMINAL.EXE'];manifest=json.loads((ROOT/parent['path']).with_name('manifest.json').read_text())
    selected,source_inputs=select_product(ROOT/parent['path'],'TERMINAL.EXE')
    assert sha(selected)==parent['sha256']
    modules=companions(selected)
    assert not manifest.get('original_inputs') and len(manifest['sources'])==parent['source_files']==len(source_inputs)-2-len(modules)
    for module in modules:assert sha(cap/'program'/module.name)==sha(module)
    assert manifest['memory_layout']['resident_CS_extent_bytes']<=65536
    assert (cap/'PASS.TXT').exists() and not (cap/'FAIL.TXT').exists()
    before=(cap/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(cap/'AFTER.BIN').read_bytes()
    assert len((cap/'SCREEN.BIN').read_bytes())==8000 and not list(cap.rglob('PCRX.$$$'))
    config=(cap/'dosbox.conf').read_text();assert 'cputype=8086' in config and 'serial3=modem irq:5 listenport:0' in config
    assert config.count('TERMINAL @D:')==1
    log=(cap/'dosbox.log').read_text();assert log.count('Modem response: CONNECT')==2 and 'Modem response: NO CARRIER' in log
    assert log.count('Command sent to modem: ->AT&K3S12=25<-')==2
    assert (cap/'TEST.PRM').read_bytes()==(cap/'START.PRM').read_bytes()
    assert accounting_check((cap/'START.DIR').read_bytes(),(cap/'TEST.DIR').read_bytes(),3,2)
    assert (cap/'program/LOGIN.LOG').read_bytes()==b'STARTAUTHREADY'
    script=(cap/'program/LOGON.ASP').read_bytes().decode('ascii').replace('\r\n','\n')
    assert script.count('transmit "loc^M"')==1 and (cap/'program/LOGON.ASX').read_bytes()==compile_source(script)
    recipe=json.loads((cap/'recipe.json').read_text())['recipe']
    assert recipe.count('browser tab D')==1 and (cap/'KEYS.ASM').read_text()==keyboard_source(recipe)
    subprocess.run(['nasm','-fbin',str(cap/'KEYS.ASM'),'-o',str(out/'PACED.COM')],check=True)
    assert sha(out/'PACED.COM')==sha(cap/'PACED.COM')
    sampler=SAMPLER.replace('mov cx,4000','mov cx,8000')
    if r.get('guard_observer'):
        from carrier_key_observer import build,decode
        sampler,guard=build(selected,out/'guard-observer')
        assert guard['observer_sha256']==r['guard_observer']['observer_sha256']
        assert guard['retained_bytes']==guard['baseline_retained_bytes']==r['guard_observer']['retained_bytes']
        assert decode(cap/'LABELS.BIN')==r['guard_observer']['trace']
        assert r['guard_observer']['trace']['int16_restored']
        proof=r['guard_observer']['transparency_report'];proof_path=(ROOT/proof['path']).resolve()
        assert proof_path.is_relative_to(ROOT/'build') and sha(proof_path)==proof['sha256']
        control=json.loads(proof_path.read_text());assert control['passed']
        assert control['observer']['observer_sha256']==guard['observer_sha256']
        for n,h in control['sources'].items():assert sha(ROOT/n)==h,n
    for off in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+off),hex(0x3e8+off))
    assert sampler==(cap/'sampler.asm').read_text()
    subprocess.run(['nasm','-fbin',str(cap/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
    assert sha(out/'SNAP.COM')==sha(cap/'SNAP.COM')
    labels=(cap/'LABELS.BIN').read_bytes();magic,count,ticks=struct.unpack_from('<3H',labels)
    capacity=r['guard_observer']['video_capacity'] if r.get('guard_observer') else 16
    assert len(labels)==2566 and magic==0x4e5a and 0<count<=capacity
    notices=[labels[6+i*160:6+(i+1)*160:2].decode('cp437') for i in range(count)]
    assert notices==r['notices'] and any('carrier lost' in n.lower() for n in notices) and any('RX complete' in n for n in notices)
    geom=struct.unpack('<4H',(cap/'GEOM.BIN').read_bytes());assert (geom[0],geom[1],geom[2],geom[3]>>8)==(25,16,0x5003,0)
    name=r['payload_name'];payload=(cap/'RECV'/name).read_bytes()
    assert len(payload)==65539 and hashlib.sha256(payload).hexdigest()==r['payload_sha256']
    assert set(payload)==set(range(256)) and payload.count(b'\x1b[8;50;80t')==215
    assert {p.name for p in (cap/'RECV').iterdir()}=={name}
    snapshots=json.loads((cap/'snapshots.json').read_text());assert snapshots==r['snapshots'] and len(snapshots)==2
    part,clean=snapshots;assert part['kind']=='partial-before-drop' and 4096<=part['bytes']<len(payload)
    assert part['sha256']==hashlib.sha256(payload[:part['bytes']]).hexdigest() and part['first_login_trace']=='STARTAUTHREADY'
    assert clean['kind']=='before-second-login' and clean['files']==[]
    sessions=[]
    for index in (1,2):
        path=cap/('connection-'+str(index));s=json.loads((path/'session.json').read_text())
        assert s['raw'] and s['done'] and not s['errors'] and s['interrupted']==(index==1)
        stream=(path/'display.bin').read_bytes();keys=(path/'serial-received.bin').read_bytes();wire=(path/'upstream.bin').read_bytes()
        online=(bridge/(str(index)+'-serial-input.bin')).read_bytes();output=(bridge/(str(index)+'-serial-output.bin')).read_bytes()
        if index==1:
            assert keys.startswith(online) or online.startswith(keys)
            assert output.startswith(wire) and wire.startswith(stream)
            assert part['relay_seconds']<=s['interrupted_at']
            offers=[h for h in scan(stream) if h['type']==4];assert len(offers)==1
            assert metadata(packet(stream,offers[0]['end'],offers[0]['format'])['payload'])==(name,len(payload))
            assert not any(h['type']==11 for h in scan(stream))
        else:
            assert online==keys and output==wire==stream
            retry=audit_batch(stream,{name:payload})
            trace=json.loads((path/'trace.json').read_text());end=timestamp(trace,'bbs',retry['end']-1)
            cut=offset_after(trace,'dos',end);assert cut is not None
            post=keys.index(b'\x1b\x1bS\r',cut)+2;when=timestamp(trace,'dos',post)
            controls=audit_controls(retry,keys,trace,'bbs',when,False)
            assert controls==r['protocol']['controls'] and retry['finish']
            tail=offset_after(trace,'bbs',when);assert tail is not None and (name+' ').encode() in stream[tail:]
        client,subs,_=telnet((bridge/(str(index)+'-telnet-input.bin')).read_bytes())
        prefix=b'loc\r\x1b[8;24;80t';assert online.startswith(prefix)
        if index==1:assert client==online[len(prefix):]
        else:
            # QUIT belongs to the returned bridge menu, not the BBS. Exclude
            # exactly that final command, after proving the observed return.
            assert online.endswith(b'QUIT\r') and client==online[len(prefix):-5]
            returned=stream.index(b'Connection closed by remote host.')
            assert b'CONNECT> ' in stream[returned:] and b'Goodbye.' in stream[returned:]
            assert timestamp(trace,'bbs',returned)<timestamp(trace,'dos',len(keys)-5)
            assert b'+++ATH\r' not in keys
        assert [list(struct.unpack('>HH',v[1:])) for v in subs if v[0]==31]==[[80,24]]
        assert json.loads((bridge/(str(index)+'-closed.json')).read_text())['source_unchanged']
        sessions.append(dict(index=index,interrupted=s['interrupted'],NAWS=[80,24],delivered_bytes=len(stream),proxy_bytes=len(output),online_bytes=len(online)))
    assert len(list(bridge.glob('*-closed.json')))==2
    rows=[json.loads(line) for line in (cap/'server-session.jsonl').read_text().splitlines()]
    marker=json.loads((cap/'server-log-start.json').read_text())
    uses_journal='lab/bbs/bbs_log_capture.py' in r['sources']
    if uses_journal:
        assert 'device' in marker
        journal=json.loads((cap/'server-log-capture/result.json').read_text())
        assert journal['passed'] and journal['boundary']==marker and journal['boundary_sha256']==sha(cap/'server-log-start.json')
        captured=[]
        for index,segment in enumerate(journal['segments']):
            assert segment['capture']==f'segment-{index:04}.jsonl'
            body=(cap/'server-log-capture'/segment['capture']).read_bytes()
            assert hashlib.sha256(body).hexdigest()==segment['sha256'] and len(body)==segment['end']-segment['start']
            assert not body or body.endswith(b'\n')
            captured.extend(json.loads(line) for line in body.splitlines() if line.strip())
        assert len(captured)==journal['records'] and all(isinstance(r,dict) for r in captured)
        authenticated={r['sessionId'] for r in captured if r.get('msg')=='User "loclab" successfully logged in'}
        assert rows==[r for r in captured if r.get('sessionId') in authenticated]
    auth=[r for r in rows if r.get('msg')=='User "loclab" successfully logged in'];assert len(auth)==2 and len({r['sessionId'] for r in auth})==2
    for index,row in enumerate(auth):
        own=[r for r in rows if r['sessionId']==row['sessionId']]
        exits=[r.get('exitCode') for r in own if r.get('msg')=='Process exited']
        assert len(exits)==1 and ((exits[0]!=0) if index==0 else exits[0]==0)
    captures=[p for p in cap.rglob('*') if p.is_file()]+[p for p in bridge.glob('*') if p.is_file()]
    sources=['lab/bbs/audit_proxy_carrier.py','lab/bbs/test_proxy_carrier_dos.py','lab/bbs/proxy_carrier_relay.py','lab/bbs/bbs_log_capture.py',
        'lab/bbs/audit_zmodem.py','lab/bbs/test_transfer_dos.py','lab/bbs/audit_size_probe_screen.py',
        'lab/bbs/paced_bios_keys.py','lab/bbs/carrier_notice_watch.py','lab/bbs/zmodem_label_watch.py','standalone/directory_test_support.py']
    if r.get('guard_observer'):sources+=list(n for n in control['sources'] if n not in sources)
    result=dict(passed=True,terminal_sha256=parent['sha256'],products=r['products'],partial_disk_bytes=part['bytes'],
        exact_retry_bytes=len(payload),payload_sha256=r['payload_sha256'],sessions=sessions,notices=notices,
        sources={n:sha(ROOT/n) for n in sources},captures={str(p.relative_to(ROOT)):sha(p) for p in captures},
        scope=__doc__+' One8086 parent,actual built-in modem DCD,socket abort after source-prefix write,cleanup before second login,two source-built ASPECT logins and DOS compiler equivalence,actual NAWS,raw byte prefixes at loss/exact second streams,CRC/finish/controls and exact retry. No physical/SIP/DSP or all-layout/protocol acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS independent carrier loss/redial:',len(payload),'exact bytes')


if __name__=='__main__':main()
