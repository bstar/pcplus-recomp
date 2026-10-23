#!/usr/bin/env python3
"""Bind staged modem offers, literal response matching and initialization evidence."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from terminal_memory import inspect_terminal_memory

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/config'))
from prm import expand_modem_command


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['linked','validation','admission','dos','initialization','proof','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--register-prefix',required=True)
    args=parser.parse_args()
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem'
    probe=base.with_name(base.name+'-hookprobe')
    binary,diagnostic=sha(base/'TERMINAL.EXE'),sha(probe/'TERMINAL.EXE')
    sources,custody={},{}
    def collect(report,key='sources'):
        for name,digest in report[key].items():
            assert name not in sources or sources[name]==digest,name
            assert sha(ROOT/name)==digest,name
            sources[name]=digest
    def capture(path):
        assert path.resolve().is_relative_to(ROOT/'build')
        custody[str(path.relative_to(ROOT))]=sha(path)
    for folder in [base,probe]:
        manifest=read(folder/'manifest.json');assert manifest['experimental_hook_modem']
        assert sha(folder/'TERMINAL.EXE')==manifest['binary_sha256'];collect(manifest)
        for name in ['TERMINAL.EXE','terminal.map','manifest.json','hook_modem.obj','hook_return.obj']:
            capture(folder/name)
    assert '_terminal_hook_probe' not in (base/'terminal.map').read_text()
    layout=inspect_terminal_memory(base/'TERMINAL.EXE',base/'terminal.map')
    assert layout['near_bytes']==65520
    sizes={s['name']:s['bytes']for s in layout['code_segments']}
    assert (sizes['_TEXT'],sizes['HOOK_CODE'],sizes['MODEM_CODE'])==(64904,20299,2900)
    legacy=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers/TERMINAL.EXE'
    legacy_manifest=read(legacy.parent/'manifest.json');collect(legacy_manifest)
    assert not legacy_manifest['experimental_hook_return'] and not legacy_manifest['experimental_hook_modem']
    assert sha(legacy)==legacy_manifest['binary_sha256']==read(ROOT/'docs/validation/register-bbs.json')['terminal_sha256']
    capture(legacy);capture(legacy.parent/'manifest.json');capture(ROOT/'build/hook-modem-legacy-build.log')
    paths=[getattr(args,n).resolve()/('checks.json' if n=='initialization' else 'result.json')
           for n in ['linked','validation','admission','dos','initialization','proof']]
    linked,validation,admission,dos,initialization,proof=map(read,paths)
    for report,path in zip([linked,validation,admission,dos,initialization,proof],paths):
        assert report['passed'];collect(report,'inputs' if report is initialization else 'sources');capture(path)
    for report,count in [(linked,3394),(validation,4822),(admission,152)]:
        assert report['binary_sha256']==binary and report['inputs']==count
    assert dos['hook_modem'] and dos['binary_sha256']==diagnostic and len(dos['cases'])==5
    offers=0
    for case in dos['cases']:
        assert case['passed'] and case['helpers']==10
        folder=paths[3].parent/case['case'];active=case['case'] in ('MODEM','directory-MODEM')
        assert case['statuses']==[0,5,7,7,6,0,0,0 if active else 7,7,5]
        for name,digest in case['artifacts'].items():assert sha(folder/name)==digest,name
        assert (folder/'STACK.BIN').read_bytes()==b'\xa5'*256
        assert (folder/'DIAG.BIN').read_bytes()==b'\0\0'
        assert (folder/'RBFORE.BIN').read_bytes()==(folder/'RBAGAIN.BIN').read_bytes()
        assert (folder/'BASE0.BIN').read_bytes()==(folder/'BASE1.BIN').read_bytes()
        assert (folder/'BASE0.BIN').read_bytes()[8:]==(folder/'TEST.PRM').read_bytes()
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        for i in [0,5,6]+([7] if active else []):
            proposal=(folder/f'STAGE{i}.BIN').read_bytes();raw=proposal[830:2094]
            expected=struct.pack('<3H',int(active),struct.unpack_from('<H',raw,2)[0],raw[0x1e2] if active else 0)
            if active:
                commands=[expand_modem_command(raw[at:at+cap].split(b'\0')[0]) for at,cap in [(0x18,47),(0x47,25),(0x60,25),(0x79,25),(0x92,25),(0xab,25)]]
                dial=commands[1].split(b'\0')[0]+b'CaseTest:23'+commands[2].split(b'\0')[0]
                expected+=b''.join(c.ljust(129,b'\0')for c in commands)+dial.ljust(129,b'\0')+raw[0xc4:0x174]+b'\0'
            else:expected+=bytes(1080)
            assert (folder/f'MODEM{i}.BIN').read_bytes()==expected
            offers+=1
        for artifact in folder.iterdir():
            if artifact.is_file():capture(artifact)
    assert offers==17
    helper=paths[3].parent/'HOOKCH.EXE'
    assert sha(helper)==dos['helper_sha256']==sha(paths[3].parent/'rebuild/HOOKCH.EXE')
    capture(helper);capture(paths[3].parent/'rebuild/HOOKCH.EXE')
    assert initialization['parent_sha256']==binary and len(initialization['cases'])==9
    assert initialization['mouse_scales']==[8,4]
    for case in initialization['cases']:
        assert case['passed'] and all(case['checks'].values())
        folder=paths[4].parent/case['case']
        assert (folder/'serial.bin').read_bytes().hex()==case['wire_hex']
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        for name,digest in case['captures'].items():assert sha(folder/name)==digest,name
        for artifact in folder.iterdir():
            if artifact.is_file():capture(artifact)
    regressions=[]
    for port in [1,2]:
        for case in ['normal','bad-token','missing-script','missing-helper','divide','budget','abort']:
            label=f'{args.register_prefix}-{port}-{case}';path=ROOT/'build/register-handoff-dos'/label/'result.json'
            report=read(path);assert report['passed'] and report['hook_modem'] and report['cpu']=='8086'
            assert report['parent_sha256']==report['DOS']['binary_sha256']==binary
            assert report['DOS']['passed'] and all(report['DOS']['checks'].values());collect(report);capture(path)
            folder=ROOT/'build/connection-dos'/('register-'+label)
            for snap in report['snapshots']:
                assert sha(folder/f'OWNER{snap["index"]}.BIN')==snap['owner_sha256']
                assert sha(folder/f'CHILD{snap["index"]}.BIN')==snap['child_sha256']
            for artifact in folder.iterdir():
                if artifact.is_file():capture(artifact)
            regressions.append(dict(port=port,case=case,snapshots=len(report['snapshots']),passed=True))
    assert proof['original_inputs']==[] and proof['source_files']==703 and len(proof['products'])==6
    for name,digest in proof['products'].items():assert sha(ROOT/name)==digest,name
    assert proof['products'][str((base/'TERMINAL.EXE').relative_to(ROOT))]==binary
    assert proof['products'][str((probe/'TERMINAL.EXE').relative_to(ROOT))]==diagnostic
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_directory_keys_source.py')
    capture(paths[5].parent/'build.log')
    for name in ['standalone/record_hook_modem.py','docs/HOOK_MODEM.md','src/config/prm.py']:sources[name]=sha(ROOT/name)
    result=dict(passed=True,linked_preparation_cases=3394,linked_validation_matcher_cases=4822,linked_admission_cases=152,
                helper_attempts=50,exact_modem_offers=17,DOS_cases=dos['cases'],initialization_cases=initialization['cases'],
                register_regressions=regressions,source_files=703,products=proof['products'],terminal_sha256=binary,
                unchanged_BBS_product_sha256=sha(legacy),near_bytes=65520,resident_code_bytes=64904,
                hook_bank_bytes=20299,modem_bank_bytes=2900,offer_far_bytes=1086,sources=sources,custody_sha256=custody,
                correction='Response slots are already expanded, so caret bytes are literal. Previous helper-return receipts describe the older restrictive policy.',
                rejected_fixture='hook-modem-init-DOS-01: startup rejected A5A5 mouse scales; corrected fixture8/4 without product changes.',
                scope='Pure modem resource staging and terminal proposal phase2->3; no active connection settings/register/baseline adoption. '
                'Normal initialization and register recovery are separate workflows. No interactive KEY routing, online helper owner handoff, '
                'new live BBS or physical hardware acceptance.')
    target=args.output.resolve();assert target.is_relative_to(ROOT/'build') or target.is_relative_to(ROOT/'docs/validation')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS3394 modem,4822 validation/matcher,152 admission;17 DOS offers,9 init,14 recovery;703 sources/six products')


if __name__=='__main__':main()
