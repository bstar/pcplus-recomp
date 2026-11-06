#!/usr/bin/env python3
"""Rebuild an opt-in ASPECT variant and unchanged control in an empty public export."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from build_path_session import ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['probe','control','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--snapshot-lease',action='store_true',help='Select the snapshot-lease application variant instead of the PROGRAM-result diagnostic')
    p.add_argument('--lease-fault-phase',type=int,choices=[0,5,6,8,10,17,22],default=0,help='Rebuild a marked fault variant against its normal snapshot-lease control')
    p.add_argument('--lease-fault-foreign-ds',action='store_true')
    p.add_argument('--lease-fault-kind',choices=['divide','abort','dispatcher'],default='divide')
    p.add_argument('--deferred-script-buffers',action='store_true',help='Compare lazy stream storage with the same snapshot-lease control')
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    assert not a.lease_fault_phase or a.snapshot_lease
    assert not a.lease_fault_foreign_ds or a.lease_fault_phase
    if a.lease_fault_kind!='divide':assert a.lease_fault_phase and not a.lease_fault_foreign_ds
    if a.deferred_script_buffers:assert a.snapshot_lease and not a.lease_fault_phase
    manifests={};binaries={}
    for name in ['probe','control']:
        folder=getattr(a,name).resolve();assert folder.is_relative_to(ROOT/'build')
        m=json.loads((folder/'manifest.json').read_text());binary=folder/'ASPECT.EXE'
        assert sha(binary)==m['binary_sha256']
        diagnostic=name=='probe' and (not a.snapshot_lease or bool(a.lease_fault_phase))
        assert bool(m['diagnostic_program_result_probe'])==diagnostic
        assert bool(m['diagnostic_build'])==diagnostic
        assert bool(m.get('experimental_snapshot_lease'))==bool(a.snapshot_lease and (name=='probe' or a.lease_fault_phase or a.deferred_script_buffers))
        assert bool(m.get('experimental_deferred_script_buffers'))==(a.deferred_script_buffers and name=='probe')
        assert m.get('diagnostic_lease_fault_phase',0)==(a.lease_fault_phase if name=='probe' else 0)
        assert bool(m.get('diagnostic_lease_fault_foreign_ds'))==(a.lease_fault_foreign_ds and name=='probe')
        assert m.get('diagnostic_lease_fault_kind','divide')==(a.lease_fault_kind if name=='probe' else 'divide')
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
    code="import sys;from pathlib import Path;sys.path.insert(0,'standalone');from build_aspect_process import main;selected=sys.argv[2]=='probe';mode=sys.argv[3];phase=int(sys.argv[4]);deferred=sys.argv[7]=='1';main(parent_render=True,output=Path(sys.argv[1]).resolve(),notice_bank=True,notice_sound=True,notice_input=True,notice_help=True,help_resource=True,serial_bank=True,register_handoff=True,custom_irq=True,program_result_probe=selected and (mode=='diagnostic' or phase!=0),snapshot_lease=mode=='lease' and (selected or phase!=0 or deferred),lease_fault_phase=phase if selected and phase else None,lease_fault_foreign_ds=selected and sys.argv[5]=='1',lease_fault_kind=sys.argv[6] if selected else 'divide',defer_script_buffers=selected and deferred)"
    with (out/'build.log').open('w') as log:
        for name in ['probe','control']:
            subprocess.run([sys.executable,'-c',code,'build/'+name,name,'lease' if a.snapshot_lease else 'diagnostic',str(a.lease_fault_phase),'1' if a.lease_fault_foreign_ds else '0',a.lease_fault_kind,'1' if a.deferred_script_buffers else '0'],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
            assert sha(fresh/'build'/name/'ASPECT.EXE')==sha(binaries[name]),name
    for name,h in sources.items():assert sha(ROOT/name)==sha(fresh/name)==h,name
    report=dict(passed=True,source_commit=revision,source_count=len(sources),sources=sources,
        probe_sha256=sha(binaries['probe']),control_sha256=sha(binaries['control']),original_inputs=[],ancestor_git_unavailable=True,
        snapshot_lease=a.snapshot_lease,
        lease_fault_phase=a.lease_fault_phase,
        lease_fault_foreign_ds=a.lease_fault_foreign_ds,
        lease_fault_kind=a.lease_fault_kind,
        deferred_script_buffers=a.deferred_script_buffers,
        scope=__doc__+' Exact executable equality through pinned Nix; runtime tests and hardware acceptance remain separate. PROGRAM-result diagnostics are not deployable replacements.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(sources),'public sources; exact diagnostic and control')
if __name__=='__main__':main()
