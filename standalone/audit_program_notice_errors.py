#!/usr/bin/env python3
"""Seal all PROGRAM message branches and successful post-error EXEC evidence."""
import argparse,hashlib,itertools,json,re,shutil,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['errors','regression','source-proof','cohort','output']:parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();errors,regression,fresh=[p.resolve() for p in [a.errors,a.regression,a.source_proof]];cohort=a.cohort.resolve();output=a.output.resolve()
    assert all(p.is_relative_to(ROOT/'build') for p in [errors,regression,fresh,cohort]) and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    matrix=read(errors/'result.json');baseline=read(regression/'result.json');proof=read(fresh/'result.json')
    assert matrix['passed'] and baseline['passed'] and proof['passed'] and len(matrix['cases'])==10 and len(baseline['cases'])==14
    assert matrix['checker_sha256']==sha(ROOT/'standalone/test_program_notice_errors_dos.py')
    assert {(r['error'],r['port'],r['flow']) for r in matrix['cases']}=={(e,p,f) for e in ['missing','longtail','format','memory','generic'] for p,f in [(1,'H'),(2,'B')]}
    assert {(r['port'],r['flow'],r['mode']) for r in baseline['cases']}=={(p,f,'0N') for p,f in itertools.product([1,2],'NSHB')}|{(1,'H',m) for m in ['1D','2D','3D','2A','2F']}|{(2,'B','2F')}
    current=read(ROOT/'build/aspect-notice-fault/manifest.json');identity=current['binary_sha256']
    assert sha(ROOT/'build/aspect-notice-fault/ASPECT.EXE')==identity
    cohort.mkdir();selected={Path(__file__),ROOT/'standalone/test_program_notice_errors_dos.py',ROOT/'standalone/prove_program_notices_source.py'}
    child=cohort/'SUCCESS.COM';subprocess.run(['nasm','-fbin',str(ROOT/'standalone/notice_success_child.asm'),'-o',str(child)],check=True);child_hash=sha(child)
    sys.path.insert(0,str(ROOT/'src/aspect'))
    from compiler import compile_source
    payload=bytes(i for i in range(256) if i not in (17,19))*2
    definitions={'missing':(2,2),'longtail':(7,10),'format':(8,11),'memory':(12,8),'generic':(13,5)}
    groups=[baseline]
    for row in matrix['cases']:
        path=ROOT/row['result'];assert path.is_relative_to(errors) and row['passed'] and sha(path)==row['result_sha256']
        part=read(path);assert part['passed'] and len(part['cases'])==1;groups.append(part)
    checked=[]
    for group in groups:
        assert group['binary_sha256']==identity and all(sha(ROOT/name)==h for name,h in group['sources'].items())
        selected.update(ROOT/name for name in group['sources'])
        for row in group['cases']:
            folder=ROOT/row['folder'];assert folder.is_relative_to(errors) or folder.is_relative_to(regression)
            assert row['passed'] and all(row['checks'].values()) and sha(folder/'ASPECT.EXE')==identity
            for name,h in row['captures_sha256'].items():assert sha(folder/name)==h
            raw=(folder/'NOTICE.BIN').read_bytes();assert len(raw) in [74,124]
            w=struct.unpack('<'+str(len(raw)//2)+'H',raw);assert list(w)==row['report_words']
            phase=int(row['mode'][0]);success=row['successful_child'];error=row['error'];crt,dos=definitions[error]
            expected_status=0 if not phase else 5 if row['mode'][1]=='A' else 12
            assert w[0]==0x4e46 and w[1]==phase and w[3]==int(bool(phase)) and w[4]==w[28]==expected_status
            assert w[5:7]==(1,crt) and w[7] in ([9] if phase==2 else [0,1,2])
            assert w[8:11]==(0,1,1) and w[11:16]==(int(phase!=1),0 if phase==1 else 508,508,1,65535)
            assert w[16:20]==(int(bool(phase)),1,0,2) and w[20] in [0,1,2]
            assert w[21:25]==(0,1,1,1) and w[25:29]==(0 if success else 65535,int(bool(phase)),1,expected_status)
            assert w[29:32]==((0,0,dos) if success else (2,2,dos))
            assert w[35]==int(error!='longtail') and w[36]==w[35]+1+int(success)
            if error=='memory':assert w[32]>32 and w[33:35]==(0,0)
            else:assert w[32:35]==(0,0,0)
            assert sha(folder/'SUCCESS.COM')==child_hash
            assert (folder/'SUCCESS.OK').exists()==success
            if success:assert (folder/'SUCCESS.OK').read_bytes()==b'OK'
            assert not list(folder.rglob('EXECUTED.BAD'))
            assert (folder/'WRITE.BIN').read_bytes()==b'FIRSTSECOND' and all((folder/f'SLOT{i}.BIN').read_bytes()==b'SEED0' for i in range(5))
            for name in ['FIRST','RECOVER']:assert compile_source((folder/(name+'.ASP')).read_text())==(folder/(name+'.ASX')).read_bytes()
            assert 'putenv "PATH="' in (folder/'FIRST.ASP').read_text() and 'putenv "PATH="' in (folder/'RECOVER.ASP').read_text()
            if error=='longtail':assert len('ROUTE '+'A'*60)<82 and 'A'*60 in (folder/'FIRST.ASP').read_text()
            peer=read(folder/'peer.json');events=peer['events'];assert not peer['errors'] and events[-1]['kind']=='EOF' and sum(e['kind']=='EOF' for e in events)==1
            assert all(x['seconds']<=y['seconds'] for x,y in zip(events,events[1:]))
            soft=row['flow'] in 'SB';wire=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
            assert wire==(folder/'wire.bin').read_bytes()==(b'\x11R'+b'\x13\x11'*(2+int(success))+b'PF\x13' if soft else b'RPF')
            assert [bytes.fromhex(e['hex']) for e in events if e['kind']=='send']==[(b'\x13'+payload+b'\x11') if soft else payload,b'READY!',b'END']
            checked.append(dict(error=error,mode=row['mode'],port=row['port'],flow=row['flow'],successful_child=success,CRT_error=crt,DOS_error=dos,raw_first=w[15],raw_last=w[25],DOS_exec_calls_first=w[35],DOS_exec_calls_total=w[36],DOS_pressure_paragraphs=w[32],last_CRT_DOS=list(w[29:31]),wire_sha256=sha(folder/'wire.bin')))
    assert proof['original_inputs']==[] and proof['source_files']==236 and len(proof['products'])==35
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_program_notices_source.py')
    for name,h in proof['inputs'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
    for name,h in proof['products'].items():assert sha(ROOT/name)==h
    for name,h in proof['manifests'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
    # Normal image and flat recovered instructions stay exact. Reuse the
    # independently sealed attached-parent tests only for that identical image.
    prior=read(ROOT/'docs/validation/program-notices.json')
    normal='build/aspect-notice-parent/ASPECT.EXE'
    assert proof['products'][normal]==prior['source_only_products'][normal] and prior['attached_parent_workflows']==13
    for name,h in prior['custody_sha256'].items():assert sha(ROOT/name)==h
    selected.add(ROOT/'docs/validation/program-notices.json')
    unit=next(u for u in read(ROOT/'reconstruction/program_exec/provenance.json')['units'] if u['file']=='reconstruction/program_exec/exec.asm')
    assert sha(ROOT/'build/native-process/exec.bin')==unit['sha256']
    selected.update([ROOT/'build/native-process/exec.bin',ROOT/'reconstruction/program_exec/provenance.json'])
    maps={}
    for name in ['aspect-notice-parent','aspect-notice-fault']:
        path=ROOT/'build'/name/'ASPECT.map';text=path.read_text();seg=re.search(r'^_TEXT\s+CODE\s+\S+\s+[0-9a-f]+:([0-9a-f]+)\s+([0-9a-f]+)',text,re.M|re.I)
        spare=65536-int(seg[1],16)-int(seg[2],16);assert spare>0;maps[name]=spare;selected.add(path)
    for folder in [errors,regression,fresh]:selected.update(path for path in folder.rglob('*') if path.is_file())
    kept={}
    for path in sorted(selected):
        dest=cohort/'accepted'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        assert sha(path)==sha(dest);kept[str(dest.relative_to(ROOT))]=sha(dest)
    result=dict(passed=True,all_PROGRAM_message_branches_accepted=True,successful_post_error_EXEC_accepted=True,natural_malformed_executable_rejection_accepted=False,full_PROGRAM_policy_accepted=False,full_application_accepted=False,error_sessions=10,regression_sessions=14,rows=checked,source_files=236,source_products=proof['products'],child_binary_sha256=child_hash,ordinary_parent_unchanged=True,reused_attached_parent_workflows=13,prior_receipt_sha256=sha(ROOT/'docs/validation/program-notices.json'),prior_custody_files_verified=len(prior['custody_sha256']),recovered_EXEC_flat_sha256=unit['sha256'],near_CODE_spare=maps,custody_sha256=kept,auditor_sha256=sha(Path(__file__)),toolchain_inputs={name:sha(ROOT/name) for name in ['nix/flake.nix','nix/flake.lock','tools/dev']},scope='Ten actual8086 DOS sessions cover CRT errno2/7/8/12/13 on COM1/HARD and COM2/BOTH, followed by missing then successful child execution with exactly two notices, rawFFFF then0, errors reset0,508 retained bytes and exact flow wires. Errno7 uses maintained bounded batch composition; errno8 explicitly requests real unsupported DOS EXEC mode4, not malformed-MZ rejection. DOS free-paragraph exhaustion reaches actual EXEC and returns DOS8/CRT12; empty-file DOS5 reaches the generic branch.14 baseline/fault sessions pass.236 sources reproduce35 products; ordinary image is identical to the prior13 attached workflows. Malformed executable behavior on real DOS, attached popup faults, quarantine/retry, full UI and physical/application gates remain open.')
    with output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ['passed','error_sessions','regression_sessions','ordinary_parent_unchanged']}))
if __name__=='__main__':main()
