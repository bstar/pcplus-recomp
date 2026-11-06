#!/usr/bin/env python3
"""Rebuild and test in an isolated public-source tree, without original inputs."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build=a.build.resolve();out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((build/'manifest.json').read_text())
    sources=set(manifest['sources'])|{'standalone/check_context_help.py','standalone/test_context_help_dos.py','standalone/test_context_help_cold.py'}
    for name in sorted(sources):
        source=ROOT/name
        if name in manifest['sources']:assert sha(source)==manifest['sources'][name],name
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    for script,args in (
        ('build_context_help.py',['--output',str(out/'build')]),
        ('check_context_help.py',['--build',str(out/'build')]),
        ('test_context_help_dos.py',['--build',str(out/'build'),'--output',str(out/'dos')]),
    ):
        with (out/(script+'.log')).open('w') as log:
            subprocess.run([sys.executable,str(out/'standalone'/script),*args],cwd=out,stdout=log,stderr=log,check=True)
    rebuilt=json.loads((out/'build/manifest.json').read_text())
    assert rebuilt==manifest
    cpu=json.loads((out/'build/cpu.json').read_text());dos=json.loads((out/'dos/result.json').read_text())
    assert cpu['passed'] and dos['passed']
    report=dict(passed=True,source_files=len(sources),source_sha256={name:sha(out/name) for name in sorted(sources)},products=rebuilt['products'],manifest_sha256=sha(out/'build/manifest.json'),cpu=cpu,dos=dos,scope='Isolated public source tree with pinned toolchain inherited from caller; no original binaries, HLP, configurations, analysis artifacts or prior objects copied. Exact products and manifest reproduced, then source CPU and DOS EXEC tests rerun.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Cold source build:',len(sources),'files;',cpu['cases'],'CPU cases;',dos['checks'],'DOS checks PASS')

if __name__=='__main__':main()
