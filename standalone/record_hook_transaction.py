#!/usr/bin/env python3
"""Bind linked admission, actual helper proposals, recovery and source proof."""
import argparse
import hashlib
import json
from pathlib import Path
from terminal_memory import inspect_terminal_memory

ROOT = Path(__file__).resolve().parents[1]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['linked','validation','dos','proof','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--register-prefix',required=True)
    args = parser.parse_args()
    base = ROOT / 'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute'
    probe = base.with_name(base.name+'-hookprobe')
    prior = base.with_name(base.name.removesuffix('-execute'))
    sources, custody = {}, {}
    def collect(report):
        for name,digest in report['sources'].items():
            assert name not in sources or sources[name] == digest,name
            assert sha(ROOT/name) == digest,name
            sources[name] = digest
    def capture(path):
        assert path.resolve().is_relative_to(ROOT/'build')
        custody[str(path.relative_to(ROOT))] = sha(path)
    for folder in [base,probe]:
        manifest = read(folder/'manifest.json')
        assert manifest['experimental_hook_execute'] and manifest['experimental_hook_return']
        assert sha(folder/'TERMINAL.EXE') == manifest['binary_sha256']
        collect(manifest)
        for name in ['TERMINAL.EXE','terminal.map','manifest.json','hook_transaction.obj','hook_owner.obj','hook_exchange.obj']:
            capture(folder/name)
    binary, diagnostic = sha(base/'TERMINAL.EXE'),sha(probe/'TERMINAL.EXE')
    assert '_terminal_hook_probe' not in (base/'terminal.map').read_text()
    assert b'STAGE0.BIN' not in (base/'TERMINAL.EXE').read_bytes()
    old = read(ROOT/'docs/validation/hook-return.json')
    assert sha(prior/'TERMINAL.EXE') == old['terminal_sha256']
    capture(prior/'TERMINAL.EXE')
    layout = inspect_terminal_memory(base/'TERMINAL.EXE',base/'terminal.map')
    previous = inspect_terminal_memory(prior/'TERMINAL.EXE',prior/'terminal.map')
    def size(info,name): return next(s['bytes'] for s in info['code_segments'] if s['name'] == name)
    assert layout['near_bytes'] == previous['near_bytes'] == 65520
    assert size(layout,'_TEXT') == size(previous,'_TEXT') == 64904
    assert size(layout,'HOOK_CODE')-size(previous,'HOOK_CODE') == 9447
    paths = [getattr(args,n).resolve()/'result.json' for n in ['linked','validation','dos','proof']]
    linked, validation, dos, proof = map(read,paths)
    for report,path in zip([linked,validation,dos,proof],paths):
        assert report['passed'];collect(report);capture(path)
    assert linked['inputs'] == 152 and linked['binary_sha256'] == binary
    assert validation['inputs'] == 1995 and validation['binary_sha256'] == binary
    assert dos['binary_sha256'] == diagnostic and len(dos['cases']) == 5
    for case in dos['cases']:
        assert case['passed'] and case['helpers'] == 10
        assert case['statuses'] == [0,5,7,7,6,0,0,7,7,5]
        folder = paths[2].parent/case['case']
        for name,digest in case['artifacts'].items(): assert sha(folder/name) == digest,name
        for artifact in folder.iterdir():
            if artifact.is_file(): capture(artifact)
        assert (folder/'DIAG.BIN').read_bytes() == b'\0\0'
        assert (folder/'STACK.BIN').read_bytes() == b'\xa5'*256
        assert (folder/'RBFORE.BIN').read_bytes() == (folder/'RBAGAIN.BIN').read_bytes()
        assert (folder/'BASE0.BIN').read_bytes() == (folder/'BASE1.BIN').read_bytes()
        assert (folder/'BASE0.BIN').read_bytes()[8:] == (folder/'TEST.PRM').read_bytes()
        assert (folder/'BEFORE.BIN').read_bytes() == (folder/'AFTER.BIN').read_bytes()
        assert len((folder/'BEFORE.BIN').read_bytes()) == 42
        for i in [1,2,3,4]: assert (folder/f'STAGE{i}.BIN').read_bytes() == (folder/'STAGE0.BIN').read_bytes()
        for i in [7,8,9]: assert (folder/f'STAGE{i}.BIN').read_bytes() == (folder/'STAGE6.BIN').read_bytes()
    helper = paths[2].parent/'HOOKCH.EXE'
    assert sha(helper) == dos['helper_sha256'] == sha(paths[2].parent/'rebuild/HOOKCH.EXE')
    capture(helper);capture(paths[2].parent/'rebuild/HOOKCH.EXE')
    regressions = []
    for port in [1,2]:
        for case in ['normal','bad-token','missing-script','missing-helper','divide','budget','abort']:
            label = f'{args.register_prefix}-{port}-{case}'
            path = ROOT/'build/register-handoff-dos'/label/'result.json'
            report = read(path)
            assert report['passed'] and report['hook_execute'] and report['cpu'] == '8086'
            assert report['parent_sha256'] == report['DOS']['binary_sha256'] == binary
            assert report['DOS']['passed'] and all(report['DOS']['checks'].values())
            collect(report);capture(path)
            folder = ROOT/'build/connection-dos'/('register-'+label)
            for snap in report['snapshots']:
                assert sha(folder/f'OWNER{snap["index"]}.BIN') == snap['owner_sha256']
                assert sha(folder/f'CHILD{snap["index"]}.BIN') == snap['child_sha256']
            for artifact in folder.iterdir():
                if artifact.is_file(): capture(artifact)
            regressions.append(dict(port=port,case=case,snapshots=len(report['snapshots']),passed=True))
    assert proof['original_inputs'] == [] and len(proof['products']) == 6 and proof['source_files'] == 700
    for name,digest in proof['products'].items(): assert sha(ROOT/name) == digest,name
    assert proof['products'][str((base/'TERMINAL.EXE').relative_to(ROOT))] == binary
    assert proof['products'][str((probe/'TERMINAL.EXE').relative_to(ROOT))] == diagnostic
    assert proof['checker_sha256'] == sha(ROOT/'standalone/prove_directory_keys_source.py')
    capture(paths[3].parent/'build.log')
    for name in ['standalone/record_hook_transaction.py','docs/HOOK_TRANSACTION.md']: sources[name] = sha(ROOT/name)
    result = dict(passed=True,linked_admission_cases=152,linked_validation_cases=1995,helper_attempts=50,
                  DOS_cases=dos['cases'],register_regressions=regressions,products=proof['products'],source_files=700,
                  terminal_sha256=binary,prior_validation_sha256=sha(prior/'TERMINAL.EXE'),near_bytes=65520,
                  resident_code_bytes=64904,added_hook_bank_bytes=9447,transaction_far_storage_bytes=3934,
                  sources=sources,custody_sha256=custody,
                  rejected_run='build/hook-transaction-DOS-04: combined frames corrupted printer/mouse shutdown; corrected by separating projection and EXEC staging.',
                  scope='Actual terminal-linked owned helper EXEC, validated private proposal after release, exact return/failure retention '
                  'and stack guard. Diagnostic before UART/mouse acquisition. No KEY kind2 routing, online owner handoff, '
                  'resource staging, accepted settings/register adoption, live BBS or physical hardware acceptance.')
    target = args.output.resolve()
    assert target.is_relative_to(ROOT/'build') or target.is_relative_to(ROOT/'docs/validation')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS152 admission,1995 validation,50 DOS helper attempts,14 register workflows,700-source/six-product proof')


if __name__ == '__main__': main()
