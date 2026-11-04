#!/usr/bin/env python3
"""Rebuild all five connection-test executables and stage identical public files."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from package_connection_test import ROOT,sha,validate_dos_directory
from prove_phone_log_startup_terminal import flags


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    package,output=a.package.resolve(),a.output.resolve()
    assert package.is_relative_to(ROOT/'build') and output.is_relative_to(ROOT/'build') and not output.exists()
    record=json.loads((package/'manifest.json').read_text());revision=record['source_base_commit']
    dos_directory=validate_dos_directory(record.get('dos_directory','PCPLUSSE'))
    for leaf,h in record['files'].items():assert sha(package/dos_directory/leaf)==h
    products={leaf:ROOT/'build'/identity['folder'] for leaf,identity in record['products'].items()}
    manifests={leaf:json.loads((folder/'manifest.json').read_text()) for leaf,folder in products.items()}
    tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',revision],cwd=ROOT,text=True).splitlines()
    names=set(record['sources'])|{n for n in tracked if n.startswith('standalone/') and n.endswith('.py')}|{'nix/flake.nix','nix/flake.lock','tools/dev'}
    output.mkdir();fresh=output/'source';sources={}
    for name in sorted(names):
        relative=Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0] not in ('build','analysis','original','originals','install','.git')
        assert relative.suffix.lower() not in ('.exe','.obj','.com','.img','.db','.prm','.fon')
        data=subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)
        target=fresh/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        stamp=(ROOT/name).stat();os.utime(target,ns=(stamp.st_atime_ns,stamp.st_mtime_ns));sources[name]=sha(target)
        assert sha(ROOT/name)==sources[name],name
    env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(output))
    assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
    terminal_out=fresh/'build/reproduction-terminal'
    runner_out=fresh/'build/reproduction-aspect'
    runner_code=("import sys;from pathlib import Path;sys.path.insert(0,'standalone');"
                 "from build_aspect_process import main;"
                 "main(parent_render=True,output=Path(sys.argv[1]),notice_bank=True,notice_sound=True,"
                 "notice_input=True,notice_help=True,help_resource=True,serial_bank=True,"
                 "register_handoff=True,custom_irq=True)")
    commands=[['standalone/build_terminal.py',*flags(manifests['TERMINAL.EXE'],True),'--output-dir',str(terminal_out)],
        ['-c',runner_code,str(runner_out)],
        ['standalone/build_aspect_compiler_dos.py'],['standalone/build_setup.py','--mouse','--notice-sound','--custom-irq'],['standalone/build_xlt_editor.py']]
    with (output/'build.log').open('w') as log:
        for command in commands:subprocess.run([sys.executable,*command],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
        rebuilt={'TERMINAL.EXE':terminal_out/'TERMINAL.EXE','ASPECT.EXE':runner_out/'ASPECT.EXE',
            'ASPCOMP.EXE':fresh/'build/aspect-compiler-dos/ASPCOMP.EXE',
            'PRMEDIT.EXE':fresh/'build/setup-mouse-notice-sound-custom-irq/PRMEDIT.EXE',
            'XLTEDIT.EXE':fresh/'build/xlt-editor/XLTEDIT.EXE'}
        for leaf,path in rebuilt.items():assert sha(path)==record['files'][leaf],leaf
        command=[sys.executable,'standalone/package_connection_test.py','--output',str(fresh/'build/connection-package'),'--source-base-commit',revision,'--dos-directory',dos_directory]
        for option,leaf in zip(('terminal','runner','compiler','setup','translation'),('TERMINAL.EXE','ASPECT.EXE','ASPCOMP.EXE','PRMEDIT.EXE','XLTEDIT.EXE')):command+=['--'+option,str(rebuilt[leaf])]
        subprocess.run(command,cwd=fresh,env=env,stdout=log,stderr=log,check=True)
    staged=json.loads((fresh/'build/connection-package/manifest.json').read_text());assert staged['files']==record['files'] and staged['dos_directory']==dos_directory
    assert all(sha(ROOT/n)==h and sha(fresh/n)==h for n,h in sources.items())
    result={'passed':True,'source_commit':revision,'dos_directory':dos_directory,'source_count':len(sources),'sources':sources,'original_inputs':[],
        'ancestor_git_unavailable':True,'package_manifest_sha256':sha(package/'manifest.json'),'files':staged['files'],'rebuilt_executables':{n:sha(p) for n,p in rebuilt.items()},
        'build_log_sha256':sha(output/'build.log'),'scope':__doc__+' Empty export; no originals,objects,configuration/card files or Git metadata. Separate runtime/hardware acceptance required.'}
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS:',len(sources),'public sources; five exact executables; ten exact package files')
if __name__=='__main__':main()
