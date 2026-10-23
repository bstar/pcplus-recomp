#!/usr/bin/env python3
"""Rebuild the native-input retention fixtures and ordinary ASPECT from source."""
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path
from build_notice_input_exit import ROOT,OUT,sha
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    out=p.parse_args().output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    m=json.loads((OUT/'manifest.json').read_text());assert not m['original_inputs']
    for n,h in m['products'].items():assert sha(OUT/n)==h
    with tempfile.TemporaryDirectory(prefix='pcplus-input-exit-source-') as name:
        stage=Path(name)
        for n,h in m['sources'].items():
            assert sha(ROOT/n)==h;target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
        assert not (stage/'analysis').exists() and not (stage/'build').exists()
        with (out/'build.log').open('w') as log:subprocess.run(['python3',str(stage/'standalone/build_notice_input_exit.py')],cwd=stage,stdout=log,stderr=log,check=True)
        for n,h in m['products'].items():assert sha(stage/'build/notice-input-exit'/n)==sha(OUT/n)==h,n
    r=dict(passed=True,original_inputs=[],source_files=len(m['sources']),sources=m['sources'],products={f'build/notice-input-exit/{n}':h for n,h in m['products'].items()},checker_sha256=sha(Path(__file__)),scope=__doc__+' No original executable, REA database, media, existing objects or maintained EXE in the fresh tree. The actual ordinary CLI is rebuilt before its map is used to compile the controlled probe.')
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,source_files=r['source_files'],products=len(r['products']))))
if __name__=='__main__':main()
