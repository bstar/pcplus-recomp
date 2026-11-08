#!/usr/bin/env python3
"""Match frozen GET compiler observations in opt-in host and DOS frontends."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/aspect'));import compiler
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
FIXTURE='standalone/fixtures/aspect_get_compiler.json'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('compiler-dir','default-compiler-dir','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 sources={};builds=[]
 for folder,enabled,leaf in [(a.compiler_dir,True,'ASPCOMP.EXE'),(a.default_compiler_dir,False,'DEFAULT.EXE')]:
  m=json.loads((folder/'manifest.json').read_text());assert m.get('experimental_get_compiler',False)==enabled and m['original_inputs']==[]
  assert sha(folder/'ASPCOMP.EXE')==m['binary_sha256']
  for n,h in m['sources'].items():assert sha(ROOT/n)==h;sources[n]=h
  builds.append((folder,leaf,m))
 rows=[]
 for v in json.loads((ROOT/FIXTURE).read_text())['vectors']:
  for presentation in (False,True):
   source=v['source']
   if presentation:
    source=re.sub(r'"[^"\r\n]*"|[A-Za-z_$][A-Za-z_0-9$]*',lambda m:m[0] if m[0].startswith('"') else m[0].upper(),source)
    source='\r\n'.join('\t '+line+'  ' for line in source.splitlines())+'\r\n'
   try:
    wire=compiler.compile_source(source,enable_get=True);assert v['accepted'] and wire==bytes.fromhex(v['hex']),v['label']
   except compiler.CompileError:assert not v['accepted'],v['label']
   try:compiler.compile_source(source);raise AssertionError('default host compiler admitted GET')
   except compiler.CompileError:pass
   rows.append(dict(label=v['label'],presentation=presentation,source=source,accepted=v['accepted'],hex=v.get('hex')))
 assert len(rows)==162 and sum(r['accepted'] for r in rows)==56
 out.mkdir()
 for folder,leaf,m in builds:shutil.copyfile(folder/'ASPCOMP.EXE',out/leaf)
 batch=['@echo off'];sentinel=b'UNCHANGED OUTPUT'
 for i,row in enumerate(rows):
  name='C'+str(i).zfill(3);(out/(name+'.ASP')).write_bytes(row['source'].encode('cp437'))
  (out/(name+'.ASX')).write_bytes(sentinel);(out/(name+'.DEF')).write_bytes(sentinel)
  batch+=['ASPCOMP '+name+'.ASP '+name+'.ASX >'+name+'.LOG','if errorlevel 2 goto failed',
   'if errorlevel 1 goto failed' if row['accepted'] else 'if not errorlevel 1 goto failed']
  # The default compiler refuses before publishing even for originally valid GET.
  batch+=['DEFAULT '+name+'.ASP '+name+'.ASX >'+name+'.DLOG','if errorlevel 2 goto failed','if not errorlevel 1 goto failed']
 batch+=['echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done','exit']
 (out/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode())
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nRUN\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=90)
 assert (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists()
 for i,row in enumerate(rows):
  name='C'+str(i).zfill(3);wire=(out/(name+'.ASX')).read_bytes();assert wire==(bytes.fromhex(row['hex']) if row['accepted'] else sentinel),row['label']
  row.pop('source');row['source_sha256']=sha(out/(name+'.ASP'));row['output_sha256']=sha(out/(name+'.ASX'))
 assert not list(out.glob('LPC*.TMP')) and not list(out.glob('LPC*.BAK'))
 for n in (FIXTURE,'src/aspect/compiler.py','standalone/test_aspect_get_compiler.py'):sources[n]=sha(ROOT/n)
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 r=dict(passed=True,cases=rows,DOS_compilations=324,accepted=56,rejected=106,default_refusals=162,
  binary_sha256=builds[0][2]['binary_sha256'],default_binary_sha256=builds[1][2]['binary_sha256'],sources=sources,original_inputs=[],
  scope=__doc__+'81 original observations plus presentation variants; exact complete ASX for28accepted originals and atomic refusal for53rejections. Default host/DOS refuse allGET. Float syntax accepted; runtime float remains unsupported. Not VM/parent/physical or full language acceptance.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS GET compilers:162 oracle/presentation cases;324 DOS compilations; defaults refuse GET')
if __name__=='__main__':main()
