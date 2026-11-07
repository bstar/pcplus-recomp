#!/usr/bin/env python3
"""Original-free ALARM grammar/emission checks in host and DOS compilers."""
import argparse,json,os,re,shutil,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha
sys.path.insert(0,str(ROOT/'src/aspect'))
import compiler

FIXTURE='standalone/fixtures/aspect_alarm_compiler_vectors.json'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--compiler-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();build=a.compiler_dir.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 manifest=json.loads((build/'manifest.json').read_text());binary=sha(build/'ASPCOMP.EXE')
 assert binary==manifest['binary_sha256'] and manifest['original_inputs']==[]
 sources=dict(manifest['sources'])
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 fixture=json.loads((ROOT/FIXTURE).read_text());cases=[]
 for accepted,key in ((True,'vectors'),(False,'rejected')):
  for case in fixture[key]:
   assert sha_bytes(case['source'].encode('cp437'))==case['source_sha256']
   if accepted:assert sha_bytes(bytes.fromhex(case['hex']))==case['asx_sha256']
   for variant in ('original','presentation'):
    source=case['source']
    if variant=='presentation':
     source=re.sub(r'"[^"\r\n]*"|[a-zA-Z_$][a-zA-Z_0-9$]*',lambda m:m[0] if m[0].startswith('"') else m[0].upper(),source)
     source='\r\n'.join('\t '+line+'  ' for line in source.splitlines())+'\r\n'
    try:
     answer=compiler.compile_source(source);assert accepted and answer==bytes.fromhex(case['hex']),case['label']
    except compiler.CompileError:assert not accepted,case['label']
    cases.append(dict(label=case['label'],variant=variant,source=source,accepted=accepted,expected=case.get('hex')))
 assert len(cases)==78
 shutil.copyfile(build/'ASPCOMP.EXE',out/'ASPCOMP.EXE');batch=['@echo off'];sentinel=b'PREVIOUS VALID OUTPUT'
 for i,case in enumerate(cases):
  name=f'C{i:03}';(out/(name+'.ASP')).write_bytes(case['source'].encode('cp437'))
  if not case['accepted']:(out/(name+'.ASX')).write_bytes(sentinel)
  batch.extend([f'ASPCOMP {name}.ASP {name}.ASX >{name}.LOG','if errorlevel 2 goto failed',('if errorlevel 1 goto failed' if case['accepted'] else 'if not errorlevel 1 goto failed')])
 batch.extend(['echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done'])
 (out/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode('ascii'))
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\ncall RUN.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=90)
 assert (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists()
 rows=[]
 for i,case in enumerate(cases):
  name=f'C{i:03}';data=(out/(name+'.ASX')).read_bytes()
  assert data==(bytes.fromhex(case['expected']) if case['accepted'] else sentinel),case['label']
  rows.append(dict(label=case['label'],variant=case['variant'],accepted=case['accepted'],source_sha256=sha(out/(name+'.ASP')),output_sha256=sha_bytes(data)))
 assert not list(out.glob('LPC*.TMP')) and not list(out.glob('LPC*.BAK'))
 assert sha(out/'ASPCOMP.EXE')==binary
 for name in (FIXTURE,'src/aspect/compiler.py','standalone/test_aspect_alarm_compiler.py','standalone/build_context_help.py'):sources[name]=sha(ROOT/name)
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 captures={f.name:sha(f) for f in out.iterdir() if f.is_file()}
 result=dict(passed=True,cases=rows,original_cases=39,presentation_cases=39,DOS_children=78,accepted=34,rejected=44,binary_sha256=binary,sources=sources,captures=captures,original_inputs=[],scope=__doc__+' Authored frozen original compiler outcomes:17accept22reject plus presentation variants. Exact ASX bytes; rejected compilations preserve existing output and leave no temporary files. No ALARM opcode execution, VM/parent integration or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS ALARM compiler:39 original +39 presentation cases, host and DOS')
def sha_bytes(data):return __import__('hashlib').sha256(data).hexdigest()
if __name__=='__main__':main()
