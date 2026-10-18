#!/usr/bin/env python3
"""Explicit ENiGMA DOS editor experiment, using the retained unsaved key recipe.

Requires the owned stock loopback server on23233. Leaves immediate-bridge
compatibility evidence untouched. Never sends an editor Save/menu Enter.
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--delay-ms',type=int,choices=range(101),required=True)
 p.add_argument('--label',required=True)
 p.add_argument('--binary',type=Path,default=ROOT/'build/terminal/TERMINAL.EXE')
 a=p.parse_args()
 assert a.label and all(c.isalnum() or c in '-_' for c in a.label),'Simple unique label required'
 out=ROOT/'build/bbs-lab/results/enigma'/a.label
 assert not out.exists(),'Preserve previous attempt folders; select a new label'
 recipe_path=ROOT/'lab/bbs/editor-recipes.json'
 recipe=json.loads(recipe_path.read_text())['enigma_unsaved']['keyboard_input']
 # Stop after typing UNSAVED and disconnect. A changed recipe requires review.
 assert 'U N S A V E D p3000 a-x' in recipe and recipe[recipe.index('A B C D E'):].count('enter')==0
 binary=a.binary.resolve();digest=sha(binary)
 sources=['lab/bbs/modem.py','lab/bbs/test_dos.py','lab/bbs/check_editor_dos.py','lab/bbs/editor_dos_probe.py','lab/bbs/packetization_editor_probe.py','lab/bbs/editor-recipes.json']
 hashes={s:sha(ROOT/s) for s in sources}
 command=[sys.executable,str(ROOT/'lab/bbs/editor_dos_probe.py'),str(binary),'enigma','--port','23233','--label',a.label,'--com','2','--baud','19200','--flow','HARD','--dial-fixture','--packet-delay-ms',str(a.delay_ms),'--timeout','160','--wait','2','--keys',recipe]
 out.mkdir(parents=True,exist_ok=False)
 with (out/'harness.log').open('w') as log:code=subprocess.call(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 assert code==0 and (out/'result.json').is_file(),'DOS harness failed; see retained harness.log. No editor comparison recorded.'
 with (out/'audit.log').open('w') as log:audit_code=subprocess.call([sys.executable,str(ROOT/'lab/bbs/check_editor_dos.py'),'enigma','--label',a.label,'--disconnect-unsaved'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 assert sha(binary)==digest and hashes=={s:sha(ROOT/s) for s in sources},'Inputs changed during experiment'
 run=json.loads((out/'result.json').read_text());audit=json.loads((out/'semantic-audit.json').read_text())
 assert code==0 and run['passed'],'DOS harness failed; retained evidence is not an editor result'
 assert audit['checks']['no_post_saved'],'Unexpected saved local message'
 result={'binary_sha256':digest,'source_sha256':hashes,'packet_delay_ms':a.delay_ms,'DOS_harness_passed':run['passed'],'editor_passed':audit['passed'],'audit_exit_code':audit_code,'checks':audit['checks'],'observed_key_wire':audit['observed_key_wire'],'scope':'Stock local ENiGMA, same retained key recipe and actual DOS executable. Explicit byte-transparent modem buffering experiment; no physical firmware or guaranteed TCP boundaries. Immediate baseline reports remain unchanged.'}
 (out/'experiment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
