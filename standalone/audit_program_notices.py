#!/usr/bin/env python3
"""Seal PROGRAM popup, synchronous outer-fault recovery and source-only evidence."""
import argparse,hashlib,itertools,json,re,shutil,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['dos','parent','source-proof','component','near-component','near-source','checkpoint','cohort','output']:parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();folders=[a.dos.resolve(),a.parent.resolve(),a.source_proof.resolve(),a.component.resolve(),a.near_component.resolve(),a.near_source.resolve(),a.checkpoint.resolve()];dos,parent,fresh,component,near,near_source,checkpoint=folders
    cohort=a.cohort.resolve();output=a.output.resolve();assert all(p.is_relative_to(ROOT/'build') for p in [*folders,cohort]) and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    reports=[read(folder/'result.json') for folder in folders];assert all(r['passed'] for r in reports)
    d,p,f,c,n,ns,k=reports;selected={Path(__file__)};sources={}
    bases=['build/aspect-notice-parent','build/aspect-notice-fault'];identities={};placement=[]
    for base in bases:
        folder=ROOT/base;m=read(folder/'manifest.json');assert m['original_inputs']==[] and m['experimental_notice_error_binding'] and not m['production_dispatch_changed']
        assert sha(folder/'ASPECT.EXE')==m['binary_sha256'];identities[base]=m['binary_sha256'];selected.update([folder/'ASPECT.EXE',folder/'manifest.json',folder/'ASPECT.map'])
        for name,h in m['sources'].items():assert sha(ROOT/name)==h;sources[name]=h
        text=(folder/'ASPECT.map').read_text();symbols={name:int(seg,16) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',text,re.M|re.I)}
        assert symbols['_notice_show']==symbols['_program_notice_error']==symbols['_notice_unwind']==symbols['_program_notice_unwind']
        assert symbols['_notice_show']!=symbols['main_']==symbols['_program_notice_callback']
        seg=re.search(r'^_TEXT\s+CODE\s+\S+\s+[0-9a-f]+:([0-9a-f]+)\s+([0-9a-f]+)',text,re.M|re.I);spare=65536-int(seg[1],16)-int(seg[2],16);assert spare>0
        placement.append(dict(product=base,near_CODE_spare=spare))
    assert d['binary_sha256']==identities['build/aspect-notice-fault'] and len(d['cases'])==14
    expected={(port,flow,'0N') for port,flow in itertools.product([1,2],'NSHB')}|{(1,'H',mode) for mode in ['1D','2D','3D','2A','2F']}|{(2,'B','2F')}
    assert {(r['port'],r['flow'],r['mode']) for r in d['cases']}==expected
    payload=bytes(i for i in range(256) if i not in (17,19))*2;rows=[]
    sys.path.insert(0,str(ROOT/'src/aspect'))
    from compiler import compile_source
    for row in d['cases']:
        assert row['passed'] and all(row['checks'].values());folder=ROOT/row['folder'];assert folder.is_relative_to(dos)
        for name,h in row['captures_sha256'].items():assert sha(folder/name)==h
        assert sha(folder/'ASPECT.EXE')==d['binary_sha256']
        raw=(folder/'NOTICE.BIN').read_bytes();assert len(raw) in [58,74,124]
        words=struct.unpack('<'+str(len(raw)//2)+'H',raw);assert list(words)==row['report_words']
        phase=int(row['mode'][0]);kind={'N':0,'D':0,'A':1,'F':2}[row['mode'][1]];error=0 if not phase else 5 if kind==1 else 12
        assert words[:7]==(0x4e46,phase,kind,int(bool(phase)),error,1,2)
        assert words[7] in ([9] if phase==2 else [0,1,2]) and words[8:11]==(0,1,1)
        assert words[11:18]==(int(phase!=1),0 if phase==1 else 508,508,1,65535,int(bool(phase)),1)
        assert words[18:20]==(0,2) and words[20] in [0,1,2] and words[21:29]==(0,1,1,1,65535,int(bool(phase)),1,error)
        assert (folder/'WRITE.BIN').read_bytes()==b'FIRSTSECOND' and all((folder/f'SLOT{i}.BIN').read_bytes()==b'SEED0' for i in range(5))
        for name in ['FIRST','RECOVER']:assert (folder/(name+'.ASX')).read_bytes()==compile_source((folder/(name+'.ASP')).read_text())
        peer=read(folder/'peer.json');events=peer['events'];assert not peer['errors'] and events[-1]['kind']=='EOF' and sum(e['kind']=='EOF' for e in events)==1
        assert all(x['seconds']<=y['seconds'] for x,y in zip(events,events[1:]))
        wire=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive');soft=row['flow'] in 'SB'
        assert wire==(folder/'wire.bin').read_bytes()==(b'\x11R'+b'\x13\x11'*2+b'PF\x13' if soft else b'RPF')
        assert [bytes.fromhex(e['hex']) for e in events if e['kind']=='send']==[(b'\x13'+payload+b'\x11') if soft else payload,b'READY!',b'END']
        config=(folder/'dosbox.conf').read_text();assert 'cputype=8086' in config and f"set PCPNOTICE={row['mode']}{row['port']}" in config
        rows.append(dict(port=row['port'],flow=row['flow'],mode=row['mode'],raw_first=words[15],raw_second=words[25],first_notice_status=words[7],retained_first=words[12],retained_second=words[13],wire_sha256=sha(folder/'wire.bin')))
    for name,h in d['sources'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
    assert p['child_sha256']==identities['build/aspect-notice-parent'] and len(p['cases'])==13 and all(r['passed'] and all(r['checks'].values()) for r in p['cases'])
    for name,h in p['source_hashes'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
    assert f['original_inputs']==[] and f['source_files']==len(f['inputs'])==236 and len(f['products'])==35
    assert f['checker_sha256']==sha(ROOT/'standalone/prove_program_notices_source.py')
    selected.add(ROOT/'standalone/prove_program_notices_source.py')
    for name,h in f['inputs'].items():
        assert sha(ROOT/name)==h
        if name in sources:assert sources[name]==h
        sources[name]=h
    for name,h in f['products'].items():assert sha(ROOT/name)==h
    for name,h in f['manifests'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
    assert c['assertions']==n['assertions']==583 and c['allocations']==c['frees']==n['allocations']==n['frees']==69
    assert sha(component/'NOTICE.EXE')==f['products']['build/notice-bank/NOTICE.EXE']
    assert ns['source_files']==64 and len(ns['products'])==33
    for name,h in ns['products'].items():assert sha(ROOT/name)==h
    assert sha(near/'NOTICE.EXE')==ns['products']['build/notice/NOTICE.EXE']
    assert k['bank_segment']!=k['callback_segment'] and (checkpoint/'OUTPUT.TXT').read_text().strip()=='CHECKPOINT PASS 2048 calls 2048 far callbacks'
    for folder,report in [(component,c),(near,n),(checkpoint,k)]:
        assert all(report['checks'].values())
        for name,h in report['inputs'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
        for name,h in report['captures_sha256'].items():assert sha(folder/name)==h
    for name,h in ns['inputs'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
    selected.update(ROOT/name for name in sources)
    for folder in folders:selected.update(path for path in folder.rglob('*') if path.is_file())
    cohort.mkdir();kept={}
    for path in sorted(selected):
        dest=cohort/'accepted'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        assert sha(path)==sha(dest);kept[str(dest.relative_to(ROOT))]=sha(dest)
    result=dict(passed=True,selected_PROGRAM_notice_binding_accepted=True,outer_synchronous_notice_recovery_accepted=True,full_PROGRAM_policy_accepted=False,normal_dispatch_changed=False,full_application_accepted=False,DOS_cases=14,retained_payload_bytes_per_session=508,attached_parent_workflows=13,component_DOS_assertions=583,near_regression_DOS_assertions=583,checkpoint_cases=2048,source_files=236,source_only_products=f['products'],near_source_files=64,near_source_products=ns['products'],placement=placement,cases=rows,custody_sha256=kept,source_inputs=sources,auditor_sha256=sha(Path(__file__)),scope='Experimental PROGRAM error2 presentation preserves FFFF raw status and live transport.14 actual8086 DOS socket-peer sessions cover COM1/2 and all flow settings plus before/during/after notices, foreign-DS DIV and native typed abort. A second VM invocation shows another popup then consumes508 exact peer bytes. Probe records video/cursor, PSP/JFT/IVT and owner cleanup;13 attached PROGRAM workflows pass.236 source files reproduce35 products without originals. Error7/8/12/generic actual DOS fixtures, attached-parent popup fault observation, corrupted-window quarantine, original sound/macros/mouse, broader geometries, BBS and physical acceptance remain open.')
    with output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ['passed','DOS_cases','attached_parent_workflows','source_files']}))
if __name__=='__main__':main()
