#!/usr/bin/env python3
"""Reproduce native sound products from declared sources in an empty tree."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);out=parser.parse_args().output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    manifest=ROOT/'build/program-sound/manifest.json';m=json.loads(manifest.read_text());assert not m['original_inputs']
    with tempfile.TemporaryDirectory(prefix='pcplus-sound-source-') as name:
        stage=Path(name)
        for n,h in m['sources'].items():
            assert sha(ROOT/n)==h;npath=stage/n;npath.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,npath)
        assert not (stage/'analysis').exists() and not (stage/'build').exists()
        with (out/'build.log').open('w') as log:subprocess.run(['python3',str(stage/'standalone/build_program_sound.py')],cwd=stage,stdout=log,stderr=log,check=True)
        for n,h in m['products'].items():assert sha(stage/'build/program-sound'/n)==sha(ROOT/'build/program-sound'/n)==h,n
    r=dict(passed=True,original_inputs=[],source_files=len(m['sources']),sources=m['sources'],products=m['products'],manifest_sha256=sha(manifest),checker_sha256=sha(Path(__file__)),scope=__doc__)
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,source_files=r['source_files'],products=len(r['products']))))
if __name__=='__main__':main()
