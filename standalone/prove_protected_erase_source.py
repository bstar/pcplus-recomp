#!/usr/bin/env python3
"""Rebuild protected erase, overlapping-pane clears and their application regressions."""
import argparse,ast,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from prove_native_bank_parent_source import ROOT,SPECIAL,SPECIAL_FLAGS
BASE='terminal-native-bank-transaction'
FULL=SPECIAL+'-transaction'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--nested',action='store_true');a=p.parse_args();a.nested=True
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 products=[('terminal',[]),('terminal-native-bank',['--native-reset-bank']),
  (BASE,['--native-reset-bank','--native-reset-transaction']),(FULL,SPECIAL_FLAGS+['--native-reset-transaction'])]
 sources={};expected={}
 for folder,flags in products:
  m=load(ROOT/'build'/folder/'manifest.json');assert sha(ROOT/'build'/folder/'TERMINAL.EXE')==m['binary_sha256']
  expected[folder]=m['binary_sha256']
  for name,digest in m['sources'].items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
 children={'aspect-runner':'ASPECT.EXE','aspect-register-parent-custom-irq':'ASPECT.EXE','aspect-compiler-dos':'ASPCOMP.EXE'}if a.nested else{}
 child_hashes={}
 for folder,leaf in children.items():
  m=load(ROOT/'build'/folder/'manifest.json');child_hashes[folder]=sha(ROOT/'build'/folder/leaf);assert child_hashes[folder]==m['binary_sha256']
  for name,digest in m['sources'].items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
 csi=load(ROOT/'build/csi/manifest.json');csi_hash=csi['binary_sha256']
 assert sha(ROOT/'build/csi/CSI.EXE')==csi_hash
 for name,digest in csi['sources'].items():
  assert sha(ROOT/name)==digest,name
  assert name not in sources or sources[name]==digest,name
  sources[name]=digest
 for name in ['standalone/build_csi.py','reconstruction/ansi/dispatch-provenance.json']:sources[name]=sha(ROOT/name)
 pending=[ROOT/'standalone/record_protected_erase.py',ROOT/'standalone/check_protected_erase_live.py',ROOT/'standalone/check_wide_clear_live.py',ROOT/'standalone/test_aspect_wide_dos.py',ROOT/'standalone/check_aspect_viewport_ownership.py',ROOT/'standalone/build_aspect_renderer_policy.py',ROOT/'standalone/check_aspect_renderer_policy.py',Path(__file__),ROOT/'standalone/check_reset_live.py',ROOT/'standalone/test_reset_live_dos.py',ROOT/'standalone/check_native_bank_parent.py',ROOT/'standalone/check_width_edit_live.py',ROOT/'standalone/check_character_edit_live.py',ROOT/'standalone/check_width_fields_live.py',ROOT/'standalone/check_attribute_repair_live.py',ROOT/'standalone/check_line_attributes_live.py',ROOT/'standalone/check_csi_relocation.py',ROOT/'standalone/check_scroll_fields_live.py',ROOT/'standalone/check_line_edit_live.py',ROOT/'standalone/check_reset_fields_live.py',ROOT/'standalone/check_shared_screen_live.py',ROOT/'standalone/check_wide_redisplay_live.py',ROOT/'standalone/test_wide_viewer_dos.py',ROOT/'standalone/check_redisplay_live.py',ROOT/'standalone/check_command_menu_live.py',ROOT/'standalone/check_menu_pending_live.py',ROOT/'standalone/check_viewport_live.py'];seen=set()
 if a.nested:
  pending.extend(ROOT/'standalone'/name for name in ['test_nested_compiler_memory_dos.py','check_aspect_compiler_stack.py','check_aspect_compiler_workspace.py','check_compiler_arena_fallback.py'])
 while pending:
  path=pending.pop().resolve()
  if path in seen:continue
  seen.add(path);sources[str(path.relative_to(ROOT))]=sha(path)
  for node in ast.walk(ast.parse(path.read_text())):
   names=[item.name for item in node.names]if isinstance(node,ast.Import)else[node.module]if isinstance(node,ast.ImportFrom)else[]
   for name in names:
    if name:
     local=ROOT/'standalone'/(name.split('.')[0]+'.py')
     if local.is_file():pending.append(local)
 if a.nested:
  from check_compiler_arena_fallback import INPUTS
  for name in INPUTS:sources[name]=sha(ROOT/name)
  for path in (ROOT/'src/aspect').glob('compiler_*.h'):sources[str(path.relative_to(ROOT))]=sha(path)
  sources['src/aspect/compiler.py']=sha(ROOT/'src/aspect/compiler.py')
  for path in (ROOT/'standalone/fixtures').glob('aspect*.json'):sources[str(path.relative_to(ROOT))]=sha(path)
 for name in ['standalone/line_attributes_watch.asm','standalone/wide_viewer_watch.asm','standalone/aspect_wide_watch.asm','nix/flake.nix','nix/flake.lock','tools/dev']:sources[name]=sha(ROOT/name)
 fresh=out/'source'
 for name,digest in sources.items():
  path=Path(name);assert not path.is_absolute()and'..'not in path.parts and path.parts[0]not in('build','analysis','original','originals','install')
  assert path.suffix.lower()not in('.exe','.com','.obj','.o','.img','.prm','.dir','.xlt')
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
 assert not(fresh/'build').exists()
 logs={};reports={}
 def run(label,argv,report=None):
  log=out/(label+'.log')
  with log.open('w')as stream:subprocess.run([sys.executable,*argv],cwd=fresh,stdout=stream,stderr=stream,check=True,timeout=360)
  logs[label]=sha(log)
  if report:
   path=fresh/report;data=load(path);assert data['passed'];reports[report]=sha(path)
 def parallel(jobs):
  # Read-only MZ/map inputs, isolated emulators and distinct result paths.
  # Wait on every future; one failed check prevents a completed proof.
  with ThreadPoolExecutor(max_workers=4)as pool:
   futures=[pool.submit(run,*job)for job in jobs]
   for future in futures:future.result()
 for folder,flags in products:
  run('build-'+folder,['standalone/build_terminal.py',*flags])
  assert sha(fresh/'build'/folder/'TERMINAL.EXE')==expected[folder],folder
  if 'transaction'in folder:
   run('bank-'+folder,['standalone/check_native_bank_parent.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/native-bank-parent-checks.json')
   run('shared-'+folder,['standalone/check_shared_screen_live.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/shared-screen-checks.json')
   parallel([
    ('protected-'+folder,['standalone/check_protected_erase_live.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/protected-erase-checks.json'),
    ('clear-'+folder,['standalone/check_wide_clear_live.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/wide-clear-checks.json'),
    ('aspect-owner-'+folder,['standalone/check_aspect_viewport_ownership.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/aspect-viewport-ownership-checks.json'),
    ('viewer-'+folder,['standalone/check_wide_redisplay_live.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/wide-viewer-checks.json'),
    ('fields-'+folder,['standalone/check_reset_fields_live.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/reset-field-checks.json'),
    ('scroll-'+folder,['standalone/check_scroll_fields_live.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/scroll-field-checks.json'),
    ('edits-'+folder,['standalone/check_width_edit_live.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/width-edit-checks.json'),
    ('model-'+folder,['standalone/check_reset_live.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/reset-live-checks.json')])
  elif not flags:
   parallel([
    ('viewer80',['standalone/check_redisplay_live.py'],'build/terminal/redisplay-checks.json'),
    ('menu80',['standalone/check_command_menu_live.py'],'build/terminal/command-menu-checks.json'),
    ('pending80',['standalone/check_menu_pending_live.py'],'build/terminal/menu-pending-checks.json'),
    ('viewport80',['standalone/check_viewport_live.py'],'build/terminal/viewport-live-checks.json'),
    ('characters80',['standalone/check_character_edit_live.py'],'build/terminal/character-edit-live-checks.json'),
    ('repair80',['standalone/check_attribute_repair_live.py'],'build/attribute-repair/live-checks.json'),
    ('lines80',['standalone/check_line_attributes_live.py'],'build/terminal/line-attributes-live-checks.json'),
    ('policy80',['standalone/check_line_edit_live.py'],'build/terminal/line-edit-live-checks.json')])
  elif flags:run('cold',['standalone/check_native_bank_parent.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/native-bank-parent-checks.json')
 run('build-render-policy',['standalone/build_aspect_renderer_policy.py'])
 run('render-policy',['standalone/check_aspect_renderer_policy.py'],'build/aspect-renderer-policy/checks.json')
 run('build-csi',['standalone/build_csi.py'])
 assert sha(fresh/'build/csi/CSI.EXE')==csi_hash
 run('relocate-csi',['standalone/check_csi_relocation.py'],'build/csi-relocation/result.json')
 for folder,label in [(BASE,'base'),(FULL,'special')]:
  run('DOS-'+label,['standalone/test_reset_live_dos.py','--terminal','build/'+folder+'/TERMINAL.EXE','--output','build/DOS-'+label,'--character-edits','--field-edits','--scroll-fields','--active-width-fields'],
   'build/DOS-'+label+'/checks.json')
  assert all(load(fresh/'build'/('DOS-'+label)/'checks.json')['checks'].values())
  run('DOS-hidden-'+label,['standalone/test_reset_live_dos.py','--terminal','build/'+folder+'/TERMINAL.EXE','--output','build/DOS-hidden-'+label,'--hidden-status','--character-edits','--field-edits','--scroll-fields','--active-width-fields'],
   'build/DOS-hidden-'+label+'/checks.json')
 for folder,label in [(BASE,'base'),(FULL,'special')]:
  for hidden in (False,True):
   name='WIDE-DOS-'+('hidden-'if hidden else'')+label
   run(name,['standalone/test_wide_viewer_dos.py','--terminal','build/'+folder+'/TERMINAL.EXE','--output','build/'+name,*(['--hidden-status']if hidden else[])],'build/'+name+'/checks.json')
 if a.nested:
  run('build-default-runner',['standalone/build_aspect_runner.py'])
  run('build-runner',['standalone/build_aspect_process.py','--notice-bank','--notice-sound','--notice-input','--notice-help','--help-resource','--serial-bank','--register-handoff','--custom-irq'])
  run('build-compiler',['standalone/build_aspect_compiler_dos.py'])
  for folder,leaf in children.items():assert sha(fresh/'build'/folder/leaf)==child_hashes[folder],folder
  for case,port,irq,chooser in [('explicit',2,5,False),('fallback',1,4,False),('chain',2,7,False),('rejected',1,5,False),('explicit',2,5,True)]:
   label='chooser-'+case if chooser else case
   report='build/nested/'+label+'/result.json'
   run('nested-'+label,['standalone/test_nested_compiler_memory_dos.py','--output','build/nested/'+label,'--case',case,'--port',str(port),'--irq',str(irq),
    '--terminal','build/'+FULL+'/TERMINAL.EXE','--runner','build/aspect-register-parent-custom-irq/ASPECT.EXE','--splash-key',*(['--chooser']if chooser else[]),'--log-collisions','32'if case=='explicit'else'0'],report)
 for hidden in (False,True):
  for window in (False,True):
   for compile_in_dos in (False,True):
    name='ASPECT-DOS-'+('hidden-'if hidden else'visible-')+('window-'if window else'')+('source'if compile_in_dos else'precompiled')
    run(name,['standalone/test_aspect_wide_dos.py','--terminal','build/'+FULL+'/TERMINAL.EXE','--runner','build/aspect-register-parent-custom-irq/ASPECT.EXE','--output','build/'+name,*(['--hidden-status']if hidden else[]),*(['--window']if window else[]),*(['--compiler','build/aspect-compiler-dos/ASPCOMP.EXE']if compile_in_dos else[])],'build/'+name+'/checks.json')
 for hidden in (False,True):
  for window in (False,True):
   for compile_in_dos in (False,True):
    for color in (False,True):
     name='PROTECTED-DOS-'+('hidden-'if hidden else'visible-')+('window-'if window else'')+('source-'if compile_in_dos else'precompiled-')+('color'if color else'mono')
     run(name,['standalone/test_aspect_wide_dos.py','--terminal','build/'+FULL+'/TERMINAL.EXE','--runner','build/aspect-register-parent-custom-irq/ASPECT.EXE','--output','build/'+name,'--protected-erase',*(['--field-color']if color else[]),*(['--hidden-status']if hidden else[]),*(['--window']if window else[]),*(['--compiler','build/aspect-compiler-dos/ASPCOMP.EXE']if compile_in_dos else[])],'build/'+name+'/checks.json')
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 result=dict(passed=True,source_files=len(sources),sources=sources,products=expected,child_products=child_hashes,nested_compiler_verified=a.nested,csi_product=csi_hash,reports=reports,logs=logs,
  checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__,limitations=[
   'Local views own physical80-column frames over a132-column live plane; ASPECT rendering composes through checked parent RPC. Peer width, other child/UI families and partial-width wrapped scrolling remain open.',
   'DOS witnesses call from real25-row startup, with default visible or fixture-hidden status; rollback/IRQ faults use the hardware model.',
   'Wide source trials use a compact read-only observer, while precompiled trials capture complete screen/field planes; hardware acceptance remains open.'if a.nested else'Nested compiler admission is a separate gate and is not established by this proof.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS protected erase source: four exact products, prior regressions and16 protected DOS cases; nested compiler gate '+('passed'if a.nested else'separate'))
if __name__=='__main__':main()
