#!/usr/bin/env python3
"""Rebuild matching PRM sound parent and ordinary/diagnostic ASPECT from source only."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--mouse',action='store_true');parser.add_argument('--input',action='store_true');args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    if args.input:assert args.mouse
    sources={};products={}
    for base,binary in [('build/setup-mouse-notice-sound' if args.mouse else 'build/setup-notice-sound','PRMEDIT.EXE'),('build/terminal-mouse-notice-input' if args.input else 'build/terminal-mouse-notice-sound' if args.mouse else 'build/terminal-notice-sound','TERMINAL.EXE'),('build/aspect-notice-input-parent' if args.input else 'build/aspect-notice-sound-parent','ASPECT.EXE'),('build/aspect-notice-input-fault' if args.input else 'build/aspect-notice-sound-fault','ASPECT.EXE')]:
        m=json.loads((ROOT/base/'manifest.json').read_text());assert m.get('original_inputs',[])==[];assert sha(ROOT/base/binary)==m['binary_sha256']
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
        products[base+'/'+binary]=m['binary_sha256']
    with tempfile.TemporaryDirectory(prefix='pcplus-program-sound-source-') as name:
        stage=Path(name)
        for n,h in sources.items():
            assert sha(ROOT/n)==h,n;target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
        assert not (stage/'analysis').exists() and not (stage/'build').exists()
        commands=[['standalone/build_setup.py','--notice-sound'],['standalone/build_terminal.py','--external-render','--notice-sound'],['standalone/build_aspect_process.py','--notice-bank','--notice-sound'],['standalone/build_aspect_process.py','--notice-bank','--notice-sound','--fault-diagnostic']]
        if args.mouse:
            commands[0].append('--mouse');commands[1].append('--mouse')
        if args.input:
            for command in commands[1:]:command.append('--notice-input')
        with (out/'build.log').open('w') as log:
            for command in commands:subprocess.run(['python3',*command],cwd=stage,stdout=log,stderr=log,check=True)
        for n,h in products.items():assert sha(stage/n)==sha(ROOT/n)==h,n
    report=dict(native_notice_input=args.input,mouse=args.mouse,passed=True,original_inputs=[],source_files=len(sources),sources=sources,products=products,checker_sha256=sha(Path(__file__)),scope=__doc__+' Empty tree contains no original executable, install, private PRM, REA database or previous objects. Native sound and notice source dependencies are rebuilt by the declared builders.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,source_files=len(sources),products=len(products))))
if __name__=='__main__':main()
