#!/usr/bin/env python3
"""Reproduce notice input and both quiet notice products from source alone."""
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path
from build_native_mouse import ROOT,sha
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--bios-fallback',action='store_true');args=p.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    sources={};products={}
    for base,binary in [('notice-input-bios' if args.bios_fallback else 'notice-input','NINPUT.EXE'),('notice-bank','NOTICE.EXE'),('notice-bank-uart','NUART.EXE')]:
        m=json.loads((ROOT/'build'/base/'manifest.json').read_text());assert not m['original_inputs']
        assert sha(ROOT/'build'/base/binary)==m['binary_sha256'];products[f'build/{base}/{binary}']=m['binary_sha256']
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
    with tempfile.TemporaryDirectory(prefix='pcplus-notice-input-source-') as name:
        stage=Path(name)
        for n,h in sources.items():
            assert sha(ROOT/n)==h;target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
        assert not (stage/'analysis').exists() and not (stage/'build').exists()
        with (out/'build.log').open('w') as log:subprocess.run(['python3',str(stage/'standalone/build_notice_input.py'),*(['--bios-fallback'] if args.bios_fallback else [])],cwd=stage,stdout=log,stderr=log,check=True)
        for n,h in products.items():assert sha(stage/n)==sha(ROOT/n)==h,n
    r=dict(bios_fallback=args.bios_fallback,passed=True,source_files=len(sources),sources=sources,products=products,checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__+' No original executable, PRM, installed media, existing objects or REA database in the fresh tree. Separate input component; no whole-application gate closes.')
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,source_files=len(sources),products=len(products))))
if __name__=='__main__':main()
