#!/usr/bin/env python3
"""Publish bounded attached-PROGRAM evidence; keep normal publication open."""
import argparse,json,re
from pathlib import Path
from build_aspect_process import ROOT,sha


def read(path):return json.loads(path.read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True);parser.add_argument('--source-label',required=True)
    args=parser.parse_args()
    for label in (args.label,args.source_label):assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
    folder=ROOT/'build/aspect-parent-process'/args.label;run=read(folder/'result.json')
    assert run['passed'] and len(run['cases'])==13 and run['checker_sha256']==sha(ROOT/'standalone/test_aspect_parent_process_dos.py')
    expected={'G','T','W','R','F'}|{f'full-{p}-{f}' for p in (1,2) for f in 'NSHB'}
    assert {c['case'] for c in run['cases']}==expected
    for name,digest in run['source_hashes'].items():assert sha(ROOT/name)==sha(folder/'sources'/name)==digest,name
    assert run['parent_sha256']==sha(ROOT/'build/terminal-process/TERMINAL.EXE')
    assert run['child_sha256']==sha(ROOT/'build/aspect-process-parent/ASPECT.EXE')
    assert read(ROOT/'build/terminal-process/manifest.json')['experimental_external_render']
    assert read(ROOT/'build/aspect-process-parent/manifest.json')['experimental_parent_render']
    cases=[];evidence=[folder/'result.json',folder/'observer.asm',folder/'RENDER.COM']
    for case in run['cases']:
        assert case['passed'] and all(case['checks'].values())
        sub=folder/case['case'];raw=(sub/'RENDER.BIN').read_bytes();size=case['compared_parent_bytes']
        assert size==10276 and case['resource_words'][2]==0 and case['resource_words'][7]==0
        assert raw[-2*size:-size]==raw[-size:]
        assert (sub/'BEFORE.BIN').read_bytes()==(sub/'AFTER.BIN').read_bytes()
        assert sha(sub/'TERMINAL.EXE')==run['parent_sha256'] and sha(sub/'ASPECT.EXE')==run['child_sha256']
        successful=sum(not r['carry'] for r in case['nested_EXEC'])
        assert successful==(9 if case['configuration']['full'] else 1)
        cases.append(dict(case=case['case'],checks=len(case['checks']),successful_nested_EXEC=successful,
            attempted_nested_EXEC=len(case['nested_EXEC']),compared_parent_bytes=size,
            external_leases=case['resource_words'][8],retired_leases=case['resource_words'][9],
            view_refreshes=case['resource_words'][10],configuration=case['configuration']))
        evidence += [sub/n for n in ('result.json','serial.bin','SCREEN.BIN','RENDER.BIN','BEFORE.BIN','AFTER.BIN','CHILD.LOG')]
    proof_folder=ROOT/'build/aspect-parent-process/source-proofs'/args.source_label;proof=read(proof_folder/'result.json')
    assert proof['passed'] and len(proof['products'])==25
    assert proof['checker_sha256']==sha(ROOT/'standalone/check_aspect_parent_process_source.py')
    for name,digest in proof['sources'].items():assert sha(ROOT/name)==sha(proof_folder/'source'/name)==digest,name
    for name,pair in proof['products'].items():assert pair['expected']==pair['actual']==sha(ROOT/'build'/name)==sha(proof_folder/'source/build'/name)
    models=[]
    for path,key,checker,count,product in [
        (ROOT/'build/terminal-process/process-owner-checks.json','parent_sha256','check_aspect_parent_process.py',29,ROOT/'build/terminal-process/TERMINAL.EXE'),
        (ROOT/'build/aspect-process-parent/program-client-checks.json','child_sha256','check_aspect_program_client.py',48,ROOT/'build/aspect-process-parent/ASPECT.EXE')]:
        model=read(path);assert model['passed'] and len(model['cases'])==count and model[key]==sha(product)
        assert model['checker_sha256']==sha(ROOT/'standalone'/checker)
        models.append(dict(path=str(path.relative_to(ROOT)),cases=count,scope=model['scope']));evidence.append(path)
    evidence += [proof_folder/'result.json',proof_folder/'build.log']
    counter_path=ROOT/'build/aspect-process-parent/program-client-before.json';counter=read(counter_path)
    assert not counter['passed'] and counter['end_result']==10 and counter['next_emit_result']==0 and counter['new_parent_requests']==1
    assert counter['binary_sha256']!=run['child_sha256']
    evidence.append(counter_path)
    assert sha(ROOT/'build/aspect-runner/ASPECT.EXE')=='aef146fdf62846a2dfc5d73413f435a8bfe68ca4f68d639178083d4d21e559f5'
    assert sha(ROOT/'build/terminal/TERMINAL.EXE')=='dbc5e7104ea32b2cec00a47030acc579bed4c46dd6fc19ff07750df513338b52'
    raw=read(ROOT/'docs/validation/aspect-process.json');assert sha(ROOT/'build/aspect-process/ASPECT.EXE')==raw['experimental_binary_sha256']
    retained=[]
    for path,reason in [
        (ROOT/'build/aspect-parent-process/parent-process-01/result.json','Fixture dropped DTR; actual UART owner correctly reported LINE and rejected success.'),
        (ROOT/'build/aspect-parent-process/parent-process-08/full-2-N/result.json','Fixture selected COM1 in the directory while only COM2 was configured in the emulator.'),
        (ROOT/'build/aspect-parent-process/parent-process-10/result.json','Fixture compared20 characters with a21-character saved-screen expectation.')]:
        old=read(path);assert not old['passed'];retained.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),reason=reason))
    result=dict(passed=True,experimental_only=True,whole_application_gates_closed=[],normal_publication_changed=False,
        capability=7,normal_capability=6,normal_supported_slots=105,experimental_supported_slots=108,
        actual_DOS_cases=13,actual_DOS_checks=sum(c['checks'] for c in cases),cases=cases,
        successful_nested_EXEC=sum(c['successful_nested_EXEC'] for c in cases),
        external_leases=sum(c['external_leases'] for c in cases),view_refreshes=sum(c['view_refreshes'] for c in cases),
        exact_parent_bytes_per_attempt=10276,linked_models=models,fresh_source_products=25,
        parent_sha256=run['parent_sha256'],child_sha256=run['child_sha256'],source_hashes=run['source_hashes'],
        prior_raw_binary_preserved=True,prior_raw_ledger_sha256=sha(ROOT/'docs/validation/aspect-process.json'),
        nix_inputs={n:sha(ROOT/n) for n in ('nix/flake.nix','nix/flake.lock')},
        recorder_sha256=sha(Path(__file__)),retained_failures=retained,retained_owner_counterexample=counter,
        evidence={str(p.relative_to(ROOT)):sha(p) for p in evidence},
        limitations=['Experimental only; normal105-slot/capability6 products remain byte-identical and do not publish DOS/RUN/SHELL.',
            'Fixed admitted80x25/page0 view. The refresh hint revalidates that retained view without RIS or discarding NOCLEAR text; this is not the original general geometry/UI implementation.',
            'Actual synthetic selected-directory/input-table/settings/metadata leases are compared. Macro keyboard, mouse/window/error notices and broader views remain open.',
            'Nonlocal faults during external ownership require separate complete unwind evidence before normal publication.',
            'Modeled38400-baud UART/DOSBox BIOS. Live ENiGMA/Synchronet transfer/door acceptance, loaded-input pressure and physical RS-232 modem/hardware testing remain open.'])
    (ROOT/'docs/validation/aspect-parent-process.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recorded13 real attached cases,77 linked policy cases and25 fresh products; normal publication remains unchanged.')


if __name__=='__main__':main()
