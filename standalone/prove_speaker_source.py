#!/usr/bin/env python3
"""Rebuild speaker and optional notice composition from declared source-only inputs."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);out=parser.parse_args().output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    sources={};products={}
    for base,binary in [('build/speaker','SPEAKER.EXE'),('build/speaker-notice','NSOUND.EXE'),('build/notice-bank','NOTICE.EXE'),('build/notice-bank-uart','NUART.EXE')]:
        m=json.loads((ROOT/base/'manifest.json').read_text());assert not m['original_inputs'];assert sha(ROOT/base/binary)==m['binary_sha256']
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
        products[base+'/'+binary]=m['binary_sha256']
    with tempfile.TemporaryDirectory(prefix='pcplus-speaker-source-') as name:
        stage=Path(name)
        for n,h in sources.items():
            assert sha(ROOT/n)==h;npath=stage/n;npath.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,npath)
        assert not (stage/'analysis').exists() and not (stage/'build').exists()
        with (out/'build.log').open('w') as log:subprocess.run(['python3',str(stage/'standalone/build_speaker_notice.py')],cwd=stage,stdout=log,stderr=log,check=True)
        for n,h in products.items():assert sha(stage/n)==sha(ROOT/n)==h,n
    r=dict(passed=True,original_inputs=[],source_files=len(sources),sources=sources,products=products,checker_sha256=sha(Path(__file__)),scope=__doc__+' Both new executables and both normal notice components reproduce exactly. No original executable, install, REA database or existing object in the fresh tree. Full application and physical acceptance remain open.')
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,source_files=r['source_files'],products=len(r['products']))))
if __name__=='__main__':main()
