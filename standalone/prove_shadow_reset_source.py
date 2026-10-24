#!/usr/bin/env python3
"""Reproduce the owned native width/reset composition without originals or prior objects."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists()
    base=ROOT/'build/terminal-reset-shadow';m=json.loads((base/'manifest.json').read_text())
    assert m['shadow_owner']and m['viewport_bound']and sha(base/'RESET.EXE')==m['binary_sha256']
    assert sha(base/'shadow-owner-normal.obj')==m['normal_owner_object_sha256']
    fresh=out/'source'
    for name,digest in m['sources'].items():
        path=Path(name);assert not path.is_absolute()and'..'not in path.parts and path.parts[0]not in('analysis','build')
        assert path.suffix.lower()not in('.exe','.obj','.o','.img','.prm','.dir','.xlt')and sha(ROOT/path)==digest
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    assert not(fresh/'build').exists()and not(fresh/'analysis').exists()
    with(out/'build.log').open('w')as log:
        subprocess.run([sys.executable,'standalone/build_terminal_reset.py','--viewport','--shadow-owner'],cwd=fresh,
                       stdout=log,stderr=log,check=True,timeout=90)
    rebuilt=fresh/'build/terminal-reset-shadow'
    assert sha(rebuilt/'RESET.EXE')==m['binary_sha256']
    assert(rebuilt/'shadow-owner-normal.obj').is_file()
    for name,digest in m['sources'].items():assert sha(ROOT/name)==sha(fresh/name)==digest
    result=dict(passed=True,binary_sha256=m['binary_sha256'],sources=m['sources'],source_files=len(m['sources']),
                original_inputs=[],normal_owner_compiled=True,build_log_sha256=sha(out/'build.log'),
                checker_sha256=sha(Path(__file__)),scope=__doc__)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS owned reset source reproduction:',len(m['sources']),'sources')


if __name__=='__main__':main()
