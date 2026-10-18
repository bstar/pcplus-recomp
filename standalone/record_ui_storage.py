#!/usr/bin/env python3
"""Bind far UI ownership, DOS behavior and source-only build evidence."""
import hashlib,json
from pathlib import Path
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 runtime=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json')
 assert manifest['binary_sha256']==runtime
 for p,want in manifest['sources'].items():assert sha(p)==want,p
 layout=inspect_terminal_memory(ROOT/'build/terminal/TERMINAL.EXE',ROOT/'build/terminal/terminal.map')
 assert layout==manifest['memory_layout'] and layout['far_ui_storage_bytes']==12000
 linked=read('build/terminal/ui-screen-far-checks.json')
 for p,want in linked['source_sha256'].items():assert sha(p)==want,p
 child=read('build/far-storage-dos/checks.json');regression=read('build/terminal/far-code-final-regression.json');source=read('docs/validation/terminal-source-build.json')
 for result in (linked,child,regression,source):assert result['passed'] and result['binary_sha256']==runtime
 assert child['checks']['all_three_far_UI_screen_buffers_survive_child_allocation_fill']
 commands=(ROOT/'Makefile').read_text().split('test-terminal: terminal\n',1)[1].split('\n\n',1)[0].splitlines()
 assert [r['command'] for r in regression['commands']]==[c.strip() for c in commands]
 assert all(not r['exit_code'] for r in regression['commands'])
 components={}
 for name,binary in [('directory-editor','EDITOR.EXE'),('directory-browser','BROWSER.EXE')]:
  folder='build/'+name+'/'
  component=read(folder+'manifest.json');cpu=read(folder+'checks.json');dos=read(folder+'dos-results.json');digest=sha(folder+binary)
  assert cpu['passed'] and dos['passed'] and component['binary_sha256']==cpu['binary_sha256']==dos['binary_sha256']==digest
  for p,want in component['sources'].items():assert sha(p)==want,p
  components[name]=dict(binary_sha256=digest,CPU_checks=cpu,DOS_checks=dos,manifest=component)
 scripts=['standalone/record_ui_storage.py','standalone/check_ui_screen_far.py','standalone/terminal_memory.py','standalone/test_far_storage_dos.py','standalone/far_storage_child.asm','standalone/check_directory_browser.py','standalone/check_directory_editor.py','standalone/test_directory_browser_dos.py','standalone/test_directory_editor_dos.py']
 paths=['build/terminal/ui-screen-far-checks.json','build/far-storage-dos/checks.json','build/connection-dos/far-storage/FARTEST.BIN','build/terminal/far-code-final-regression.json','build/terminal/far-code-final-regression.log']
 result=dict(passed=True,binary_sha256=runtime,memory_layout=layout,baseline=dict(commit='57ebcd3',binary_sha256='bdeb347c99168c8f745c312abfd40468250959ffdfd82af562476a6d29bea2c8',near_bytes=64368,loaded_module_bytes=104874,image_bytes=105050),near_bytes_freed=64368-layout['near_bytes'],loaded_module_bytes_saved=104874-layout['loaded_module_bytes'],image_bytes=(ROOT/'build/terminal/TERMINAL.EXE').stat().st_size,image_bytes_saved=105050-(ROOT/'build/terminal/TERMINAL.EXE').stat().st_size,linked_checks=linked,DOS_child=child,components=components,terminal_regression=regression,source_rebuild=dict(report='docs/validation/terminal-source-build.json',binary_sha256=source['binary_sha256'],source_snapshot_sha256=source['source_snapshot_sha256']),source_sha256={p:sha(p) for p in scripts},retained_artifacts={p:sha(p) for p in paths},scope='Three distinct4000-byte far screen owners, packed browser/editor formats and raw PROGRAM frame. Actual linked helper ABI, bounds, CGA port models and layout-rejection tests; standalone actual DOS browser/editor keyboard/video plus parent/child allocation/fill. Full terminal regressions include nested browser/edit/save and PROGRAM handoff. Source rebuild is separate; no physical CGA/386/modem, full original UI or whole-application completion claim.')
 (ROOT/'docs/validation/terminal-ui-storage.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded far UI storage',runtime,'near bytes freed',result['near_bytes_freed'])
if __name__=='__main__':main()
