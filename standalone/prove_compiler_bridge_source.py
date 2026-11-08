#!/usr/bin/env python3
"""Cold rebuild and exact full-parent DOS replay of the opt-in compiler bridge.

No originals, prior objects or ancestor Git are available inside the export.
This proves only the supplied emulator cases, not physical or full ASPECT parity.
"""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
 p = argparse.ArgumentParser(description=__doc__)
 for name in ('parent', 'child', 'compiler', 'output'):
  p.add_argument('--'+name, type=Path, required=True)
 p.add_argument('--checks', type=Path, action='append', required=True)
 p.add_argument('--lab-payload',type=Path)
 p.add_argument('--connection-package',type=Path)
 p.add_argument('--termination-checks',type=Path,action='append',default=[])
 a = p.parse_args(); out = a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifests = [json.loads((folder/'manifest.json').read_text()) for folder in (a.parent,a.child,a.compiler)]
 parent,child,compiler = manifests
 assert parent['experimental_compiler_lease_bridge']
 assert child['experimental_compiler_parent_lease'] and compiler['experimental_get_compiler']
 sources = {}
 for folder,leaf,m in zip((a.parent,a.child,a.compiler),('TERMINAL.EXE','ASPECT.EXE','ASPCOMP.EXE'),manifests):
  assert sha(folder/leaf)==m['binary_sha256'] and m.get('original_inputs',[])==[]
  for name,digest in m['sources'].items():
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
 extras = ['standalone/prove_compiler_bridge_source.py','standalone/keymap_connection_candidate_recipe.json',
  'standalone/test_aspect_get_vm_dos.py','standalone/test_aspect_renderer_dos.py',
  'standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py',
  'standalone/modem_fixtures.py','standalone/directory_test_support.py','standalone/terminal_config_fixtures.py',
  'src/aspect/compiler.py','standalone/compiler_bridge_recovery_observer.py','standalone/compiler_bridge_repeat_observer.py','standalone/test_compiler_bridge_termination_dos.py','standalone/compiler_bridge_termination_observer.asm','standalone/compiler_bridge_reuse_observer.py']
 for name in extras:sources[name]=sha(ROOT/name)
 payload=None
 if a.lab_payload:
  payload=json.loads((a.lab_payload/'package.json').read_text())
  assert payload['passed'] and not payload.get('original_inputs')
  for leaf,folder in (('TERMINAL.EXE',a.parent),('ASPECT.EXE',a.child),('ASPCOMP.EXE',a.compiler)):
   assert payload['products'][leaf]==sha(folder/leaf)
  for name,digest in payload['sources'].items():
   assert sha(ROOT/name)==digest and (name not in sources or sources[name]==digest),name
   sources[name]=digest
  for name in ('standalone/test_compiler_bridge_lab_payload.py','lab/bbs/product_inputs.py'):sources[name]=sha(ROOT/name)

 connection=None
 if a.connection_package:
  assert a.lab_payload,'Connection package requires the complete lab/Help source closure'
  connection=json.loads((a.connection_package/'manifest.json').read_text())
  assert connection['experimental_compiler_lease_bridge'] and connection['parent_render_capability']==23
  assert not connection['original_inputs'] and not connection['card_written']
  for leaf,digest in connection['files'].items():assert sha(a.connection_package/connection['dos_directory']/leaf)==digest,leaf
  for leaf,digest in payload['products'].items():assert connection['files'][leaf]==digest,leaf
  for name,digest in connection['sources'].items():
   assert sha(ROOT/name)==digest and (name not in sources or sources[name]==digest),name
   sources[name]=digest
  for name in ('standalone/check_compiler_bridge_package.py','standalone/archive_connection_test_package.py'):sources[name]=sha(ROOT/name)
 reports=[json.loads(path.read_text()) for path in a.checks]
 assert any(r.get('source_lease_cases') and len(r['cases'])==2 for r in reports)
 for r in reports:
  assert r['passed'] and r['GET_VM'] and r['GET_compiler_sha256']==compiler['binary_sha256']
  assert r['checker_sha256']==sources['standalone/test_aspect_get_vm_dos.py']
  for case in r['cases']:
   assert case['binary_sha256']==parent['binary_sha256']
 termination=[json.loads(path.read_text()) for path in a.termination_checks]
 for r in termination:
  assert r['passed'] and r['parent_sha256']==parent['binary_sha256'] and r['child_sha256']==child['binary_sha256'] and r['compiler_sha256']==compiler['binary_sha256']
  for name,digest in r['sources'].items():assert sources[name]==digest,name
 out.mkdir(); fresh=out/'source'
 for name,digest in sources.items():
  n=Path(name)
  assert not n.is_absolute() and '..' not in n.parts
  assert n.parts[0] in ('src','standalone','reconstruction','resources','lab')
  assert n.suffix in ('.c','.h','.asm','.inc','.py','.json','.txt')
  assert sha(ROOT/n)==digest,name
  target=fresh/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
 assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 def run(args):
  with (out/'replay.log').open('a') as log:
   subprocess.run([sys.executable,*args],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 recipe=json.loads((fresh/'standalone/keymap_connection_candidate_recipe.json').read_text())
 run(['standalone/build_terminal.py',*recipe['terminal_flags'],'--aspect-get-display','--aspect-get-policy',
      '--compiler-lease-bridge',*(['--chat-send-mode'] if parent.get('experimental_chat_send_mode') else []),'--output-dir','build/parent'])
 assert child['startup_heap_growth_bytes'] in (128,256,512)
 run(['-c','import json,sys;from pathlib import Path;sys.path.insert(0,"standalone");from build_aspect_process import main;main(parent_render=True,output=Path("build/child").resolve(),notice_bank=True,notice_sound=True,notice_input=True,notice_help=True,help_resource=True,serial_bank=True,register_handoff=True,custom_irq=True,get_display=True,get_policy=True,get_vm=True,near_globals=True,compiler_parent_lease=True,heap_growth_bytes='+str(child['startup_heap_growth_bytes'])+',defer_help_resource='+str(bool(child.get('experimental_deferred_help_resource')))+',disk_script_snapshots='+str(bool(child.get('experimental_disk_script_snapshots')))+',**json.loads(Path("standalone/keymap_connection_candidate_recipe.json").read_text())["aspect_options"])'])
 run(['standalone/build_aspect_compiler_dos.py','--get','--output','build/compiler'])
 artifacts={}
 if parent.get('experimental_chat_send_mode'):
  assert sha(fresh/'build/parent/PCCHAT.OVL')==sha(a.parent/'PCCHAT.OVL')
  artifacts['PCCHAT.OVL']=sha(a.parent/'PCCHAT.OVL')
 for folder,leaves,original in [('parent',('TERMINAL.EXE','PCCOMP.OVL','PCLINE.OVL','PCMETA.OVL'),a.parent),
                                ('child',('ASPECT.EXE',),a.child),('compiler',('ASPCOMP.EXE',),a.compiler)]:
  for leaf in leaves:
   assert sha(fresh/'build'/folder/leaf)==sha(original/leaf),leaf
   artifacts[leaf]=sha(original/leaf)
 lab_payload=None
 if payload:
  run(['standalone/package_compiler_bridge_lab.py','--parent','build/parent','--child','build/child','--compiler','build/compiler','--output','build/lab-payload'])
  staged=json.loads((fresh/'build/lab-payload/package.json').read_text());assert staged['products']==payload['products']
  run(['standalone/test_compiler_bridge_lab_payload.py','--payload','build/lab-payload','--output','build/lab-contract'])
  contract=json.loads((fresh/'build/lab-contract/result.json').read_text());assert contract['passed']
  lab_payload=dict(products=staged['products'],package_sha256=sha(fresh/'build/lab-payload/package.json'),contract_sha256=sha(fresh/'build/lab-contract/result.json'),checks=contract['checks'])
 connection_result=None
 if connection:
  run(['standalone/build_setup.py','--mouse','--notice-sound','--custom-irq',*(['--chat-mode'] if connection.get('experimental_chat_send_mode') else []),'--output-dir','build/setup'])
  run(['standalone/build_xlt_editor.py','--output-dir','build/translation'])
  run(['standalone/build_keymap_helper.py','--output','build/keymap'])
  run(['standalone/package_connection_test.py','--terminal','build/lab-payload/TERMINAL.EXE','--runner','build/child/ASPECT.EXE',
       '--compiler','build/compiler/ASPCOMP.EXE','--setup','build/setup/PRMEDIT.EXE','--translation','build/translation/XLTEDIT.EXE',
       '--keymap-helper','build/keymap/PCKEYMAP.EXE','--dos-directory',connection['dos_directory'],
       '--source-base-commit',connection['source_base_commit'],'--output','build/connection-package'])
  staged=json.loads((fresh/'build/connection-package/manifest.json').read_text());assert staged['files']==connection['files']
  run(['standalone/check_compiler_bridge_package.py','--terminal','build/lab-payload/TERMINAL.EXE','--runner','build/child/ASPECT.EXE',
       '--package','build/connection-package','--output','build/connection-contract'])
  run(['standalone/archive_connection_test_package.py','--package','build/connection-package','--output','build/connection-archive'])
  contract=json.loads((fresh/'build/connection-contract/result.json').read_text());archive=json.loads((fresh/'build/connection-archive/result.json').read_text())
  assert contract['passed'] and archive['passed'] and archive['files']==connection['files']
  connection_result=dict(files=staged['files'],contract_cases=len(contract['cases']),archive_sha256=archive['archive_sha256'],archive_bytes=archive['archive_bytes'])
 replays=[]
 families=('source_lease_reuse_cases','source_lease_close_cases','source_lease_begin_cases','source_lease_repeat_cases','source_lease_cleanup_cases','source_lease_recovery_cases','source_lease_fault_cases','source_lease_cases','source_memory_cases','policy_cases','storage_cases','when_error_cases','when_cases','lifetime_cases')
 for i,(path,r) in enumerate(zip(a.checks,reports)):
  leaf='build/replay-'+str(i)
  flags=['--'+key.replace('_','-') for key in families if r.get(key)]
  flags += ['--'+key.replace('_','-') for key in ('allocation_probe','stream_probe') if r.get(key)]
  if r.get('CONNECTED_probe'):flags+=['--connected-probe']
  if 'get_watch_data:' in (path.parent/r['cases'][0]['case']/'observer.asm').read_text():flags+=['--watchdog']
  run(['standalone/test_aspect_get_vm_dos.py','--parent-dir','build/parent','--child-dir','build/child',
       '--get-compiler-dir','build/compiler','--cpu',r['emulated_cpu'],'--output',leaf,*flags])
  replay=json.loads((fresh/leaf/'checks.json').read_text())
  assert replay['passed'] and len(replay['cases'])==len(r['cases'])
  for old,new in zip(r['cases'],replay['cases']):
   for key in ('case','checks','passive_observer_header','child_exit_probe','memory_before_EXEC',
               'observer_sha256','observer_source_sha256','allocation_probe','compiler_EXEC_memory',
               'GET_generations','GET_error_retirement','GET_pending_WHEN_gate','GET_waiting_before_WHEN','GET_observed_width'):
    assert old.get(key)==new.get(key),(old['case'],key)
   if 'restore_recovery' in old:
    # The checksum covers mutable parent memory, including elapsed state.
    # Each run must pass the kernel's complete checksum/EOF restoration gate;
    # across runs compare the invariant capture, not that per-run checksum.
    def invariant(case):
     capture=case['restore_recovery']
     return dict(capture,kernel={k:v for k,v in capture['kernel'].items() if k!='crc'})
    assert invariant(old)==invariant(new),(old['case'],'restore_recovery')
   if 'prepare_failure' in old:
    def prepare_invariant(case):
     capture=case['prepare_failure']
     return dict(capture,kernel={k:v for k,v in capture['kernel'].items() if k!='crc'})
    assert prepare_invariant(old)==prepare_invariant(new),(old['case'],'prepare_failure')
   if 'restore_cleanup' in old:
    def cleanup_invariant(case):
     capture=case['restore_cleanup']
     return dict(sample=capture['sample'],kernel={k:v for k,v in capture['kernel'].items() if k!='crc'},
      backups=[{k:v for k,v in backup.items() if k not in ('sha256','crc16')} for backup in capture['backups']])
    # Each preserved backup must match its own captured full-tail checksum;
    # mutable parent bytes need not have the same digest between executions.
    assert cleanup_invariant(old)==cleanup_invariant(new),(old['case'],'restore_cleanup')
   if 'compiler_reuse' in old:
    def reuse_invariant(case):
     capture=case['compiler_reuse']
     return dict(capture,second_kernel={k:v for k,v in capture['second_kernel'].items() if k!='crc'})
    assert reuse_invariant(old)==reuse_invariant(new),(old['case'],'compiler_reuse')
   if 'compiler_repeat' in old:
    def repeat_invariant(case):
     return [dict(sample=row['sample'],kernel={k:v for k,v in row['kernel'].items() if k!='crc'}) for row in case['compiler_repeat']]
    assert repeat_invariant(old)==repeat_invariant(new),(old['case'],'compiler_repeat')
   assert (path.parent/old['case']/'serial.bin').read_bytes()==(fresh/leaf/new['case']/'serial.bin').read_bytes()
  replays.append(dict(cases=len(replay['cases']),checks_sha256=sha(fresh/leaf/'checks.json'),
                      source_lease_cases=replay.get('source_lease_cases',False)))
 termination_replays=[]
 for i,(path,r) in enumerate(zip(a.termination_checks,termination)):
  leaf='build/termination-'+str(i)
  flags=[arg for case in r['cases'] for arg in ('--case',case['case'])]
  run(['standalone/test_compiler_bridge_termination_dos.py','--parent','build/parent','--child','build/child','--compiler','build/compiler','--output',leaf,*flags])
  replay=json.loads((fresh/leaf/'checks.json').read_text());assert replay['passed'] and len(replay['cases'])==len(r['cases'])
  for old,new in zip(r['cases'],replay['cases']):
   for key in ('case','checks','sample','BIOS_text_hex','observer_sha256'):
    assert old[key]==new[key],(old['case'],key)
   for key in ('kernel_before','kernel_after'):
    assert {k:v for k,v in old[key].items() if k!='crc'}=={k:v for k,v in new[key].items() if k!='crc'},(old['case'],key)
   # Full video/report/backup digests can contain mutable parent clock data.
   # Each run still checks its own full backup CRC and exact fatal BIOS text.
   assert (path.parent/old['case']/'serial.bin').read_bytes()==(fresh/leaf/new['case']/'serial.bin').read_bytes()
  termination_replays.append(dict(cases=len(replay['cases']),checks_sha256=sha(fresh/leaf/'checks.json'),expected_fail_stop=True))
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 result=dict(passed=True,original_inputs=[],ancestor_git_unavailable=True,sources=sources,source_count=len(sources),
             artifacts=artifacts,lab_payload=lab_payload,connection_package=connection_result,replays=replays,DOS_cases=sum(r['cases'] for r in replays),termination_replays=termination_replays,termination_cases=sum(r['cases'] for r in termination_replays),
             scope=__doc__,physical_verified=False,installed_changed=False)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS compiler bridge cold source:',len(sources),'sources;',result['DOS_cases'],'normal DOS cases;',result['termination_cases'],'expected fail-stops')

if __name__=='__main__':main()
