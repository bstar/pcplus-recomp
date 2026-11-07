#!/usr/bin/env python3
"""Rebuild and exercise the Alt-P parent from an isolated declared source tree."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);fresh=out/'source'
 m=json.loads(binary.with_name('manifest.json').read_text())
 assert m['experimental_line_port'] and m['binary_sha256']==sha(binary)
 sources=dict(m['sources'])
 extra=['standalone/prove_line_port_terminal_source.py','standalone/line_port_profile.json',
  'standalone/test_line_port_terminal_dos.py','standalone/test_connection_dos.py',
  'standalone/path_dialog_watch.asm','standalone/line_port_readonly.asm',
  'standalone/modem_fixtures.py','standalone/directory_fixtures.py',
  'standalone/terminal_config_fixtures.py','standalone/test_terminal.py',
  'standalone/directory_test_support.py']
 if m.get('experimental_meta_editor'):extra.append('standalone/test_meta_front_dos.py')
 for name in extra:sources[name]=sha(ROOT/name)
 for name,digest in sources.items():
  rel=Path(name);assert not rel.is_absolute() and '..'not in rel.parts
  assert rel.parts[0]not in ('build','analysis','install','.git')
  assert rel.suffix.lower()not in ('.exe','.com','.obj','.img','.prm','.dir','.xlt','.db')
  assert sha(ROOT/rel)==digest,name
  target=fresh/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
 assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode!=0
 flags=json.loads((fresh/'standalone/line_port_profile.json').read_text())
 if m.get('experimental_line_port_overlay'):flags.append('--line-port-overlay')
 if m.get('experimental_meta_services'):flags.append('--meta-services')
 if m.get('experimental_meta_editor_module'):flags.append('--meta-editor-module')
 if m.get('experimental_meta_editor'):flags.append('--meta-editor')
 rebuilt=fresh/'build/rebuilt'
 with(out/'build.log').open('w')as log:
  subprocess.run([sys.executable,'standalone/build_terminal.py',*flags,'--output-dir',str(rebuilt)],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 assert sha(rebuilt/'TERMINAL.EXE')==sha(binary)
 if m.get('experimental_line_port_overlay'):
  assert sha(rebuilt/'PCLINE.OVL')==sha(binary.with_name('PCLINE.OVL'))==m['line_port_overlay']['sha256']
 if m.get('experimental_meta_editor_module'):assert sha(rebuilt/'PCMETA.OVL')==sha(binary.with_name('PCMETA.OVL'))==m['meta_editor_overlay']['sha256']
 runs=[]
 for case in ('save','serviced','readonly','portbusy'):
  target=fresh/('build/live-'+case)
  with(out/(case+'.log')).open('w')as log:
   subprocess.run([sys.executable,'standalone/test_line_port_terminal_dos.py','--terminal',str(rebuilt/'TERMINAL.EXE'),'--output',str(target),'--case',case],cwd=fresh,env=env,stdout=log,stderr=log,check=True,timeout=45)
  result=json.loads((target/'result.json').read_text());assert result['passed']
  runs.append(dict(case=case,checks=result['checks'],result_sha256=sha(target/'result.json')))
 meta_runs=[]
 if m.get('experimental_meta_editor'):
  for case in ('save','cancel','missing'):
   target=fresh/('build/meta-'+case)
   with(out/('meta-'+case+'.log')).open('w')as log:
    subprocess.run([sys.executable,'standalone/test_meta_front_dos.py','--terminal',str(rebuilt/'TERMINAL.EXE'),'--output',str(target),'--case',case],cwd=fresh,env=env,stdout=log,stderr=log,check=True,timeout=45)
   v=json.loads((target/'result.json').read_text());assert v['passed']
   meta_runs.append(dict(case=case,checks=v['checks'],result_sha256=sha(target/'result.json')))
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 result=dict(passed=True,binary_sha256=sha(binary),source_count=len(sources),sources=sources,
  runs=runs,meta_runs=meta_runs,ancestor_git_unavailable=True,original_inputs=[],build_log_sha256=sha(out/'build.log'),
  limitations=['Exact optional parent and four real DOS synthetic-peer checks. No physical modem/BBS or complete application-parity claim.',
   'Only declared public sources; no original/private/analysis/prior objects or Git metadata. Outer pinned Nix supplies tools.'])
 if m.get('experimental_line_port_overlay'):result['overlay_sha256']=sha(rebuilt/'PCLINE.OVL')
 if m.get('experimental_meta_editor_module'):result['meta_overlay_sha256']=sha(rebuilt/'PCMETA.OVL')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Alt-P public-source proof:',len(sources),'files; exact parent and four DOS application cases passed')


if __name__=='__main__':main()
