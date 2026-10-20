#!/usr/bin/env python3
"""Build real parent EXEC and child exit-ownership diagnostics."""
import json,subprocess
from pathlib import Path
import build_break_owner as breaker
ROOT=breaker.ROOT;OUT=ROOT/'build/exit-owner';sha=breaker.sha
def main():
    breaker.main(banked=True);OUT.mkdir(parents=True,exist_ok=True)
    pm=json.loads((breaker.process.OUT/'manifest.json').read_text())
    bm=json.loads((breaker.OUT/'manifest.json').read_text())
    process=[str(breaker.process.OUT/(Path(u['file']).stem+'.obj')) for u in pm['units']]
    process.append(str(breaker.process.OUT/'native_process_state.obj'))
    bank=[str(breaker.OUT/(n+'.obj')) for n in ['install','restore','ignore','break_binding','break_owner_far']]
    source=ROOT/'src/process/exit_owner.asm';obj=OUT/'exit_owner.obj'
    subprocess.run(['nasm','-fobj',str(source),'-o',str(obj)],check=True)
    common=['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/process')]
    subprocess.run([*common,'-DNATIVE_PROCESS_DIAGNOSTIC','-fm=EXITPAR.map','-fe=EXITPAR.EXE',
        str(ROOT/'src/process/native_process.c'),str(ROOT/'standalone/exit_owner_parent.c'),*process],cwd=OUT,check=True)
    subprocess.run([*common,'-DNATIVE_BREAK_FAR','-fm=EXITKID.map','-fe=EXITKID.EXE',
        str(ROOT/'src/process/exit_owner.c'),str(ROOT/'standalone/exit_owner_child.c'),str(obj),*bank],cwd=OUT,check=True)
    sources={**pm['sources'],**bm['sources']}
    for name in ['src/process/exit_owner.asm','src/process/exit_owner.c','src/process/exit_owner.h',
                 'standalone/exit_owner_parent.c','standalone/exit_owner_child.c','standalone/build_exit_owner.py']:
        sources[name]=sha(ROOT/name)
    manifest=dict(passed=True,original_inputs=[],sources=sources,
        products={n:sha(OUT/n) for n in ['EXITPAR.EXE','EXITKID.EXE']},
        scope='Actual recovered DOS EXEC parent and guarded far-owner child. Test live-lease callback is explicit controlled input; real ASPECT lifecycle is tested separately.')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Built EXITPAR.EXE and EXITKID.EXE')
if __name__=='__main__':main()
