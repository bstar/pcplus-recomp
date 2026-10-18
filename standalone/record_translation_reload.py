#!/usr/bin/env python3
"""Authenticate explicit live table reload against linked, DOS and clean-build evidence."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from check_setup_model import image
from check_directory_live import word
from test_translation_reload_dos import actions
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def sources(d):
 for p,h in d.get('sources',{}).items():assert sha(p)==h,p

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);a=p.parse_args()
 assert a.label and all(c.isalnum() or c in '-_' for c in a.label)
 runtime=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json');assert manifest['binary_sha256']==runtime;sources(manifest)
 linked=read('build/terminal/translation-reload-checks.json');assert linked['passed'] and linked['binary_sha256']==runtime and linked['inputs']==66;sources(linked)
 path=Path('build/translation-reload-dos')/a.label/'checks.json';dos=read(path)
 assert dos['passed'] and dos['binary_sha256']==runtime and len(dos['cases'])==11;sources(dos)
 kinds=['accept','decline','short','missing','explicit','fallback','cwd','early-answer','menu','identity','sevenbit']
 mapping=bytearray(range(256));mapping[ord('L')]=ord('X');mapping=bytes(mapping)
 artifacts=[path,Path('build/terminal/translation-reload-checks.json'),Path('build/terminal/manifest.json')]
 for kind,case in zip(kinds,dos['cases']):
  assert case['case']=='xlt-reload-'+a.label+'-'+kind and case['passed'] and all(case['checks'].values())
  folder=Path('build/setup-startup')/case['case'];assert sha(folder/'TERMINAL.EXE')==runtime
  assert read(folder/'result.json')==case
  before=(ROOT/folder/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(ROOT/folder/'AFTER.BIN').read_bytes()
  watch=struct.unpack('<6H',(ROOT/folder/'WATCH.BIN').read_bytes());assert watch[0]==0x5355 and watch[1]>0 and watch[2]==watch[5]==1 and watch[4]>0
  screen=(ROOT/folder/'SCREEN.BIN').read_bytes();wire=(ROOT/folder/'serial.bin').read_bytes()
  expected=b' XIVE' if kind in ('accept','explicit','fallback','cwd','early-answer','menu') else b' LIVE'
  assert len(screen)==4000 and screen[:22:2]==b'SETUP READY' and screen[22:32:2]==expected
  assert case['expected_post_receive']==expected.decode('ascii')
  for reply in (b'\x1b[0n',b'\x1b[1;12R',b'\x1b[1;17R',b'ready'):assert reply in wire,(kind,reply)
  for local in (b'COPY',b'PCPLUS.XLT',b'CUSTOM.XLT',b'\x1b[C'):assert local not in wire,(kind,local)
  if kind=='early-answer':
   assert case['checks']['controlled_pause_resumed'] and wire.count(b'\x1b[0n')>=2
   assert b'y' not in wire[:wire.index(b'ready')]
  mode=0 if kind=='identity' else 2 if kind=='sevenbit' else 1
  assert (ROOT/folder/'TEST.PRM').read_bytes()==word(image(),0x1e0,mode)
  target='CUSTOM.XLT' if kind=='explicit' else 'CFG/PCPLUS.XLT' if kind=='fallback' else 'PCPLUS.XLT'
  assert case['table_source']==target
  data=bytes(255) if kind=='short' else mapping;assert (ROOT/folder/'NEW.XLT').read_bytes()==data
  actual=ROOT/folder/target
  if kind=='missing':assert not actual.exists()
  else:assert actual.read_bytes()==(bytes(range(256)) if mode!=1 else data)
  if mode==1:
   dos_target=('D:\\'+target.replace('/','\\')).encode()
   command=b'DEL '+dos_target if kind=='missing' else b'COPY /B /Y D:\\NEW.XLT '+dos_target
   extra=(b'CD D:\\OTHER',b'CD >D:\\CWD.TXT') if kind=='cwd' else ()
   assert (ROOT/folder/'TEST.KEY').read_bytes()==actions(command,extra)
   mutations={target:None if kind=='missing' else hashlib.sha256(data).hexdigest()}
   if kind=='cwd':
    assert (ROOT/folder/'CWD.TXT').read_bytes()==b'D:\\OTHER\r\n'
    other=bytearray(range(256));other[ord('L')]=ord('Z')
    assert (ROOT/folder/'OTHER/PCPLUS.XLT').read_bytes()==bytes(other)
    mutations['CWD.TXT']=hashlib.sha256(b'D:\\OTHER\r\n').hexdigest()
   assert case['expected_file_mutations']==mutations
  else:assert not case['expected_file_mutations']
  artifacts.extend(p.relative_to(ROOT) for p in sorted((ROOT/folder).rglob('*')) if p.is_file())
 # Preserve the development failure as a failure, with its own frozen source
 # identities. The current assertion uses the same controlled DOS pause recipe.
 oldbase=Path('build/checkpoints/ad5d');old=read(oldbase/'manifest.json')
 assert sha(oldbase/'TERMINAL.EXE')==old['binary_sha256']
 oldproof=read(oldbase/'source-proof-result.json')['terminal']
 assert oldproof['passed'] and oldproof['binary_sha256']==old['binary_sha256']
 assert oldproof['manifest']==old
 for name,digest in old['sources'].items():assert sha(oldbase/'source-inputs'/name)==digest,name
 model=read(oldbase/'typeahead-reproduction.json')
 assert model['binary_sha256']==old['binary_sha256'] and model['deferred_keys']==model['program_active']==1 and model['old_table']
 assert 'unsatisfied blocking keyboard read' in model['read_error']
 failed=Path('build/setup-startup/xlt-reload-typeahead-ad5d-before-early-answer');failure=read(failed/'result.json')
 assert not failure['passed'] and failure['checks']['controlled_pause_resumed'] and failure['checks']['hardware_restored']
 assert sha(failed/'TERMINAL.EXE')==old['binary_sha256']
 oldwire=(ROOT/failed/'serial.bin').read_bytes();assert oldwire.endswith(b'yeady') and b'ready' not in oldwire
 assert (ROOT/failed/'PCPLUS.XLT').read_bytes()==mapping
 after_case='xlt-reload-'+a.label+'-early-answer';after_folder=Path('build/setup-startup')/after_case
 assert failure['arguments']==read(after_folder/'result.json')['arguments']
 assert (ROOT/failed/'TEST.KEY').read_bytes()==(ROOT/after_folder/'TEST.KEY').read_bytes()
 recipes=[]
 for folder in (failed,after_folder):
  recipes.append([line for line in (ROOT/folder/'dosbox.conf').read_text().splitlines() if line.startswith('ADDKEY ')])
 assert len(recipes[0])==1 and recipes[0]==recipes[1]
 correction=dict(before_binary_sha256=old['binary_sha256'],source_snapshot_sha256=oldproof['source_snapshot_sha256'],
  compiled_inputs_verified=len(old['sources']),model_reproduction=model,actual_DOS_failed_run=failure,
  observed_before_wire_hex=oldwire.hex(),after_case=after_case,identical_DOS_key_recipe=True,
  scope='Early Y was retained during TX drain, then a BIOS-only prompt consumed r and leaked y before eady. Controlled actual DOS SOFT pause reproduces failed post-input service; the same recipe passes with FIFO-first local prompt reads. Before source identities are retained from a prior isolated build snapshot, not a published source commit.')
 artifacts.extend(p.relative_to(ROOT) for directory in (ROOT/oldbase,ROOT/failed) for p in sorted(directory.rglob('*')) if p.is_file())
 memory=manifest['memory_layout'];assert memory['near_bytes']==64480 and memory['resident_code_bytes']==65298
 assert memory['configuration_bridge_pairs_verified']==38 and memory['far_code_bridge_pairs_verified']==87
 frames=read('build/terminal/config-far-checks.json');assert frames['passed'] and frames['binary_sha256']==runtime and len(frames['rejected_mutations'])==187
 regression=read('build/terminal/setup-profile-regression.json');commands=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert len(commands)==77 and regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 assert commands==[c['command'] for c in regression['commands']] and all(c['exit_code']==0 for c in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json');assert proof['passed'] and proof['output_count']==64
 assert proof['outputs']['terminal/TERMINAL.EXE']['sha256']==runtime and proof['outputs']['terminal/TERMINAL.EXE']['matches_workspace']
 clean_path=Path('build/application-source-proof/translation-reload-linked-checks.json');clean=read(clean_path)
 assert clean['passed'] and clean['binary_sha256']==runtime and clean['inputs']==66;sources(clean)
 artifacts.extend([clean_path,*map(Path,['build/terminal/config-far-checks.json','build/terminal/setup-profile-regression.json'])])
 report=dict(passed=True,binary_sha256=runtime,memory_layout=memory,linked=linked,actual_DOS=dos,typeahead_correction=correction,call_frames=frames,
  terminal_regression=regression,runtime_sources=manifest['sources'],
  sources={n:sha(n) for n in ['standalone/record_translation_reload.py','standalone/test_translation_reload_dos.py','standalone/check_setup_model.py','standalone/check_directory_live.py']},
  retained_artifacts={str(p):sha(p) for p in artifacts},
  source_rebuild=dict(report='docs/validation/application-components-source-build.json',output_count=64,source_snapshot_sha256=proof['source_snapshot_sha256'],linked_inputs_without_originals=66,linked_report=str(clean_path)),
  scope='Maintained AltF9/menu same-table reload from the frozen actual canonical source. Exact checked snapshot, Y/decline/failure retention, PROGRAM drain/IRQ/video owner without EXEC, queued input and unchanged mode/mask.66 linked inputs,eleven actual DOS COPY/DEL and table reload workflows,187 rejected frames/layouts,77 terminal regression commands and64 byte-identical source outputs. Dedicated live XLTEDIT, complete UI/application and physical UART/modem remain open; no whole-application gate is closed.')
 (ROOT/'docs/validation/translation-reload.json').write_text(json.dumps(report,indent=2)+'\n');print('Recorded live table reload',runtime)
if __name__=='__main__':main()
