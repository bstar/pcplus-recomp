#!/usr/bin/env python3
"""Owned stock Synchronet DOS editor, fixed COM2/19200 and clean draft line."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True)
 parser.add_argument('--flow',choices=['HARD','SOFT','NONE'],default='HARD');args=parser.parse_args()
 assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
 recipe_path=ROOT/'lab/bbs/synchronet-editor-recipe.json';recipe=json.loads(recipe_path.read_text())['keyboard_input']
 assert 'c-y p400 A B C D E' in recipe and 'enter' not in recipe[recipe.index('A B C D E'):].split()
 binary=ROOT/'build/terminal/TERMINAL.EXE';digest=sha(binary);recipe_hash=sha(recipe_path)
 out=ROOT/'build/bbs-lab/results/synchronet'/args.label;assert not out.exists();out.mkdir(parents=True)
 sources=['lab/bbs/synchronet_editor_dos_probe.py','lab/bbs/synchronet-editor-recipe.json','lab/bbs/editor_dos_probe.py','lab/bbs/test_dos.py','lab/bbs/check_editor_dos.py','lab/bbs/modem.py']
 hashes={s:sha(ROOT/s) for s in sources}
 command=[sys.executable,str(ROOT/'lab/bbs/editor_dos_probe.py'),str(binary),'synchronet','--port','23231','--label',args.label,'--com','2','--baud','19200','--flow',args.flow,'--dial-fixture','--timeout','120','--wait','2','--keys',recipe]
 with (out/'harness.log').open('w') as log:subprocess.run(command,cwd=ROOT,stdout=log,stderr=log,check=True)
 with (out/'audit.log').open('w') as log:code=subprocess.call([sys.executable,str(ROOT/'lab/bbs/check_editor_dos.py'),'synchronet','--label',args.label],cwd=ROOT,stdout=log,stderr=log)
 assert sha(binary)==digest and sha(recipe_path)==recipe_hash and hashes=={s:sha(ROOT/s) for s in sources}
 run=json.loads((out/'result.json').read_text());audit=json.loads((out/'semantic-audit.json').read_text())
 assert run['passed'] and audit['checks']['stock_editor_entered']
 assert run['serial']==audit['serial'] and run['serial']['flow']==args.flow
 result=dict(binary_sha256=digest,recipe_sha256=recipe_hash,source_sha256=hashes,serial=run['serial'],DOS_harness_passed=run['passed'],editor_passed=audit['passed'],audit_exit_code=code,checks=audit['checks'],observed_key_wire=audit['observed_key_wire'],scope='Actual DOS stock local Synchronet FSEditor with explicit synthetic body-line clear, fixed COM2/19200 and selected flow; Ctrl-Q abort is audited. No editor save command is sent. The column oracle requires this prepared one-line draft; this is not physical UART/firmware validation.')
 (out/'experiment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 raise SystemExit(code)
if __name__=='__main__':main()
