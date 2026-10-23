#!/usr/bin/env python3
"""Reproduce the directory KEY/KBD terminal, interpreter/resource and DOS compiler from source."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--process-bank',action='store_true');ap.add_argument('--session-capture',action='store_true');ap.add_argument('--session-projection',action='store_true');ap.add_argument('--session-baseline',action='store_true');ap.add_argument('--serial-bank',action='store_true');ap.add_argument('--register-handoff',action='store_true');ap.add_argument('--session-controls',action='store_true');a=ap.parse_args()
    if a.session_capture:assert a.process_bank
    if a.session_projection:assert a.session_capture
    if a.session_baseline:assert a.session_projection
    if a.register_handoff:assert a.session_baseline and a.serial_bank
    if a.session_controls:assert a.register_handoff
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    sources={};products={}
    parent='terminal-directory-keys'+('-process-bank' if a.process_bank else '')+('-session-capture' if a.session_capture else '')
    if a.session_projection:parent+='-projection'
    if a.session_baseline:parent+='-bound'
    if a.register_handoff:parent+='-registers'
    if a.session_controls:parent+='-controls'
    child='aspect-register-parent' if a.register_handoff else 'aspect-serial-bank-parent' if a.serial_bank else 'aspect-help-resource-parent'
    targets=[(parent,'TERMINAL.EXE'),(child,'ASPECT.EXE'),('aspect-compiler-dos','ASPCOMP.EXE')]
    if a.session_capture:targets.append(('setup-mouse-notice-sound','PRMEDIT.EXE'))
    if a.session_projection:targets.append((parent+'-probe','TERMINAL.EXE'))
    for base,leaf in targets:
        folder=ROOT/'build'/base;m=json.loads((folder/'manifest.json').read_text());assert not m.get('original_inputs')
        assert sha(folder/leaf)==m['binary_sha256'];products[str((folder/leaf).relative_to(ROOT))]=m['binary_sha256']
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    resource=ROOT/'build'/child/'LOCHELP.HLP';products[str(resource.relative_to(ROOT))]=sha(resource)
    with tempfile.TemporaryDirectory(prefix='pcplus-meta-aspect-source-') as name:
        stage=Path(name)
        for n,h in sources.items():
            rel=Path(n)
            assert not rel.is_absolute() and '..' not in rel.parts
            assert rel.parts[0] not in ('build','analysis','install','original','originals','.git')
            assert rel.suffix.lower() in ('.asm','.c','.h','.py','.inc','.json'),n
            assert (ROOT/n).is_file() and not (ROOT/n).is_symlink(),n
            assert sha(ROOT/n)==h,n
            p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
        commands=[['standalone/build_terminal.py','--external-render','--mouse','--notice-sound','--notice-input','--aspect-keys','--directory-keys'],
                  ['standalone/build_aspect_process.py','--notice-bank','--notice-sound','--notice-input','--notice-help','--help-resource'],
                  ['standalone/build_aspect_compiler_dos.py']]
        if a.process_bank:commands[0].append('--process-bank')
        if a.session_capture:commands[0].append('--session-capture')
        if a.session_projection:commands[0].append('--session-projection')
        if a.session_baseline:commands[0].append('--session-baseline')
        if a.serial_bank:commands[1].append('--serial-bank')
        if a.register_handoff:
            commands[0].append('--register-handoff');commands[1].append('--register-handoff')
        if a.session_controls:commands[0].append('--session-controls')
        if a.session_projection:commands.append([*commands[0],'--projection-probe'])
        if a.session_capture:commands.append(['standalone/build_setup.py','--mouse','--notice-sound'])
        with (out/'build.log').open('w') as log:
            for cmd in commands:subprocess.run(['python3',*cmd],cwd=stage,stdout=log,stderr=log,check=True)
        for n,h in products.items():assert sha(stage/n)==sha(ROOT/n)==h,n
    report=dict(passed=True,original_inputs=[],source_files=len(sources),sources=sources,products=products,
        checker_sha256=sha(Path(__file__)),scope=__doc__+' Empty temporary tree contains only the declared source inputs; no original executable, install, image, REA database or prior object is copied.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(sources),'sources',len(products),'products')
if __name__=='__main__':main()
