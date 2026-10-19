#!/usr/bin/env python3
"""Bind bounded line metadata to linked, real DOS, BBS and rebuild evidence."""
import hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def main():
 binary=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json')
 assert manifest['binary_sha256']==binary
 for p,h in manifest['sources'].items():assert sha(p)==h,p
 paths=dict(linked='build/terminal/line-attributes-live-checks.json',policy='build/terminal/line-edit-live-checks.json',DOS='build/line-attributes-dos/bounded-lines-03/checks.json',
  ASPECT='build/aspect-renderer-dos/bounded-lines-01/checks.json',ENiGMA='build/bbs-lab/results/enigma/bounded-lines-search-01/search-checks.json',ABI='build/terminal/config-far-checks.json')
 data={k:read(p) for k,p in paths.items()};reports={}
 for k,d in data.items():
  assert d['passed'],k
  assert d.get('binary_sha256',d.get('terminal_sha256'))==binary,k
  reports[k]=dict(path=paths[k],sha256=sha(paths[k]))
 linked=data['linked'];assert (linked['cases'],linked['repair_operations'],linked['pre_mutation_rejections'])==(512,192,45)
 assert linked['checker_sha256']==sha('standalone/check_line_attributes_live.py')
 assert linked['repair_reference_sha256']==sha('standalone/check_attribute_repair.py')
 assert len(data['policy']['cases'])==8 and all(c['passed'] for c in data['policy']['cases'])
 dos=data['DOS'];assert all(dos['checks'].values())
 for p,h in dos['inputs'].items():assert sha(p)==h,p
 base='build/line-attributes-dos/bounded-lines-03';raw=(ROOT/base/'product/LINEATTR.BIN').read_bytes();assert len(raw)==12216
 assert sha(base+'/product/LINEATTR.BIN')==dos['capture_sha256'] and sha(base+'/LATTR.COM')==dos['observer_program_sha256']
 state=struct.unpack_from('<12H',raw);assert tuple(dos['state'])==state
 assert state[:4]==(0x4c41,1,1,0) and state[4]==state[5] and state[6:11]==(1,7,2000,24,79) and state[11]>=3
 flags=bytearray(2000);flags[800]=0x81
 assert raw[24:4120]==bytes(flags)+b'\x55'*2096 and raw[4120:8216]==b'\x07'*2000+b'\x66'*2096
 cells=[0x0720]*2000
 for row,text in [(0,b'FIRST BYTE SAFE'),(1,b'TOP'),(2,b'R2'),(3,b'R4'),(6,b'BOTTOM')]:
  for i,c in enumerate(text):cells[row*80+i]=0x700|c
 assert raw[8216:]==struct.pack('<2000H',*cells)
 aspect=data['ASPECT'];assert {c['case'] for c in aspect['cases']}=={'queries-before-login','native-edits-origin-scroll'}
 assert all(c['passed'] and all(c['checks'].values()) for c in aspect['cases'])
 assert aspect['checker_sha256']==sha('standalone/test_aspect_renderer_dos.py')
 enigma=data['ENiGMA'];assert all(enigma['checks'].values())
 assert enigma['runner_sha256']==sha('lab/bbs/enigma_search_dos.py') and enigma['fixture_sha256']==sha('lab/bbs/enigma_search_fixture.py')
 live=ROOT.parent/'black-flag-bbs'
 for p,h in enigma['source_modules'].items():assert hashlib.sha256((live/p).read_bytes()).hexdigest()==h,p
 live_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=live,text=True).strip()
 live_client=hashlib.sha256((live/'core/client.js').read_bytes()).hexdigest();assert live_client=='d66207f46af13ae4acb0ac430b1d0f2572a03722c79f4bcb7125dcd01e98e788'
 proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
 assert proof['passed'] and proof['outputs']['terminal/TERMINAL.EXE']['sha256']==binary
 assert 'standalone/check_line_attributes_live.py' in proof['build_scripts']
 assert read('build/dos-package/manifest.json')['files']['TERMINAL.EXE']==binary
 memory=manifest['memory_layout'];assert memory['line_attribute_far_entries_verified']==2 and memory['line_attribute_resident_references_verified']==3 and memory['line_attribute_video_callbacks_verified']==2
 history=[]
 for label,failed in [('bounded-lines-01','video_byte_exact'),('bounded-lines-02','three_cursor_snapshots')]:
  p='build/line-attributes-dos/'+label+'/checks.json';d=read(p)
  assert not d['passed'] and not d['checks'][failed] and d['checks']['canonical_DOS_harness']
  history.append(dict(path=p,sha256=sha(p),failed_observation=failed,product_exit_passed=True))
 result=dict(passed=True,terminal_sha256=binary,reports=reports,linked=dict(cases=512,repair_operations=192,pre_mutation_rejections=45),
  actual_DOS=dict(checks=dos['checks'],state=dict(wrap=state[6],normal_fill_word=state[7],logical_cells=state[8],cursor=list(state[9:11]),cursor_snapshots=state[11]),capture_sha256=dos['capture_sha256'],fixture='Explicit test-only BIOS-boundary plane seeding; application executable and subsequent instructions unmodified.'),
  ASPECT=dict(cases=[c['case'] for c in aspect['cases']],runner_sha256=aspect['runner_sha256']),
  ENiGMA=dict(checks=enigma['checks'],source_modules=enigma['source_modules'],live_revision=live_revision,live_client_sha256=live_client,live_server_modified=False),
  source_build=dict(path=proof_path,sha256=sha(proof_path),outputs=proof['output_count']),memory_layout=memory,
  sources={p:sha(p) for p in ('src/terminal/line_edit.asm','src/terminal/line_attributes.asm','src/terminal/attribute_repair.asm','standalone/check_line_edit_live.py','standalone/check_line_attributes_live.py','standalone/test_line_attributes_dos.py','standalone/line_attributes_watch.asm','standalone/terminal_memory.py')},
  exact_native_sources={p:sha(p) for p in ('reconstruction/line_edit/insert_line.asm','reconstruction/line_edit/delete_line.asm','reconstruction/line_edit/provenance.json')},
  retained_observation_failures=history,recorder_sha256=sha(Path(__file__).relative_to(ROOT)),whole_application_gates_closed=[],
  scope='Maintained NETWORK line-plane shifts/region-limited real native repair with real native video callbacks, distinct from unchanged exact recovery/ORIGINAL policy. Actual-linked state/video oracles, explicit-fixture unmodified DOS executable, ordinary DOS ASPECT and owned-source ENiGMA search/NFO regression plus current source rebuild.',
  limitations=['Admitted fixed80-column B800 mode with no viewport; complete video/emulation and settings exposure remain open.',
   'The real DOS plane-mode test uses declared test-only state seeding; the ordinary ENiGMA/ASPECT runs validate current supported defaults.',
   'Exact ORIGINAL helpers retain their legacy23-row metadata copies; this intentional application policy does not rewrite that evidence.',
   'Live ENiGMA decoder installation, physical RS-232/Wi-Fi modem validation and complete application gates remain open.'])
 (ROOT/'docs/validation/line-attributes.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded bounded line metadata, native repair, DOS guards/video, ASPECT and owned ENiGMA source-only checkpoint')
if __name__=='__main__':main()
