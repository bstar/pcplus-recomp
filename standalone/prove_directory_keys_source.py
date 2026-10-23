#!/usr/bin/env python3
"""Reproduce the directory KEY/KBD terminal, interpreter/resource and DOS compiler from source."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    sources={};products={}
    for base,leaf in [('terminal-directory-keys','TERMINAL.EXE'),('aspect-help-resource-parent','ASPECT.EXE'),('aspect-compiler-dos','ASPCOMP.EXE')]:
        folder=ROOT/'build'/base;m=json.loads((folder/'manifest.json').read_text());assert not m.get('original_inputs')
        assert sha(folder/leaf)==m['binary_sha256'];products[str((folder/leaf).relative_to(ROOT))]=m['binary_sha256']
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    resource=ROOT/'build/aspect-help-resource-parent/LOCHELP.HLP';products[str(resource.relative_to(ROOT))]=sha(resource)
    with tempfile.TemporaryDirectory(prefix='pcplus-meta-aspect-source-') as name:
        stage=Path(name)
        for n,h in sources.items():
            assert sha(ROOT/n)==h,n
            p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
        commands=[['standalone/build_terminal.py','--external-render','--mouse','--notice-sound','--notice-input','--aspect-keys','--directory-keys'],
                  ['standalone/build_aspect_process.py','--notice-bank','--notice-sound','--notice-input','--notice-help','--help-resource'],
                  ['standalone/build_aspect_compiler_dos.py']]
        with (out/'build.log').open('w') as log:
            for cmd in commands:subprocess.run(['python3',*cmd],cwd=stage,stdout=log,stderr=log,check=True)
        for n,h in products.items():assert sha(stage/n)==sha(ROOT/n)==h,n
    report=dict(passed=True,original_inputs=[],source_files=len(sources),sources=sources,products=products,
        checker_sha256=sha(Path(__file__)),scope=__doc__+' Empty temporary tree contains only the declared source inputs; no original executable, install, image, REA database or prior object is copied.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(sources),'sources',len(products),'products')
if __name__=='__main__':main()
