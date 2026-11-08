#!/usr/bin/env python3
"""Cold public-source rebuild and DOS replay of the opt-in full GET VM pair."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('parent','child','checks','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--parent-profile',choices=('installed','keymap'),default='installed')
 p.add_argument('--compiler',type=Path,default=ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE')
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 parent=json.loads((a.parent/'manifest.json').read_text());child=json.loads((a.child/'manifest.json').read_text())
 compiler=json.loads(a.compiler.with_name('manifest.json').read_text());assert sha(a.compiler)==compiler['binary_sha256']
 checks=json.loads(a.checks.read_text());assert checks['passed'] and checks['GET_VM'] and len(checks['cases'])==(2 if checks.get('lifetime_cases') else 6)
 assert sha(a.parent/'TERMINAL.EXE')==parent['binary_sha256'] and sha(a.child/'ASPECT.EXE')==child['binary_sha256']
 sources={}
 for manifest in (parent,child,compiler):
  assert manifest.get('original_inputs',[])==[]
  for n,h in manifest['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
 for n in ['standalone/prove_get_vm_source.py','standalone/test_get_vm_cli.py','standalone/test_aspect_get_vm_dos.py',
  'standalone/test_aspect_renderer_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py',
  'standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/directory_test_support.py',
  'standalone/terminal_config_fixtures.py','src/aspect/compiler.py','standalone/meta_shared_connection_candidate_recipe.json',
  'standalone/keymap_connection_candidate_recipe.json','standalone/check_aspect_file.py','standalone/build_aspect_file.py',
  'standalone/aspect_file_fixture.c','standalone/aspect_file_fixture.asm','standalone/test_mz_layout_dos.py',
  'standalone/check_aspect_source_compile.py','standalone/check_aspect_source_serial_dos.py','standalone/test_aspect_script_serial_dos.py','standalone/compare_compiler_exec.py','standalone/test_aspect_get_compiler.py','standalone/fixtures/aspect_get_compiler.json']:
  sources[n]=sha(ROOT/n)
 from build_aspect_file import ASM_SOURCES
 for name,n,define in ASM_SOURCES:sources[n]=sha(ROOT/n)
 assert checks['checker_sha256']==sources['standalone/test_aspect_get_vm_dos.py']
 out.mkdir();fresh=out/'source'
 for n,h in sources.items():
  path=Path(n);assert not path.is_absolute() and '..' not in path.parts
  assert path.parts[0] in ('src','standalone','reconstruction','resources') and path.suffix in ('.c','.h','.asm','.inc','.py','.json','.txt'),n
  assert sha(ROOT/path)==h,n
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 def run(args):
  with (out/'build.log').open('a') as log:subprocess.run([sys.executable,*args],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 recipe_name='keymap_connection_candidate_recipe.json' if a.parent_profile=='keymap' else 'meta_shared_connection_candidate_recipe.json'
 recipe=json.loads((fresh/'standalone'/recipe_name).read_text())
 run(['standalone/build_terminal.py',*recipe['terminal_flags'],'--aspect-get-display','--aspect-get-policy','--output-dir','build/parent'])
 run(['-c','import sys,json;from pathlib import Path;sys.path.insert(0,"standalone");from build_aspect_process import main;main(parent_render=True,output=Path("build/child").resolve(),notice_bank=True,notice_sound=True,notice_input=True,notice_help=True,help_resource=True,serial_bank=True,register_handoff=True,custom_irq=True,get_display=True,get_policy=True,get_vm=True,near_globals=True,**json.loads(Path("standalone/keymap_connection_candidate_recipe.json").read_text())["aspect_options"])'])
 assert sha(fresh/'build/parent/TERMINAL.EXE')==parent['binary_sha256']
 assert sha(fresh/'build/child/ASPECT.EXE')==child['binary_sha256']
 run(['-c','import sys,json;from pathlib import Path;sys.path.insert(0,"standalone");from build_aspect_process import main;main(parent_render=True,output=Path("build/default-child").resolve(),notice_bank=True,notice_sound=True,notice_input=True,notice_help=True,help_resource=True,serial_bank=True,register_handoff=True,custom_irq=True,**json.loads(Path("standalone/keymap_connection_candidate_recipe.json").read_text())["aspect_options"])'])
 assert sha(fresh/'build/default-child/ASPECT.EXE')==json.loads((fresh/'standalone/meta_shared_connection_candidate_recipe.json').read_text())['expected_files']['ASPECT.EXE']
 run(['standalone/build_aspect_compiler_dos.py'])
 assert sha(fresh/'build/aspect-compiler-dos/ASPCOMP.EXE')==compiler['binary_sha256']
 selected_compiler='build/aspect-compiler-dos/ASPCOMP.EXE'
 if checks.get('compiler_GET_enabled'):
  run(['standalone/build_aspect_compiler_dos.py','--get','--output','build/get-compiler'])
  selected_compiler='build/get-compiler/ASPCOMP.EXE'
  assert sha(fresh/selected_compiler)==checks['GET_compiler_sha256']
  run(['standalone/test_aspect_get_compiler.py','--compiler-dir','build/get-compiler','--default-compiler-dir','build/aspect-compiler-dos','--output','build/get-grammar'])
 run(['standalone/check_aspect_source_compile.py','--runner','build/default-child/ASPECT.EXE','--compiler',selected_compiler,'--output','build/compiler-baseline'])
 run(['standalone/check_aspect_source_compile.py','--runner','build/child/ASPECT.EXE','--compiler',selected_compiler,'--output','build/compiler-exec'])
 run(['standalone/compare_compiler_exec.py','--baseline','build/compiler-baseline','--candidate','build/compiler-exec','--output','build/compiler-equivalence'])
 run(['standalone/check_aspect_source_serial_dos.py','--runner','build/child/ASPECT.EXE','--compiler',selected_compiler,'--output','build/compiler-serial'])
 run(['standalone/test_get_vm_cli.py','--child','build/child','--output','build/cli'])
 run(['standalone/check_aspect_file.py','--owned-window','--output','build/file'])
 run(['standalone/test_mz_layout_dos.py','--output','build/mz'])
 run(['standalone/test_aspect_get_vm_dos.py','--parent-dir','build/parent','--child-dir','build/child','--output','build/dos',*(['--get-compiler-dir','build/get-compiler'] if checks.get('compiler_GET_enabled') else []),*(['--lifetime-cases'] if checks.get('lifetime_cases') else []),*(['--stream-probe'] if checks.get('stream_probe') else []),*(['--allocation-probe'] if checks.get('allocation_probe') else [])])
 replay=json.loads((fresh/'build/dos/checks.json').read_text());assert replay['passed'] and len(replay['cases'])==len(checks['cases'])
 for previous,current in zip(checks['cases'],replay['cases']):
  assert previous['case']==current['case'] and previous['checks']==current['checks']
  for field in ('passive_observer_header','child_exit_probe','memory_before_EXEC','observer_sha256','observer_source_sha256',*(['GET_generations'] if checks.get('lifetime_cases') else []),*(['allocation_probe'] if checks.get('allocation_probe') else [])):
   assert previous[field]==current[field],(previous['case'],field)
  assert (a.checks.parent/previous['case']/'serial.bin').read_bytes()==(fresh/'build/dos'/current['case']/'serial.bin').read_bytes()
 ordinary=None
 if checks.get('lifetime_cases'):
  run(['standalone/test_aspect_get_vm_dos.py','--parent-dir','build/parent','--child-dir','build/child','--output','build/ordinary','--get-compiler-dir','build/get-compiler','--stream-probe','--allocation-probe'])
  ordinary=json.loads((fresh/'build/ordinary/checks.json').read_text());assert ordinary['passed'] and len(ordinary['cases'])==6
 for n,h in sources.items():assert sha(ROOT/n)==sha(fresh/n)==h,n
 result=dict(passed=True,original_inputs=[],ancestor_git_unavailable=True,source_count=len(sources),sources=sources,
  parent_sha256=parent['binary_sha256'],parent_profile=a.parent_profile,child_sha256=child['binary_sha256'],compiler_sha256=compiler['binary_sha256'],compiler_exec_checks=json.loads((fresh/'build/compiler-exec/checks.json').read_text()),compiler_equivalence=json.loads((fresh/'build/compiler-equivalence/result.json').read_text()),compiler_serial_checks=json.loads((fresh/'build/compiler-serial/checks.json').read_text()),DOS_cases=len(replay['cases']),lifetime_cases=checks.get('lifetime_cases',False),ordinary_GET_checks=ordinary,compiled_GET_cases=replay.get('compiled_GET_cases',0),GET_grammar_checks=json.loads((fresh/'build/get-grammar/result.json').read_text()) if checks.get('compiler_GET_enabled') else None,CLI_cases=7,MZ_layout_checks=json.loads((fresh/'build/mz/result.json').read_text()),owned_read_window_checks=json.loads((fresh/'build/file/checks.json').read_text()),
  scope=__doc__+' Exact executables, DOS check booleans, serial wire and observer/probes. No originals/private files/prior objects/ancestor Git. Selected complete parent recipe plus capability22. Attached GET cases establish only the reported compiler/runtime paths, not full variable/stream/help co-residency, physical hardware or whole-language parity.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS GET VM cold source:',len(sources),'sources; exact pair and DOS replay')
if __name__=='__main__':main()
