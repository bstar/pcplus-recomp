#!/usr/bin/env python3
"""Reject missing, stale or undeclared keyboard companions before archiving."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
from package_connection_test import ROOT,sha,keymap_companion,reviewed_keymap_profile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('helper','package','output'):
        parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args()
    out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir()
    helper=args.helper.resolve();package=args.package.resolve()
    assert helper.is_relative_to(ROOT/'build') and package.is_relative_to(ROOT/'build')
    original=json.loads(helper.with_name('result.json').read_text())
    blob=helper.read_bytes();rows=[]
    reviewed=json.loads((ROOT/'standalone/keymap_helper_profile.json').read_text())
    for name,field,value in [('unknown-version','contract',99),('wrong-profile-size','profile_bytes',947),
            ('empty-file-allowed','minimum_profiles',0),('excess-profiles','maximum_profiles',34),
            ('wrong-maximum-size','maximum_KBD_bytes',31285),('padding-allowed','preserves_file_length',False),
            ('wrong-recovery-exit','recovery_exit',0),('wrong-arguments','arguments','filename')]:
        profile=copy.deepcopy(reviewed);profile[field]=value
        try:reviewed_keymap_profile(profile);accepted=True
        except (AssertionError,KeyError):accepted=False
        assert not accepted,name
        rows.append(dict(case=name,accepted=False))
    fixture=out/'helper';fixture.mkdir();binary=fixture/'PCKEYMAP.EXE'
    for name in ('valid','disabled','missing-selection','undeclared','missing-binary','missing-proof','corrupt','forged-proof-hash','not-passed','original-input','stale-source','foreign-source','non-source'):
        proof=copy.deepcopy(original);binary.write_bytes(blob)
        selected=binary;parent={'experimental_keymap_editor':True}
        if name=='disabled':selected=None;parent={}
        elif name=='missing-selection':selected=None
        elif name=='undeclared':parent={}
        elif name=='missing-binary':binary.unlink()
        elif name in ('corrupt','forged-proof-hash'):
            binary.write_bytes(bytes([blob[0]^1])+blob[1:])
            if name=='forged-proof-hash':proof['binary_sha256']=sha(binary)
        elif name=='not-passed':proof['passed']=False
        elif name=='original-input':proof['original_inputs']=['original.exe']
        elif name=='stale-source':proof['sources'][next(iter(proof['sources']))]='0'*64
        elif name=='foreign-source':proof['sources']['../outside.py']='0'*64
        elif name=='non-source':proof['sources']['src/forbidden.exe']='0'*64
        record=binary.with_name('result.json');record.write_text(json.dumps(proof))
        if name=='missing-proof':record.unlink()
        try:
            files,_,_=keymap_companion(parent,selected);accepted=True
        except (AssertionError,FileNotFoundError):accepted=False
        assert accepted==(name in ('valid','disabled')),name
        if name=='valid':assert files['PCKEYMAP.EXE'].read_bytes()==blob
        if name=='disabled':assert files=={}
        rows.append(dict(case=name,accepted=accepted))
    for name in ('archive-missing','archive-corrupt','archive-undeclared','archive-forged-hash','archive-wrong-contract'):
        folder=out/name;shutil.copytree(package,folder)
        m=json.loads((folder/'manifest.json').read_text());leaf=folder/m['dos_directory']/'PCKEYMAP.EXE'
        if name=='archive-missing':del m['files']['PCKEYMAP.EXE']
        elif name in ('archive-corrupt','archive-forged-hash'):
            leaf.write_bytes(b'wrong helper')
            if name=='archive-forged-hash':m['files']['PCKEYMAP.EXE']=m['products']['PCKEYMAP.EXE']['binary_sha256']=sha(leaf)
        elif name=='archive-undeclared':m.pop('experimental_keymap_editor')
        else:m['products']['PCKEYMAP.EXE']['contract']+=1
        (folder/'manifest.json').write_text(json.dumps(m))
        target=out/(name+'-zip')
        with (out/(name+'.log')).open('w') as log:
            result=subprocess.run([sys.executable,str(ROOT/'standalone/archive_connection_test_package.py'),'--package',str(folder),'--output',str(target)],stdout=log,stderr=log)
        assert result.returncode and not target.exists(),name
        rows.append(dict(case=name,accepted=False,archive_started=False))
    assert helper.read_bytes()==blob
    names=['standalone/check_keymap_package_contract.py','standalone/package_connection_test.py','standalone/archive_connection_test_package.py','standalone/keymap_helper_profile.json']
    result=dict(passed=True,cases=rows,helper_sha256=sha(helper),sources={name:sha(ROOT/name) for name in names},scope=__doc__+' Isolated public fixtures only; no child execution, private settings or deployment.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS keyboard package contract:',len(rows),'cases')


if __name__=='__main__':main()
