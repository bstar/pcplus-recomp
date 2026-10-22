#!/usr/bin/env python3
"""Reproduce the window products in a fresh declared-source-only directory."""
import argparse,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/notice-window';m=json.loads((base/'manifest.json').read_text());assert m['original_inputs']==[]
    with tempfile.TemporaryDirectory(prefix='pcplus-window-source-') as name:
        stage=Path(name)
        for path,digest in m['sources'].items():
            source=ROOT/path;assert sha(source)==digest
            target=stage/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        assert not (stage/'analysis').exists()
        with (out/'build.log').open('w') as log:subprocess.run(['python3',str(stage/'standalone/build_notice_window.py')],cwd=stage,stdout=log,stderr=log,check=True)
        fresh=json.loads((stage/'build/notice-window/manifest.json').read_text());assert fresh==m
        for path,digest in m['products'].items():assert sha(base/path)==sha(stage/'build/notice-window'/path)==digest
    r=dict(passed=True,source_files=len(m['sources']),products=m['products'],inputs=m['sources'],manifest_sha256=sha(base/'manifest.json'),checker_sha256=sha(Path(__file__)),scope=__doc__+' Original executable, install, analysis database and earlier build products are absent. This proves the declared component products, not a complete application.')
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,source_files=r['source_files'],products=len(r['products']))))
if __name__=='__main__':main()
