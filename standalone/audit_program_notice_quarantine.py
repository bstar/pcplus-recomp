#!/usr/bin/env python3
"""Seal retained window/stream ownership, rejected retries and repaired VM reuse."""
import argparse,hashlib,itertools,json,re,shutil,struct,sys
from pathlib import Path
from omf_imports import records,externals,rename_imports
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['dos','regression','errors','parent','source-proof','cohort','output']:parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();folders=[p.resolve() for p in [a.dos,a.regression,a.errors,a.parent,a.source_proof]];dos,regression,errors,parent,fresh=folders
    cohort=a.cohort.resolve();output=a.output.resolve();assert all(p.is_relative_to(ROOT/'build') for p in [*folders,cohort]) and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    q,b,e,p,f=[read(folder/'result.json') for folder in folders];assert all(r['passed'] for r in [q,b,e,p,f])
    assert len(q['cases'])==12 and len(b['cases'])==14 and len(e['cases'])==10 and len(p['cases'])==13
    assert {(r['ownership'],r['port'],r['flow'],r['mode']) for r in q['cases']}=={(o,port,flow,m) for o in ['guard','foreign'] for port,flow in [(1,'H'),(2,'B')] for m in ['2D','2A','2F']}
    assert {(r['port'],r['flow'],r['mode']) for r in b['cases']}=={(port,flow,'0N') for port,flow in itertools.product([1,2],'NSHB')}|{(1,'H',m) for m in ['1D','2D','3D','2A','2F']}|{(2,'B','2F')}
    assert {(r['error'],r['port'],r['flow']) for r in e['cases']}=={(error,port,flow) for error in ['missing','longtail','format','memory','generic'] for port,flow in [(1,'H'),(2,'B')]}
    for aggregate,checker in [(q,'test_program_notice_quarantine_dos.py'),(e,'test_program_notice_errors_dos.py')]:assert aggregate['checker_sha256']==sha(ROOT/'standalone'/checker)
    selected={Path(__file__),ROOT/'standalone/test_program_notice_quarantine_dos.py',ROOT/'standalone/test_program_notice_errors_dos.py',ROOT/'standalone/prove_program_notices_source.py'}
    groups=[b]
    for aggregate,root in [(q,dos),(e,errors)]:
        for row in aggregate['cases']:
            path=ROOT/row['result'];assert path.is_relative_to(root) and row['passed'] and sha(path)==row['result_sha256']
            report=read(path);assert report['passed'] and len(report['cases'])==1;groups.append(report)
    identity=read(ROOT/'build/aspect-notice-fault/manifest.json')['binary_sha256'];assert sha(ROOT/'build/aspect-notice-fault/ASPECT.EXE')==identity
    payload=bytes(i for i in range(256) if i not in (17,19))*2;checked=[]
    definitions={'missing':(2,2),'longtail':(7,10),'format':(8,11),'memory':(12,8),'generic':(13,5)}
    sys.path.insert(0,str(ROOT/'src/aspect'))
    from compiler import compile_source
    for group in groups:
        assert group['binary_sha256']==identity
        for name,h in group['sources'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
        for row in group['cases']:
            folder=ROOT/row['folder'];assert any(folder.is_relative_to(root) for root in [dos,regression,errors])
            assert row['passed'] and all(row['checks'].values()) and sha(folder/'ASPECT.EXE')==identity
            for name,h in row['captures_sha256'].items():assert sha(folder/name)==h
            w=struct.unpack('<62H',(folder/'NOTICE.BIN').read_bytes());assert list(w)==row['report_words']
            ownership=row['quarantine'];guard=ownership=='guard';phase=int(row['mode'][0]);success=row['successful_child'];crt,de=definitions[row['error']]
            error=0 if not phase else 5 if row['mode'][1]=='A' else 12
            assert w[:7]==(0x4e46,phase,1 if row['mode'][1]=='A' else 2 if row['mode'][1]=='F' else 0,int(bool(phase)),error,1,crt)
            assert w[7] in ([10] if ownership and guard else [9] if phase==2 else [0,1,2])
            assert w[8:11]==((5 if guard else 0,0,0) if ownership else (0,1,1))
            assert w[11:18]==(int(phase!=1),0 if phase==1 else 508,508,1,65535,int(bool(phase)),1)
            recoveries=3 if ownership else int(bool(phase))
            assert w[18:20]==(0,2) and w[20] in [0,1,2] and w[21:29]==(0,1,1,1,0 if success else 65535,recoveries,1,error)
            assert w[29:32]==((0,0,de) if success else (2,2,de)) and w[35]==int(row['error']!='longtail') and w[36]==w[35]+1+int(success)
            if ownership:
                count=1 if guard else 2
                assert w[37:44]==(1 if guard else 2,1,1,6,1,1 if guard else 0,2 if guard else 1)
                assert w[44:56]==(9,10,1,1,10,10,0,0,1,1,1,0)
                assert w[56:62]==(count,count,9,count+1,count+1,0)
            else:
                assert not any(w[37:59]) and w[59:62]==(1 if phase==1 else 2,1 if phase==1 else 2,0)
            assert (folder/'SUCCESS.OK').exists()==success
            if success:assert (folder/'SUCCESS.OK').read_bytes()==b'OK'
            assert (folder/'WRITE.BIN').read_bytes()==b'FIRSTSECOND'
            for name in ['FIRST','RECOVER']:assert (folder/(name+'.ASX')).read_bytes()==compile_source((folder/(name+'.ASP')).read_text())
            peer=read(folder/'peer.json');events=peer['events'];assert not peer['errors'] and events[-1]['kind']=='EOF' and sum(x['kind']=='EOF' for x in events)==1
            assert all(x['seconds']<=y['seconds'] for x,y in zip(events,events[1:]))
            soft=row['flow'] in 'SB';wire=b''.join(bytes.fromhex(x['hex']) for x in events if x['kind']=='receive')
            assert wire==(folder/'wire.bin').read_bytes()==(b'\x11R'+b'\x13\x11'*(2+int(success))+b'PF\x13' if soft else b'RPF')
            assert [bytes.fromhex(x['hex']) for x in events if x['kind']=='send']==[(b'\x13'+payload+b'\x11') if soft else payload,b'READY!',b'END']
            checked.append(dict(ownership=ownership,port=row['port'],flow=row['flow'],mode=row['mode'],error=row['error'],private_streams_retained=w[40],failed_retry=w[45],live_retry=w[48],VM_reuse_attempt=w[49],successful_retry=w[51],recovery_count=w[26],allocations=w[59],frees=w[60],wire_sha256=sha(folder/'wire.bin')))
    assert p['child_sha256']==sha(ROOT/'build/aspect-notice-parent/ASPECT.EXE') and all(row['passed'] and all(row['checks'].values()) for row in p['cases'])
    for name,h in p['source_hashes'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
    assert f['original_inputs']==[] and f['source_files']==len(f['inputs'])==237 and len(f['products'])==35
    assert f['checker_sha256']==sha(ROOT/'standalone/prove_program_notices_source.py')
    for name,h in f['inputs'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
    for name,h in f['products'].items():assert sha(ROOT/name)==h
    for name,h in f['manifests'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
    # Verify both parent-specific OMF rewrites independently; rename_imports
    # proves every non-EXTDEF record, type index and fixup remains exact.
    sharing=[];aliases={'_notice_bank_int86':'_program_bank_int86','_notice_bank_memset':'_program_bank_memset'}
    maps={}
    for name in ['aspect-notice-parent','aspect-notice-fault']:
        base=ROOT/'build'/name;path=base/'ASPECT.map';text=path.read_text();selected.add(path)
        symbols={symbol:int(seg,16) for seg,off,symbol in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',text,re.M|re.I)}
        assert symbols['_program_bank_int86']==symbols['_program_bank_memset']==symbols['main_']
        assert '_notice_bank_int86' not in symbols and '_notice_bank_memset' not in symbols
        for unit in ['owner-normal','runtime']:
            original=ROOT/'build/notice-bank'/('owner.obj' if name.endswith('fault') and unit=='owner-normal' else unit+'.obj')
            blob=original.read_bytes();imports={n.decode() for kind,body,_ in records(blob) if kind==0x8c for n,_ in externals(body)}
            wanted,counts=rename_imports(blob,{a:b for a,b in aliases.items() if a in imports});target=base/('notice-shared-'+unit+'.obj')
            assert target.read_bytes()==wanted;sharing.append(dict(object=str(target.relative_to(ROOT)),sha256=sha(target),imports=counts));selected.add(target);selected.add(original)
        segment=re.search(r'^_TEXT\s+CODE\s+\S+\s+[0-9a-f]+:([0-9a-f]+)\s+([0-9a-f]+)',text,re.M|re.I)
        maps[name]=65536-int(segment[1],16)-int(segment[2],16);assert maps[name]>0
    for root in folders:selected.update(path for path in root.rglob('*') if path.is_file())
    cohort.mkdir();kept={}
    for path in sorted(selected):
        dest=cohort/'accepted'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        assert sha(path)==sha(dest);kept[str(dest.relative_to(ROOT))]=sha(dest)
    result=dict(passed=True,selected_window_quarantine_retry_accepted=True,full_PROGRAM_policy_accepted=False,full_application_accepted=False,quarantine_sessions=12,popup_and_error_regressions=24,attached_parent_workflows=13,source_files=237,source_products=f['products'],shared_bridge_objects=sharing,near_CODE_spare=maps,cases=checked,custody_sha256=kept,auditor_sha256=sha(Path(__file__)),scope='Bad snapshot guards and foreign replacement windows retain program/window, six script streams and the invocation file across real DIV/foreign-DS DIV/typed abort. Live retry and fresh VM entry reject; a failed stopped-owner retry preserves the exact displayed window. Repair then retires the private JFT/streams, keeps the original notice cause and permits another popup, successful child and exact508-byte peer exchange.12 DOS8086 COM1/HARD and COM2/BOTH cases,24 popup/error regressions and13 attached normal workflows pass;237 sources reproduce35 products. Attached-parent quarantine/fault observation, natural malformed-executable rejection, complete sound/macros/mouse/UI, other views, BBS and physical requirements stay open.')
    with output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ['passed','quarantine_sessions','popup_and_error_regressions','attached_parent_workflows','source_files']}))
if __name__=='__main__':main()
