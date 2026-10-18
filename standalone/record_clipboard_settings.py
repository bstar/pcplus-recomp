#!/usr/bin/env python3
"""Bind saved separator adoption/persistence to current runtime and source proof."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def sources(report):
 for path,digest in report.get('sources',{}).items():assert sha(path)==digest,path

def main():
 runtime=sha('build/terminal/TERMINAL.EXE');editor=sha('build/setup/PRMEDIT.EXE')
 manifest=read('build/terminal/manifest.json');sources(manifest);assert manifest['binary_sha256']==runtime
 linked=read('build/terminal/clipboard-settings-checks.json');dos=read('build/clipboard-settings-dos/checks.json')
 for r in [linked,dos]:assert r['passed'] and r['binary_sha256']==runtime;sources(r)
 assert linked['inputs']==805 and len(linked['groups'])==5
 assert len(dos['cases'])==7 and dos['editor_sha256']==editor
 assert all(c['passed'] and all(c['checks'].values()) for c in dos['cases'])
 model=read('build/setup-model/checks.json');assert model['passed'] and model['binary_sha256']==sha('build/setup-model/MODEL.EXE');sources(model)
 log=(ROOT/'build/clipboard-settings-codec.log').read_text();assert 'Ran 14 tests' in log and '\nOK\n' in log
 frames=read('build/terminal/config-far-checks.json');assert frames['passed'] and frames['binary_sha256']==runtime and len(frames['rejected_mutations'])==173
 regression=read('build/terminal/setup-profile-regression.json')
 expected=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert len(expected)==77 and regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 assert [c['command'] for c in regression['commands']]==expected and all(c['exit_code']==0 for c in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json');assert proof['passed'] and proof['output_count']==64
 for name,digest in [('terminal/TERMINAL.EXE',runtime),('setup/PRMEDIT.EXE',editor)]:assert proof['outputs'][name]['sha256']==digest and proof['outputs'][name]['matches_workspace']
 inputs=['standalone/record_clipboard_settings.py','standalone/check_clipboard_settings.py','standalone/test_clipboard_settings_dos.py','standalone/check_setup_model.py','src/config/prm.py','src/config/test_prm.py']
 artifacts=['build/terminal/clipboard-settings-checks.json','build/clipboard-settings-dos/checks.json','build/setup-model/checks.json','build/clipboard-settings-codec.log','build/terminal/config-far-checks.json','build/terminal/setup-profile-regression.json']
 for c in dos['cases']:
  folder=ROOT/'build/connection-dos'/c['case'];assert folder.name==c['case']
  artifacts.extend(str(p.relative_to(ROOT)) for p in sorted(folder.iterdir()) if p.is_file())
 result=dict(passed=True,binary_sha256=runtime,editor_sha256=editor,memory_layout=manifest['memory_layout'],linked=linked,actual_DOS=dos,field_model=model,codec_units=dict(passed=True,count=14,command="python3 -m unittest discover -s src/config -p 'test_*.py' -v"),ABI=dict(serial_bytes=44,candidate_bytes=628,clipboard_serial_offset=42,modem_candidate_offset=44,directory_candidate_offset=412,change_mask_offset=626,change_bit=4096,editor_fields=46,editor_separator_index=45,raw_PRM_offset=1258),call_frames=frames,terminal_regression=regression,runtime_sources=manifest['sources'],sources={p:sha(p) for p in inputs},retained_artifacts={p:sha(p) for p in artifacts},source_rebuild=dict(report='docs/validation/application-components-source-build.json',source_snapshot_sha256=proof['source_snapshot_sha256'],output_count=64),scope='Maintained saved PRM04EA clipboard separator word, strict0..255 validation,44-byte serial/628-byte candidate ABI,46th source-owned PRMEDIT field and live independent application. Session R survives unchanged/unsaved/unrelated editor returns; successful foreground acknowledgement advances saved baseline so explicit revert is recognized.805 linked inputs,7 actual DOS UI/file/UART/observer workflows,14 codec unit tests,173 rejected bridge mutations,77-command regression and64 reproducible outputs. Original PCSETUP menu binding, clipboard transfer-prompt workflows, other geometries, physical UART/modem and whole-application reconstruction remain open.')
 (ROOT/'docs/validation/clipboard-settings.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded saved clipboard settings',runtime)
if __name__=='__main__':main()
