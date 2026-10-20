#!/usr/bin/env python3
"""Audit exit retention, normal attached workflows and full fault regressions."""
import argparse,json,re,struct
from pathlib import Path
from build_exit_owner import ROOT,OUT,sha
def read(path):return json.loads(path.read_text())
def current(sources):
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fault-label',action='append',required=True)
    parser.add_argument('--normal-label',required=True);parser.add_argument('--source-label',required=True)
    parser.add_argument('--exit-label',required=True);parser.add_argument('--cli-label',required=True)
    args=parser.parse_args()
    for label in [*args.fault_label,args.normal_label,args.source_label,args.exit_label,args.cli_label]:
        assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
    summaries={};evidence={}
    for name,folder,wanted in [
        ('component',OUT/'runs'/args.exit_label,{m+str(f) for m in 'NRQDPL' for f in [0,1]}),
        ('CLI',ROOT/'build/aspect-exit-break/runs'/args.cli_label,{'Q0'})]:
        run=read(folder/'result.json');assert run['passed'] and run['actual_ASPECT_CLI']==(name=='CLI')
        current(run['sources']);assert run['checker_sha256']==sha(ROOT/'standalone/test_exit_owner_dos.py')
        assert {c['case'] for c in run['cases']}==wanted
        for case in run['cases']:
            sub=folder/case['case'];mode=case['case'][0];retained=mode in 'QL'
            assert case['status']==(0x030a if retained else 37)
            words=struct.unpack('<13H',(sub/'EXITWIT.BIN').read_bytes())
            assert words[:2]==(0x5845,ord(mode)) and words[11]==int(case['case'][1])
            assert words[10]==(4 if mode in 'QD' else 1 if mode in 'RP' else 0)
            assert case['checks']==(277 if name=='CLI' else 276 if mode=='Q' else 273 if mode=='L' else 8)
            if name=='CLI':assert words[12]!=0
            output=(sub/'OUTPUT.TXT').read_text()
            assert re.fullmatch(r'EXIT OWNER '+case['case']+r' checks='+str(case['checks'])+r' failures=0 status='+str(case['status'])+r'\s*',output)
            assert (sub/'RESULT.TXT').read_text().strip()=='PASS'
            for product,digest in run['products'].items():assert sha(sub/product)==digest
            for artifact,digest in case['artifacts'].items():assert sha(sub/artifact)==digest
            evidence[str(sub.relative_to(ROOT))]=case['artifacts']
        summaries[name]=dict(cases=run['cases'],products=run['products'],scope=run['scope'])
    normal_folder=ROOT/'build/aspect-parent-break'/args.normal_label
    normal=read(normal_folder/'result.json');assert normal['passed'] and normal['experimental_break_owner']
    assert normal['checker_sha256']==sha(ROOT/'standalone/test_aspect_parent_process_dos.py');current(normal['source_hashes'])
    expected={'G','T','W','R','F'}|{f'full-{p}-{f}' for p in [1,2] for f in 'NSHB'}
    assert {c['case'] for c in normal['cases']}==expected
    for case in normal['cases']:
        sub=normal_folder/case['case'];assert case['passed'] and all(case['checks'].values())
        assert (sub/'BEFORE.BIN').read_bytes()==(sub/'AFTER.BIN').read_bytes()
        assert sha(sub/'ASPECT.EXE')==normal['child_sha256']
    fault=[];seen=set()
    child=ROOT/'build/aspect-fault-break/ASPECT.EXE'
    for label in args.fault_label:
        folder=ROOT/'build/aspect-unwind-break/runs'/label;run=read(folder/'result.json')
        assert run['passed'] and run['child_sha256']==sha(child)
        assert run['checker_sha256']==sha(ROOT/'standalone/test_aspect_unwind_dos.py');current(run['sources'])
        for case in run['cases']:
            item=(case['phase'],case['kind'],case['port'],case['flow']);assert item not in seen;seen.add(item)
            sub=folder/case['case'];assert case==read(sub/'result.json')
            assert case['passed'] and all(case['checks'].values())
            words=struct.unpack('<20H',(sub/'FAULT.BIN').read_bytes());assert list(words)==case['report_words']
            control=item[0]==0;error=0 if control else 5 if item[1] in 'AL' else 12
            assert words[:10]==(0x4652,item[0],{'D':0,'A':1,'F':2,'L':3}[item[1]],error,0,int(not control),int(not control),0,int(not control),1)
            assert words[12:16]==(0,1,1,1) and words[17]<36 and words[19]==1
            if item[0] in [9,20]:assert words[10]>words[11]>0 and words[18]==int(item[0]==9)
            assert (sub/'BEFORE.BIN').read_bytes()==(sub/'AFTER.BIN').read_bytes()
            assert sha(sub/'ASPECT.EXE')==sha(child)
            fault.append(dict(label=label,phase=item[0],kind=item[1],port=item[2],flow=item[3],checks=len(case['checks'])))
    expected={(p,k,1,'H') for p in range(1,23) for k in 'DAFL'}
    expected|={(0,'D',1,'H'),(9,'D',2,'B'),(21,'D',2,'B'),(6,'D',1,'S'),(10,'D',2,'N')}
    assert seen==expected
    proof=read(OUT/'source-proofs'/args.source_label/'result.json')
    assert proof['passed'] and len(proof['products'])==29
    assert proof['checker_sha256']==sha(ROOT/'standalone/check_exit_source.py');current(proof['sources'])
    for name,pair in proof['products'].items():assert pair['actual']==pair['expected']==sha(ROOT/'build'/name),name
    model=read(OUT/'model-checks.json');assert model['passed'] and len(model['admission_rejections'])==10 and model['decisions']==4
    assert model['checker_sha256']==sha(ROOT/'standalone/check_exit_owner.py')
    assert model['binary_sha256']==sha(OUT/'EXITKID.EXE')
    baseline=read(ROOT/'docs/validation/enigma-upload-time.json')['source_products']
    normal_products={name:sha(ROOT/'build'/name) for name in ['aspect-runner/ASPECT.EXE','terminal/TERMINAL.EXE']}
    for name,digest in normal_products.items():assert baseline[name]==digest,name
    bank=read(ROOT/'build/aspect-fault-break/bank-checks.json')
    assert bank['passed'] and bank['binary_sha256']==sha(child)
    result=dict(passed=True,whole_application_gates_closed=[],exit_routes=summaries,admission_model=model,
        normal_routes=dict(cases=13,binary_sha256=normal['child_sha256'],checks=sum(len(c['checks']) for c in normal['cases'])),
        fault_routes=fault,fault_checks=sum(c['checks'] for c in fault),
        source_proof=proof,evidence=evidence,normal_products_unchanged=normal_products,
        near_code_spare=bank['near_spare'],checker_sha256=sha(Path(__file__)),
        limits=['Live-lease callback is controlled input in the small component; separate timer probe exercises actual ASPECT CLI',
                'Invalid MCB fail-stop is instruction-model evidence, not kernel-corruption recovery',
                'Retention deliberately keeps allocations and remaining DOS handles; automatic unload/repair is not implemented',
                'Normal terminal/ASPECT publication, application-wide parent ownership and physical modem/keyboard acceptance remain open'])
    (ROOT/'docs/validation/exit-owner.json').write_text(json.dumps(result,indent=2)+'\n')
    print('12 exit cases, real CLI retention, 13 normal routes, 93 fault routes and 29 source products audited')
if __name__=='__main__':main()
