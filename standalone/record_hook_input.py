#!/usr/bin/env python3
"""Bind frozen-path input offers to DOS bytes, recovery and source reproduction."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from terminal_memory import inspect_terminal_memory

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['linked','modem','validation','admission','input-dos','helper-dos','proof','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--register-prefix',required=True);args=parser.parse_args()
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input'
    probe=base.with_name(base.name+'-inputprobe');helper_probe=base.with_name(base.name+'-hookprobe')
    binary=sha(base/'TERMINAL.EXE');sources,custody={},{}
    def collect(report):
        for name,digest in report['sources'].items():
            assert name not in sources or sources[name]==digest,name
            assert sha(ROOT/name)==digest,name
            sources[name]=digest
    def capture(path):
        assert path.resolve().is_relative_to(ROOT/'build')
        custody[str(path.relative_to(ROOT))]=sha(path)
    for folder in [base,probe,helper_probe]:
        manifest=read(folder/'manifest.json');assert manifest['experimental_hook_input']
        assert sha(folder/'TERMINAL.EXE')==manifest['binary_sha256'];collect(manifest)
        for name in ['TERMINAL.EXE','terminal.map','manifest.json','hook_input.obj','xlt_live.obj']:capture(folder/name)
    assert '_terminal_hook_input_probe' not in (base/'terminal.map').read_text()
    assert b'D:\\CASE.BIN' not in (base/'TERMINAL.EXE').read_bytes()
    layout=inspect_terminal_memory(base/'TERMINAL.EXE',base/'terminal.map')
    sizes={s['name']:s['bytes']for s in layout['code_segments']}
    assert layout['near_bytes']==65520 and (sizes['_TEXT'],sizes['HOOK_CODE'],sizes['CONFIG_CODE'])==(64908,22145,63662)
    prior=base.with_name(base.name.removesuffix('-input'))
    legacy=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers'
    assert sha(prior/'TERMINAL.EXE')==read(ROOT/'docs/validation/hook-modem.json')['terminal_sha256']
    assert sha(legacy/'TERMINAL.EXE')==read(ROOT/'docs/validation/register-bbs.json')['terminal_sha256']
    for folder in [prior,legacy]:
        collect(read(folder/'manifest.json'));capture(folder/'TERMINAL.EXE');capture(folder/'manifest.json')
    capture(ROOT/'build/hook-input-prior-builds.log')
    paths=[getattr(args,n).resolve()/'result.json' for n in ['linked','modem','validation','admission','input_dos','helper_dos','proof']]
    linked,modem,validation,admission,dos,helpers,proof=map(read,paths)
    for report,path in zip([linked,modem,validation,admission,dos,helpers,proof],paths):
        assert report['passed'];collect(report);capture(path)
    for report,count in [(linked,39),(modem,3394),(validation,4822),(admission,152)]:
        assert report['inputs']==count and report['binary_sha256']==binary
    assert dos['binary_sha256']==sha(probe/'TERMINAL.EXE') and len(dos['cases'])==19
    accepted=0
    for case in dos['cases']:
        folder=paths[4].parent/case['case'];recipe=case['recipe'];status=case['status']
        assert case['passed']
        for name,digest in case['artifacts'].items():assert sha(folder/name)==digest,name
        for artifact in folder.rglob('*'):
            if artifact.is_file():capture(artifact)
        assert (folder/'CWD.BIN').read_bytes()==b'ALT\0'.ljust(64,b'\0')
        for a,b in [('BASE0.BIN','BASE1.BIN'),('PBEFORE.BIN','PAFTER.BIN'),('KEY0.BIN','KEY1.BIN'),
                    ('TABLE0.BIN','TABLE1.BIN'),('LIVE0.BIN','LIVE1.BIN'),('EDIT0.BIN','EDIT1.BIN'),
                    ('BANK0.BIN','BANK1.BIN'),('BEFORE.BIN','AFTER.BIN')]:
            assert (folder/a).read_bytes()==(folder/b).read_bytes(),(case['case'],a)
        assert (folder/'BANK0.BIN').read_bytes()==bytes(830)
        assert (folder/'STACK.BIN').read_bytes()==b'\xa5'*256
        assert (folder/'BASE0.BIN').read_bytes()[8:]==(folder/'TEST.PRM').read_bytes()
        assert struct.unpack('<6H',(folder/'RESULTS.BIN').read_bytes())[0]==status
        offer=(folder/'OFFER.BIN').read_bytes();assert len(offer)==1212
        current_profile,current_mode,enabled,mask=struct.unpack('<4H',(folder/'LIVE0.BIN').read_bytes())
        assert current_profile==recipe.get('initial_profile',4)
        assert current_mode==(1 if recipe.get('explicit') else recipe.get('initial_mode',0))
        assert enabled==int(current_mode==1) and mask==(127 if current_mode==2 else 255)
        if status:assert offer==b'X'*1212
        else:
            accepted+=1
            change_profile=recipe['profile']!=current_profile;change_mode=recipe['mode']!=current_mode
            keys=(folder/'KEY0.BIN').read_bytes();table=(folder/'TABLE0.BIN').read_bytes()
            if change_profile and recipe.get('kbd'):
                data=(folder/'KEYS.KBD').read_bytes();keys=data[recipe['profile']*948:(recipe['profile']+1)*948]
            if change_mode and recipe['mode']==1:
                path=folder/'PCPLUS.XLT'
                if not path.exists():path=folder/'LIB/PCPLUS.XLT'
                table=path.read_bytes();assert len(table)==256
            assert offer==struct.pack('<4H',recipe['profile'],recipe['mode'],int(change_profile),int(change_mode))+keys+table
        before=bytearray((folder/'PBEFORE.BIN').read_bytes())
        struct.pack_into('<H',before,0x194,recipe['profile']);struct.pack_into('<H',before,0x1e0,recipe['mode'])
        assert (folder/'PROPOSAL.BIN').read_bytes()[830:2094]==before
    assert accepted==10
    helper=paths[4].parent/'INPUTCH.EXE';assert sha(helper)==dos['helper_sha256']==sha(paths[4].parent/'rebuild/INPUTCH.EXE')
    capture(helper);capture(paths[4].parent/'rebuild/INPUTCH.EXE')
    assert helpers['hook_input'] and helpers['binary_sha256']==sha(helper_probe/'TERMINAL.EXE') and len(helpers['cases'])==5
    for case in helpers['cases']:
        assert case['passed'] and case['helpers']==10
        folder=paths[5].parent/case['case']
        for name,digest in case['artifacts'].items():assert sha(folder/name)==digest,name
        for artifact in folder.iterdir():
            if artifact.is_file():capture(artifact)
    regressions=[]
    for port in [1,2]:
        for case in ['normal','bad-token','missing-script','missing-helper','divide','budget','abort']:
            label=f'{args.register_prefix}-{port}-{case}';path=ROOT/'build/register-handoff-dos'/label/'result.json'
            report=read(path);assert report['passed'] and report['hook_input'] and report['cpu']=='8086'
            assert report['parent_sha256']==report['DOS']['binary_sha256']==binary
            assert report['DOS']['passed'] and all(report['DOS']['checks'].values());collect(report);capture(path)
            folder=ROOT/'build/connection-dos'/('register-'+label)
            for snap in report['snapshots']:
                assert sha(folder/f'OWNER{snap["index"]}.BIN')==snap['owner_sha256']
                assert sha(folder/f'CHILD{snap["index"]}.BIN')==snap['child_sha256']
            for artifact in folder.iterdir():
                if artifact.is_file():capture(artifact)
            regressions.append(dict(port=port,case=case,snapshots=len(report['snapshots']),passed=True))
    assert proof['original_inputs']==[] and proof['source_files']==708 and len(proof['products'])==7
    for name,digest in proof['products'].items():assert sha(ROOT/name)==digest,name
    for folder in [base,probe,helper_probe]:assert proof['products'][str((folder/'TERMINAL.EXE').relative_to(ROOT))]==sha(folder/'TERMINAL.EXE')
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_directory_keys_source.py');capture(paths[6].parent/'build.log')
    for name in ['standalone/record_hook_input.py','docs/HOOK_INPUT.md']:sources[name]=sha(ROOT/name)
    result=dict(passed=True,linked_input_cases=39,linked_modem_cases=3394,linked_validation_cases=4822,linked_admission_cases=152,
                input_DOS_cases=dos['cases'],accepted_input_offers=10,helper_attempts=50,register_regressions=regressions,
                source_files=708,products=proof['products'],terminal_sha256=binary,prior_modem_sha256=sha(prior/'TERMINAL.EXE'),
                unchanged_BBS_product_sha256=sha(legacy/'TERMINAL.EXE'),near_bytes=65520,resident_code_bytes=64908,
                added_resident_code_bytes=4,added_hook_bank_bytes=1846,added_config_bank_bytes=125,resource_far_bytes=1214,
                sources=sources,custody_sha256=custody,
                scope='Frozen pre-EXEC input-resource lookup and whole private phase4 offer. Actual helper CWD mutation, decoys, '
                'malformed resources, unchanged active/editor identity and stack guard. No resource/settings/register adoption, '
                'interactive KEY kind2 routing, online UART helper handoff, new live BBS or physical acceptance.')
    target=args.output.resolve();assert target.is_relative_to(ROOT/'build') or target.is_relative_to(ROOT/'docs/validation')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS39 input,3394 modem,4822 return,152 admission;19 input DOS,50 helpers,14 recovery;708 sources/seven products')


if __name__=='__main__':main()
