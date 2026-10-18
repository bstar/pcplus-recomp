#!/usr/bin/env python3
"""Record serviced BREAK evidence without treating virtual timing as physical proof."""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 digest=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json')
 assert manifest['binary_sha256']==digest
 for p,want in manifest['sources'].items():assert sha(p)==want,p
 linked=read('build/terminal/break-checks.json')
 regression=read('build/terminal/break-final-regression.json')
 source=read('docs/validation/terminal-source-build.json')
 for r in (linked,regression,source):assert r['passed'] and r['binary_sha256']==digest
 expected=(ROOT/'Makefile').read_text().split('test-terminal: terminal\n',1)[1].split('\n\n',1)[0].splitlines()
 assert [r['command'] for r in regression['commands']]==[c.strip() for c in expected]
 assert all(not r['exit_code'] for r in regression['commands'])
 importer=read('build/modem-import/checks.json');assert importer['passed'] and importer['settings_bytes']==368
 for p,want in importer['sources'].items():assert sha(p)==want,p
 dos={};artifacts={}
 for case in ('break','break-exit'):
  folder=Path('build/terminal-tests')/case;result=read(folder/'result.json')
  assert result['passed'] and result['binary_sha256']==digest
  sample=struct.unpack('<6H',(ROOT/folder/'WATCH.BIN').read_bytes())
  assert sample[0]==0x4c42 and sample[2]>0
  assert result['checks']['independent_DOS_timer_observed_LCR_BREAK']
  if case=='break':assert sample[5].bit_count()>=2 and result['checks']['video_digit_changes_while_BREAK_asserted']
  assert (ROOT/folder/'BEFORE.BIN').read_bytes()==(ROOT/folder/'AFTER.BIN').read_bytes()
  dos[case]=dict(result=result,timer_sample=dict(magic=sample[0],ticks=sample[1],BREAK_ticks=sample[2],post_BREAK_ticks=sample[3],last_sampled_LCR=sample[4],video_digit_mask=sample[5]))
  for file in sorted((ROOT/folder).iterdir()):
   if file.is_file():artifacts[str(file.relative_to(ROOT))]=sha(file.relative_to(ROOT))
 scripts=['standalone/record_break.py','standalone/check_terminal_break_live.py','standalone/test_terminal.py','standalone/break_watch.asm','standalone/check_modem_import.py','standalone/check_startup_import.py','standalone/check_directory_live.py','standalone/modem_fixtures.py','src/config/prm.py','src/config/test_modem.py','docs/BREAK_NATIVE.md']
 for p in ['build/terminal/break-checks.json','build/terminal/break-final-regression.json','build/terminal/break-final-regression.log','build/modem-import/checks.json']:artifacts[p]=sha(p)
 result=dict(passed=True,binary_sha256=digest,memory_layout=manifest['memory_layout'],linked_checks=linked,DOS_cases=dos,modem_import=importer,terminal_regression=regression,source_rebuild=dict(report='docs/validation/terminal-source-build.json',binary_sha256=source['binary_sha256'],source_snapshot_sha256=source['source_snapshot_sha256']),source_sha256={p:sha(p) for p in scripts},retained_artifacts=artifacts,scope='Source-built serviced UART BREAK with native calibration evidence and deliberately conservative BIOS-tick policy. Actual linked code/IRQ/key/flow/ownership tests plus independent DOS INT1C sampling of LCR and changing RX video during assertion; early AltX restores sampled UART/PIC/IRQ. No fake THR byte, original-binary build input, physical electrical timing, modem acknowledgement or complete PCPlus claim.')
 (ROOT/'docs/validation/terminal-break.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded serviced BREAK',digest,len(regression['commands']),'terminal commands',linked['inputs'],'linked inputs')
if __name__=='__main__':main()
