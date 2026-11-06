#!/usr/bin/env python3
"""Rebuild the marked PROGRAM-result diagnostic and unchanged control in an empty public export."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from build_path_session import ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['probe','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    manifests={};binaries={}
    for name in ['probe','control']:
        folder=getattr(a,name).resolve();assert folder.is_relative_to(ROOT/'build')
        m=json.loads((folder/'manifest.json').read_text());binary=folder/'ASPECT.EXE'
        assert sha(binary)==m['binary_sha256']
        assert bool(m['diagnostic_program_result_probe'])==(name=='probe')
        assert bool(m['diagnostic_build'])==(name=='probe')
        manifests[name]=m;binaries[name]=binary
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',revision],cwd=ROOT,text=True).splitlines()
    names={n for m in manifests.values() for n in m['sources']}|{n for n in tracked if n.startswith('standalone/') and n.endswith('.py')}|{'nix/flake.nix','nix/flake.lock','tools/dev'}
    fresh=out/'source';sources={};out.mkdir()
    for name in sorted(names):
        path=Path(name)
        assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ['build','original','originals','analysis','install','.git']
        assert path.suffix.lower() not in ['.exe','.com','.obj','.prm','.fon','.img','.db']
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT))
        sources[name]=sha(target);assert sha(ROOT/path)==sources[name],name
        stamp=(ROOT/path).stat();os.utime(target,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
    env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
    assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
    code="import sys;from pathlib import Path;sys.path.insert(0,'standalone');from build_aspect_process import main;main(parent_render=True,output=Path(sys.argv[1]).resolve(),notice_bank=True,notice_sound=True,notice_input=True,notice_help=True,help_resource=True,serial_bank=True,register_handoff=True,custom_irq=True,program_result_probe=sys.argv[2]=='probe')"
    with (out/'build.log').open('w') as log:
        for name in ['probe','control']:
            subprocess.run([sys.executable,'-c',code,'build/'+name,name],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
            assert sha(fresh/'build'/name/'ASPECT.EXE')==sha(binaries[name]),name
    for name,h in sources.items():assert sha(ROOT/name)==sha(fresh/name)==h,name
    report=dict(passed=True,source_commit=revision,source_count=len(sources),sources=sources,
        probe_sha256=sha(binaries['probe']),control_sha256=sha(binaries['control']),original_inputs=[],ancestor_git_unavailable=True,
        scope=__doc__+' Exact executable equality through pinned Nix; runtime tests and hardware acceptance remain separate. Diagnostic image is not a deployable replacement.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(sources),'public sources; exact diagnostic and control')
if __name__=='__main__':main()
