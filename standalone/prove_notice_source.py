#!/usr/bin/env python3
"""Reproduce notice/window/UART executables in a fresh source-only tree."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    m=read(ROOT/'build/notice-uart/manifest.json');n=read(ROOT/'build/notice/manifest.json');w=read(ROOT/'build/notice-window/manifest.json');assert all(r['original_inputs']==[] for r in [m,n,w])
    products={'build/notice-uart/NUART.EXE':m['binary_sha256'],'build/notice/NOTICE.EXE':n['binary_sha256'],**{'build/notice-window/'+name:digest for name,digest in w['products'].items()}}
    with tempfile.TemporaryDirectory(prefix='pcplus-serviced-notice-') as name:
        stage=Path(name)
        for path,digest in m['sources'].items():
            assert sha(ROOT/path)==digest;target=stage/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,target)
        assert not (stage/'analysis').exists()
        with (out/'build.log').open('w') as log:subprocess.run(['python3',str(stage/'standalone/build_notice_uart.py')],cwd=stage,stdout=log,stderr=log,check=True)
        assert read(stage/'build/notice-uart/manifest.json')==m and read(stage/'build/notice/manifest.json')==n and read(stage/'build/notice-window/manifest.json')==w
        for path,digest in products.items():assert sha(ROOT/path)==sha(stage/path)==digest
    result=dict(passed=True,source_files=len(m['sources']),inputs=m['sources'],products=products,manifest_sha256={name:sha(ROOT/name) for name in ['build/notice-uart/manifest.json','build/notice/manifest.json','build/notice-window/manifest.json']},checker_sha256=sha(Path(__file__)),scope=__doc__+' No original executable, install, REA database or prior build object is present in the new tree. Pinned Nix shell supplies NASM/Watcom; normal and diagnostic notice/window sources compile. Component proof, not a full application build.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,source_files=result['source_files'],products=len(products))))
if __name__=='__main__':main()
