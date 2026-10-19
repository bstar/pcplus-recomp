#!/usr/bin/env python3
"""Original-free EXECUTE conformance, raw path strings and retained code."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/aspect'))
import compiler

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 path=ROOT/'standalone/fixtures/aspect_chain_compiler_vectors.json';c=json.loads(path.read_text());counts=dict(accepted=0,rejected=0,presentation=0,rejected_variants=0,novel=0)
 def alter(source):
  changed=re.sub(r'"[^"\r\n]*"|[a-zA-Z_$][a-zA-Z_0-9$]*',lambda m:m[0]if m[0].startswith('"')else({'target':'next_script','result':'retained_word','worker':'dispatch_child'}.get(m[0].lower(),m[0])).upper(),source)
  return '\n'.join('\t '+line+'  'for line in changed.splitlines())
 for v in c['vectors']:
  source=v['source'];wire=bytes.fromhex(v['hex']);assert sha(source.encode('cp437'))==v['source_sha256']and sha(wire)==v['asx_sha256'];assert compiler.compile_source(source)==wire,v['label'];counts['accepted']+=1;assert compiler.compile_source(alter(source))==wire,v['label'];counts['presentation']+=1
 for v in c['rejected']:
  assert sha(v['source'].encode('cp437'))==v['source_sha256']
  for key,source in [('rejected',v['source']),('rejected_variants',alter(v['source']))]:
   try:compiler.compile_source(source)
   except compiler.CompileError:counts[key]+=1
   else:raise AssertionError((v['label'],'unexpectedaccept'))
 # Independently authored globalindex layouts, not fixture-name lookups.
 for i in range(5):
  source='string '+','.join('filename_'+str(j)for j in range(i+1))+f'\nproc main\nexecute filename_{i}\nendproc\n';assert compiler.compile_source(source)==bytes([i+1,207,203,140,i,148]);counts['novel']+=1
 assert compiler.compile_source('proc main\nexecute $null\nendproc\n')==bytes.fromhex('00cfcb6e1394');counts['novel']+=1
 source='integer retained\nproc main\ncall worker\n'+'retained=1\n'*10000+'endproc\nproc worker\nexecute $null\nendproc\n';wire=compiler.compile_source(source);assert int.from_bytes(wire[4:8],'little')==70009 and wire[70009:]==bytes.fromhex('cfcb6e1394');counts['novel']+=1
 out=ROOT/'build/aspect-chain-compiler';out.mkdir(parents=True,exist_ok=True);r=dict(passed=True,original_inputs=[],counts=counts,compiler_sha256=sha(Path(compiler.__file__).read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),fixture_sha256=sha(path.read_bytes()),scope='EXECUTEcompileronly, noCHAINalias. Rawpathspelling andpostcommandcodepreserved; loader/restart999 andruntimeexecutionnotestablishedhere.');(out/'checks.json').write_text(json.dumps(r,indent=2)+'\n');print('EXECUTEcompiler',counts,'PASS')
if __name__=='__main__':main()
