#!/usr/bin/env python3
"""Audit banked DOS evidence and write a source-only public validation receipt."""
import argparse,json,re,struct
from pathlib import Path
from build_aspect_process import ROOT,sha

def read(path):return json.loads(path.read_text())
def current(sources):
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fault-label',action='append',required=True)
    parser.add_argument('--component-label',required=True)
    parser.add_argument('--source-label',required=True)
    parser.add_argument('--component-source-label',required=True)
    args=parser.parse_args()
    for label in [*args.fault_label,args.component_label,args.source_label,args.component_source_label]:
        assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
    vm=ROOT/'build/aspect-fault-break';parent=ROOT/'build/terminal-process'
    manifest=read(vm/'manifest.json');current(manifest['sources'])
    parent_manifest=read(parent/'manifest.json');current(parent_manifest['sources'])
    assert manifest['experimental_break_owner'] and manifest['experimental_fault_unwind']
    assert sha(vm/'ASPECT.EXE')==manifest['binary_sha256']
    assert sha(parent/'TERMINAL.EXE')==parent_manifest['binary_sha256']
    routes=[];seen=set();evidence={}
    for label in args.fault_label:
        folder=ROOT/'build/aspect-unwind-break/runs'/label;run=read(folder/'result.json')
        assert run['passed'] and run['experimental_break_owner']
        assert run['checker_sha256']==sha(ROOT/'standalone/test_aspect_unwind_dos.py')
        assert run['parent_sha256']==parent_manifest['binary_sha256'] and run['child_sha256']==manifest['binary_sha256']
        current(run['sources'])
        for name,digest in run['sources'].items():assert sha(folder/'sources'/name)==digest,name
        for case in run['cases']:
            item=(case['phase'],case['kind'],case['port'],case['flow']);assert item not in seen,item;seen.add(item)
            sub=folder/case['case'];assert read(sub/'result.json')==case
            assert case['passed'] and all(case['checks'].values())
            assert sha(sub/'TERMINAL.EXE')==run['parent_sha256'] and sha(sub/'ASPECT.EXE')==run['child_sha256']
            assert re.search(r'^cputype\s*=\s*8086\s*$',(sub/'dosbox.conf').read_text(),re.M)
            words=struct.unpack('<20H',(sub/'FAULT.BIN').read_bytes());assert list(words)==case['report_words']
            phase,kind,port,flow=item;control=phase==0;error=0 if control else 5 if kind in 'AL' else 12
            assert words[:10]==(0x4652,phase,{'D':0,'A':1,'F':2,'L':3}[kind],error,0,
                int(not control),int(not control),0,int(not control),1)
            assert words[12:16]==(0,1,1,1) and words[17]<36 and words[19]==1
            if phase in [9,20]:assert words[10]>words[11]>0 and words[18]==int(phase==9)
            if control:assert words[16]==12
            assert (sub/'BEFORE.BIN').read_bytes()==(sub/'AFTER.BIN').read_bytes()
            screen=(sub/'SCREEN.BIN').read_bytes()[::2];wire=(sub/'serial.bin').read_bytes()
            assert b'RECOVERY OK' in screen and b'FAIL' not in screen
            assert wire.count(b'Synth42\r')==1 and b'ready' in wire
            assert (sub/'CHILD.LOG').read_bytes().endswith(b'T')
            assert (sub/'WRITE.BIN').read_bytes()==b'pending5'
            routes.append(dict(label=label,phase=phase,kind=kind,port=port,flow=flow,
                checks=len(case['checks']),first_error=error,second_VM_error=words[4],
                cleanup_error=words[7],clean_after_both=words[9]==words[15]==1))
            for name in ['result.json','FAULT.BIN','BEFORE.BIN','AFTER.BIN','RENDER.BIN','serial.bin']:
                evidence[str((sub/name).relative_to(ROOT))]=sha(sub/name)
    expected={(p,k,1,'H') for p in range(1,23) for k in 'DAFL'}
    expected|={(0,'D',1,'H'),(9,'D',2,'B'),(21,'D',2,'B'),(6,'D',1,'S'),(10,'D',2,'N')}
    assert seen==expected,(expected-seen,seen-expected)
    component=ROOT/'build/native-program-far';cm=read(component/'manifest.json');current(cm['sources'])
    comp=read(component/'runs'/args.component_label/'result.json')
    assert comp['passed'] and len(comp['cases'])==8 and comp['binary_sha256']==cm['binary_sha256']
    assert comp['checker_sha256']==sha(ROOT/'standalone/test_native_program_dos.py')
    assert {(c['port'],c['flow']) for c in comp['cases']}=={(p,f) for p in [1,2] for f in 'NSHB'}
    for case in comp['cases']:
        assert case['passed'] and all(case['checks'].values())
        sub=component/'runs'/args.component_label/f"com{case['port']}-{case['flow']}"
        assert sha(sub/'PROGRAM.EXE')==cm['binary_sha256']
        assert sha(sub/f"OWN{case['port']}.COM")==cm['children'][f"OWN{case['port']}.COM"]
    proofs={}
    for name,folder,checker,count in [
        ('VM',ROOT/'build/aspect-unwind-break/source-proofs'/args.source_label,'standalone/check_aspect_banked_source.py',24),
        ('component',component/'source-proofs'/args.component_source_label,'standalone/check_native_program_source.py',22)]:
        proof=read(folder/'result.json');assert proof['passed'] and len(proof['products'])==count
        assert proof['checker_sha256']==sha(ROOT/checker);current(proof['sources'])
        for path,pair in proof['products'].items():assert pair['actual']==pair['expected']==sha(ROOT/'build'/path),path
        proofs[name]=dict(products=proof['products'],source_files=proof.get('source_files'),original_inputs=[])
    bank=read(vm/'bank-checks.json');assert bank['passed'] and bank['binary_sha256']==manifest['binary_sha256']
    assert bank['checker_sha256']==sha(ROOT/'standalone/check_process_banks.py')
    assert bank['objects']['controller']['object_sha256']==manifest['objects']['native_program_far.obj']==sha(vm/'native_program_far.obj')
    assert bank['objects']['owner']['object_sha256']==manifest['objects']['break_owner_far.obj']==sha(ROOT/'build/break-owner-far/break_owner_far.obj')
    owner={}
    for name in ['break-owner','break-owner-far']:
        result=read(ROOT/'build'/name/'owner-checks.json')
        assert result['passed'] and result['checker_sha256']==sha(ROOT/'standalone/check_break_owner.py')
        assert result['admissions']==18 and result['abandoned_service_boundaries']==195 and result['quarantine_cases']==2
        assert result['binary_sha256']==sha(ROOT/'build'/name/'BRKOWN.EXE');owner[name]=result
    owner_dos={}
    for name,label in [('break-owner','near-bank-regression-01'),('break-owner-far','far-owner-separate-03')]:
        run=read(ROOT/'build'/name/label/'receipt.json')
        assert run['passed'] and run['checks']==132 and run['children']==4
        assert run['binary_sha256']==sha(ROOT/'build'/name/'BRKOWN.EXE');current(run['sources'])
        owner_dos[name]=dict(checks=132,children=4,label=label,binary_sha256=run['binary_sha256'])
    assert sha(ROOT/'build/break-owner/BRKOWN.EXE')==read(ROOT/'docs/validation/break-owner.json')['binary_sha256']
    earlier=read(ROOT/'docs/validation/program-break-owner.json')
    assert sha(ROOT/'build/native-program/PROGRAM.EXE')==earlier['default_matrix']['binary_sha256']
    assert sha(ROOT/'build/native-program-break/PROGRAM.EXE')==earlier['guarded_matrix']['binary_sha256']
    failed=ROOT/'build/break-owner-far/far-owner-separate-01/OUTPUT.TXT'
    assert b'failures=77' in failed.read_bytes()
    result=dict(passed=True,whole_application_gates_closed=[],fault_cases=routes,
        fault_checks=sum(c['checks'] for c in routes),bank_layout=bank,owner_models=owner,owner_DOS=owner_dos,
        component=dict(routes=8,DOS_assertions=sum(c['assertions'] for c in comp['cases']),binary_sha256=cm['binary_sha256']),
        source_proofs=proofs,sources=manifest['sources'],parent_sha256=parent_manifest['binary_sha256'],
        child_sha256=manifest['binary_sha256'],evidence=evidence,
        checker_sha256=sha(Path(__file__)),replay_sha256=sha(ROOT/'standalone/dos_image.py'),
        retained_failure=dict(label='far-owner-separate-01',assertions_failed=77,output_sha256=sha(failed),
            cause='Raw IRET initially remained in _TEXT while installer used its own bank CS; corrected placement is build-asserted.'),
        limits=['Experimental full fault VM; normal terminal/ASPECT publication unchanged',
            'Application-wide ownership and quarantine-to-exit retention remain open',
            'Modeled DOS-service cuts do not prove asynchronous IRQ/kernel/allocator corruption',
            'Physical RS232/WiFi-modem/keyboard acceptance and all full application gates remain open'])
    (ROOT/'docs/validation/program-banks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(len(routes),'actual VM fault/control routes, eight component routes and both source proofs audited')

if __name__=='__main__':main()
