#!/usr/bin/env python3
"""Record direct XLTEDIT launch and adoption with separate CPU/DOS/build evidence."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from check_setup_model import image
from check_directory_live import word
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def sources(report):
 for path,digest in report.get('sources',{}).items():assert sha(path)==digest,path
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);a=p.parse_args()
 assert a.label and all(c.isalnum() or c in '-_' for c in a.label)
 runtime=sha('build/terminal/TERMINAL.EXE');editor=sha('build/xlt-editor/XLTEDIT.EXE')
 manifest=read('build/terminal/manifest.json');assert manifest['binary_sha256']==runtime;sources(manifest)
 child=read('build/xlt-editor/manifest.json');assert child['binary_sha256']==editor;sources(child)
 cpu=read('build/terminal/translation-edit-checks.json');assert cpu['passed'] and cpu['inputs']==55 and cpu['binary_sha256']==runtime;sources(cpu)
 dos_path=Path('build/translation-edit-dos')/a.label/'checks.json';dos=read(dos_path)
 assert dos['passed'] and dos['binary_sha256']==runtime and dos['editor_sha256']==editor and len(dos['cases'])==8;sources(dos)
 offline=read('build/xlt-editor/checks.json');assert offline['passed'] and len(offline['cases'])==22;sources(offline)
 assert offline['binaries']['XLTEDIT.EXE']==editor
 for name,digest in offline['binaries'].items():assert sha(Path('build/xlt-editor')/name)==digest,name
 artifacts=[dos_path,*map(Path,['build/terminal/manifest.json','build/xlt-editor/manifest.json','build/terminal/translation-edit-checks.json','build/xlt-editor/checks.json'])]
 for case in dos['cases']:
  assert case['passed'] and all(case['checks'].values())
  folder=Path('build/setup-startup')/case['case'];assert sha(folder/'TERMINAL.EXE')==runtime
  if not case['case'].endswith('missing-child'):assert sha(folder/'XLTEDIT.EXE')==editor
  assert read(folder/'result.json')==case
  before=(ROOT/folder/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(ROOT/folder/'AFTER.BIN').read_bytes()
  assert (ROOT/folder/'TEST.PRM').read_bytes()==word(image(),0x1e0,1),case['case']
  artifacts.extend(p.relative_to(ROOT) for p in sorted((ROOT/folder).rglob('*')) if p.is_file())
 for case in offline['cases']:
  folder=ROOT/'build/xlt-editor/tests'/case['case']
  assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
  artifacts.extend(p.relative_to(ROOT) for p in sorted(folder.rglob('*')) if p.is_file())
 frames=read('build/terminal/config-far-checks.json');assert frames['passed'] and frames['binary_sha256']==runtime and len(frames['rejected_mutations'])==276
 memory=manifest['memory_layout'];assert memory['near_bytes']==64720 and memory['resident_code_bytes']==62222
 baseline=read('build/checkpoints/18b9/manifest.json')
 published= json.loads(subprocess.check_output(['git','show','4a1295a:docs/validation/terminal-source-build.json'],cwd=ROOT))
 assert baseline==published['manifest'] and sha('build/checkpoints/18b9/TERMINAL.EXE')==baseline['binary_sha256']
 assert memory['near_bytes']-baseline['memory_layout']['near_bytes']==240
 assert memory['resident_code_bytes']-baseline['memory_layout']['resident_code_bytes']==252
 assert memory['configuration_bridge_pairs_verified']==61 and memory['far_code_bridge_pairs_verified']==110
 regression=read('build/terminal/setup-profile-regression.json');commands=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert len(commands)==77 and regression['complete'] and regression['passed'] and regression['binary_sha256']==runtime
 assert commands==[c['command'] for c in regression['commands']] and all(c['exit_code']==0 for c in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json');assert proof['passed'] and proof['output_count']==64
 assert proof['outputs']['terminal/TERMINAL.EXE']['sha256']==runtime and proof['outputs']['xlt-editor/XLTEDIT.EXE']['sha256']==editor
 assert all(o['matches_workspace'] for o in proof['outputs'].values())
 isolated_path=Path('build/application-source-proof/translation-edit-linked-checks.json');isolated=read(isolated_path)
 assert isolated['passed'] and isolated['binary_sha256']==runtime and isolated['inputs']==55;sources(isolated)
 artifacts.extend([isolated_path,*map(Path,['build/terminal/config-far-checks.json','build/terminal/setup-profile-regression.json','build/application-source-proof/snapshot.json','build/application-source-proof/result.json','build/application-source-proof/build.log'])])
 inputs=['standalone/build_terminal.py','standalone/terminal_memory.py','standalone/check_config_far_live.py','standalone/build_xlt_editor.py','nix/flake.nix','nix/flake.lock','standalone/record_translation_edit.py','standalone/check_setup_model.py','standalone/check_directory_live.py','standalone/check_translation_edit_live.py','standalone/test_translation_edit_dos.py','standalone/test_xlt_editor_dos.py','standalone/xlt_editor_paths_host.c','src/config/resource_path.c','src/config/resource_path.h','src/translation/editor_document.c','src/translation/editor_document.h','src/translation/editor_main.c','src/translation/xlt_live.c','src/translation/xlt_live.h','src/terminal/translation_edit.asm','src/terminal/translation_reload.asm','src/terminal/program_actions.asm','src/terminal/transport.asm','src/terminal/config_abi.inc','src/redisplay/command_menu.c']
 result=dict(passed=True,binary_sha256=runtime,editor_sha256=editor,memory_layout=memory,baseline=dict(commit='4a1295aace5b9b7b0933b1d5cebd64755641e004',binary_sha256=baseline['binary_sha256'],memory_layout=baseline['memory_layout']),linked=cpu,actual_DOS=dos,offline_editor=offline,call_frames=frames,
  terminal_regression=regression,exact_PRM_files_verified=8,runtime_sources=manifest['sources'],sources={n:sha(n) for n in inputs},retained_artifacts={str(n):sha(n) for n in artifacts},
  source_rebuild=dict(report='docs/validation/application-components-source-build.json',output_count=64,source_snapshot_sha256=proof['source_snapshot_sha256'],isolated_linked_inputs=55),
  scope='Maintained AltF8/menu direct XLTEDIT child beside the launching executable using a bounded DOS3 PSP trailer. Frozen selected absolute table, quoted argument, same-parent replacement/recovery, drained UART/IRQ owner and separate post-child exact snapshot/Y confirmation.55 linked inputs,8 actual production-child DOS workflows,22 offline DOS cases,276 rejected frames/layouts,77 terminal regression commands and64 byte-identical source outputs. Physical modem, every DOS/video environment, complete settings/emulations/protocols/ASPECT/Host and whole-application gates remain open.')
 (ROOT/'docs/validation/translation-edit.json').write_text(json.dumps(result,indent=2)+'\n')
 # The offline component remains independently scoped; it contains no claim
 # about the terminal's UART, parent program or live memory behavior.
 offline['retained_artifacts']={str(n):sha(n) for n in artifacts if str(n).startswith('build/xlt-editor/')}
 (ROOT/'docs/validation/xlt-editor.json').write_text(json.dumps(offline,indent=2)+'\n')
 print('Recorded direct table editor',runtime,editor)
if __name__=='__main__':main()
