#!/usr/bin/env python3
"""Rebuild experimental PROGRAM notice parent/diagnostic from declared sources only."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    out=parser.parse_args().output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    bases=['build/aspect-notice-parent','build/aspect-notice-fault','build/notice-bank','build/notice-bank-uart']
    sources={};products={};manifests={}
    for base in bases:
        path=ROOT/base/'manifest.json';m=json.loads(path.read_text());assert m['original_inputs']==[]
        manifests[str(path.relative_to(ROOT))]=sha(path)
        for name,h in m['sources'].items():assert sha(ROOT/name)==h;sources[name]=h
        name='ASPECT.EXE' if 'aspect-' in base else 'NUART.EXE' if base.endswith('uart') else 'NOTICE.EXE'
        assert sha(ROOT/base/name)==m['binary_sha256'];products[base+'/'+name]=m['binary_sha256']
    wm=json.loads((ROOT/'build/notice-window/manifest.json').read_text())
    products.update({'build/notice-window/'+name:h for name,h in wm['products'].items()})
    with tempfile.TemporaryDirectory(prefix='pcplus-program-notice-') as name:
        stage=Path(name)
        for path,h in sources.items():
            dest=stage/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,dest)
        assert not (stage/'analysis').exists() and not (stage/'build').exists()
        with (out/'build.log').open('w') as log:
            for options in [['--notice-bank'],['--notice-bank','--fault-diagnostic']]:
                subprocess.run(['python3',str(stage/'standalone/build_aspect_process.py'),*options],cwd=stage,stdout=log,stderr=log,check=True)
        for path,h in products.items():assert sha(ROOT/path)==sha(stage/path)==h,path
    result=dict(passed=True,original_inputs=[],source_files=len(sources),inputs=sources,products=products,manifests=manifests,checker_sha256=sha(Path(__file__)),scope=__doc__+' Fresh tree contains no original executable, install, REA database or previous objects.35 source-built products include both experimental ASPECT parents and33 notice/window products. Full application and normal105-slot publication remain open.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,source_files=len(sources),products=len(products))))
if __name__=='__main__':main()
