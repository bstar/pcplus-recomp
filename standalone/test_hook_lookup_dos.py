#!/usr/bin/env python3
"""Repeat the source-only lookup and composed DOS regression cohort."""
import argparse,concurrent.futures,json,re,subprocess,sys
from pathlib import Path
from build_guarded_helper import ROOT,LOOKUP
from hook_lookup_fixtures import CASES
from prove_guarded_helper_source import sha
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();assert re.fullmatch('[A-Za-z0-9_-]+',out.name);out.mkdir(parents=True)
 terminal=ROOT/'build'/LOOKUP/'TERMINAL.EXE';reports=[]
 def run(script,*arguments):
  subprocess.run([sys.executable,'standalone/'+script,*map(str,arguments)],cwd=ROOT,check=True)
 def port(number):
  completed=[]
  for case in CASES:
   folder=out/f'final-lookup-{number}-{case}'
   run('test_hook_apply_dos.py','--terminal',terminal,'--lookup-case',case,'--online','--port',number,'--mode',0,'--output',folder);completed.append(folder/'result.json')
  for kind,modes in [('apply',range(13)),('online',(0,1,2,3,5,6,9,10)),('ownership',(0,1))]:
   for mode in modes:
    folder=out/f'final-{kind}-{number}-{mode:02}'
    if kind=='ownership':run('test_guarded_hook_ownership_dos.py','--terminal',terminal,'--port',number,'--mode',mode,'--output',folder)
    else:run('test_hook_apply_dos.py','--terminal',terminal,*(['--online']if kind=='online'else[]),'--port',number,'--mode',mode,'--output',folder)
    completed.append(folder/'result.json')
  for case in('normal','bad-token','missing-script','missing-helper','divide','budget','abort'):
   label=out.name+f'-register-{number}-{case}'
   run('test_register_handoff_dos.py','--terminal',terminal,'--label',label,'--port',number,'--case',case)
   completed.append(ROOT/'build/register-handoff-dos'/label/'result.json')
  for case in('explicit','fallback','chain','rejected'):
   folder=out/f'final-compiler-{number}-{case}'
   run('test_nested_compiler_memory_dos.py','--terminal',terminal,'--port',number,'--case',case,'--output',folder);completed.append(folder/'result.json')
  return completed
 run('check_hook_lookup.py','--output',out/'final-linked-source')
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  for completed in pool.map(port,(1,2)):reports.extend(completed)
 run('test_terminal_traps_dos.py','--mouse','--terminal-prefix',terminal.parent,'--label',out.name+'-traps')
 run('test_terminal_cancel_dos.py','--mouse','--terminal',terminal,'--label',out.name+'-cancel')
 run('check_guarded_helper_usage_dos.py','--terminal',terminal,'--output',out/'final-usage')
 reports += [ROOT/'build/terminal-trap-tests'/(out.name+'-traps')/'result.json',
  ROOT/'build/terminal-cancel-tests'/(out.name+'-cancel')/'result.json',out/'final-usage/result.json',out/'final-linked-source/result.json']
 assert all(json.loads(path.read_text())['passed']for path in reports)
 result=dict(passed=True,binary_sha256=sha(terminal),checker_sha256=sha(Path(__file__)),
  reports={str(path.relative_to(ROOT)):sha(path)for path in reports},scope=__doc__+' No native-original, live BBS or physical modem claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS lookup DOS cohort:',len(reports),'reports')
if __name__=='__main__':main()
