#!/usr/bin/env python3
"""Check the canonical unsaved editor input independently of recorded runs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
 path=ROOT/'lab/bbs/editor-recipes.json';raw=path.read_bytes();recipe=json.loads(raw)
 assert recipe['schema']==1
 keys=recipe['enigma_unsaved']['keyboard_input'];tokens=keys.split()
 body=tokens[tokens.index('A'):]
 # Exact terminal/editor boundary and no Enter/menu submission after typing.
 assert 'A B C D E p400 home' in keys
 assert keys.startswith('p12000 enter') and keys.endswith('U N S A V E D p3000 a-x')
 assert body.count('enter')==0 and tokens.count('a-x')==1
 assert all(k in body for k in ('home','end','ins','del','pgup','pgdown','tab','c-y'))
 assert not {'insert','delete','pageup','pagedown','pgdn','backspace'}&set(tokens)
 command='ADDKEY p1000 '+keys+' p2000 a-x';assert len(command)<500
 # A previous generated run grows if reused as input. The checked-in fixture
 # is independent of that report and stays within the complete DOS bound.
 generated=keys
 for _ in range(20):generated='p1000 '+generated+' p2000 a-x'
 assert len('ADDKEY '+generated)>=500
 result=dict(passed=True,canonical_input_characters=len(keys),complete_ADDKEY_characters=len(command),no_enter_after_body=True,source_sha256=hashlib.sha256(raw).hexdigest(),scope='Canonical local unsaved ENiGMA keyboard recipe, independent of mutable run reports. All exercised key aliases and complete DOS command length checked; generated wrapper accumulation reproduced separately. Actual editor behavior is tested by DOS/server runs.')
 out=ROOT/'build/bbs-lab/editor-recipes';out.mkdir(parents=True,exist_ok=True);(out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
