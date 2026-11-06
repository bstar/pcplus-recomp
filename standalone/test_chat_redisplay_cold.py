#!/usr/bin/env python3
"""Rebuild and exercise Chat/Redisplay from a fresh public source export."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();binary,out=a.terminal.resolve(),a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 assert not any((p/'.git').exists() for p in [out,*out.parents])
 m=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==m['binary_sha256'] and m['experimental_chat_redisplay']
 tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0');tracked=[n for n in tracked if n and not n.startswith(('analysis/','build/','.git/'))]
 extra=['standalone/build_chat_redisplay_profile.py','standalone/chat_redisplay_profile.json','standalone/test_chat_redisplay_cold.py','standalone/test_chat_redisplay_dos.py','standalone/chat_redisplay_host.c','standalone/test_chat_redisplay_main_dos.py','standalone/chat_redisplay_watch.asm','standalone/test_chat_redisplay_geometry_dos.py','standalone/chat_redisplay_geometry_host.c']
 paths=sorted(set(tracked)|set(m['sources'])|set(extra));sources={n:sha(ROOT/n) for n in paths}
 for n,h in m['sources'].items():assert sources[n]==h,n
 export=out/'public-source'
 for n,h in sources.items():
  path=Path(n);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('analysis','build','.git')
  target=export/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
 assert sorted(str(p.relative_to(export)) for p in export.rglob('*') if p.is_file())==paths
 candidate=export/'build/candidate'
 commands=[('build',[str(export/'standalone/build_chat_redisplay_profile.py'),'--output',str(candidate)]),('lease',[str(export/'standalone/test_chat_redisplay_dos.py'),'--terminal',str(candidate/'TERMINAL.EXE'),'--output',str(export/'build/lease')]),('main',[str(export/'standalone/test_chat_redisplay_main_dos.py'),'--terminal',str(candidate/'TERMINAL.EXE'),'--output',str(export/'build/main'),'--rows','50']),('geometry',[str(export/'standalone/test_chat_redisplay_geometry_dos.py'),'--terminal',str(candidate/'TERMINAL.EXE'),'--output',str(export/'build/geometry'),'--rows','50','--fault','2'])]
 for name,command in commands:
  with (out/(name+'.log')).open('w') as log:subprocess.run([sys.executable,*command],cwd=export,stdout=log,stderr=log,check=True,timeout=180)
  if name=='build':
   assert sha(candidate/'TERMINAL.EXE')==sha(binary)
   assert sha(candidate/'PCCHAT.OVL')==m['chat_loader']['module']['binary_sha256']
 checks={name:json.loads((export/'build'/name/'result.json').read_text()) for name in ('lease','main','geometry')}
 assert all(r['passed'] for r in checks.values())
 for n,h in sources.items():assert sha(ROOT/n)==sha(export/n)==h,n
 result=dict(passed=True,original_inputs=[],source_files=len(sources),sources=sources,binary_sha256=sha(candidate/'TERMINAL.EXE'),module_sha256=sha(candidate/'PCCHAT.OVL'),application_manifest_sha256=sha(candidate/'manifest.json'),lease_checks=checks['lease']['checks'],main_checks=checks['main']['checks'],main_rows=checks['main']['rows'],geometry_checks=checks['geometry']['checks'],geometry_rows=checks['geometry']['rows'],geometry_fault=checks['geometry']['fault'],receipts={n:sha(export/'build'/n/'result.json') for n in checks},checker_sha256=sha(Path(__file__)),scope='Fresh public source export with no originals, analysis artifacts, prior objects or ancestor Git. Exact parent/module binaries, real DOS lease tests and normal-main synthetic-UART observer repeated; no physical hardware acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS cold export',len(sources),'files; exact parent/module; lease and main gates repeated')

if __name__=='__main__':main()
