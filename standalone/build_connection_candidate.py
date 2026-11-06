#!/usr/bin/env python3
"""Build the reviewed connection candidate and verify its complete public archive."""
import argparse,json,subprocess,sys
from pathlib import Path
from package_connection_test import ROOT,sha,stage

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output-dir',type=Path,default=ROOT/'build/connection-candidate',help='New directory under build/; existing outputs are never replaced')
 p.add_argument('--recipe',type=Path,default=ROOT/'standalone/connection_candidate_recipe.json',help='Reviewed public payload recipe; defaults to the preceding viewer baseline')
 a=p.parse_args();out=a.output_dir.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists(),'Choose a new build output directory'
 recipe_path=a.recipe.resolve();assert recipe_path.is_relative_to(ROOT),'Recipe must be inside the source tree';r=json.loads(recipe_path.read_text())
 assert r['kind']=='reviewed-source-only-connection-candidate' and r['dos_directory']=='PCPLUS'
 assert len(r['terminal_flags'])==len(set(r['terminal_flags'])) and all(s.startswith('--') for s in r['terminal_flags'])
 out.mkdir(parents=True);log=out/'build.log'
 def run(arguments):
  with log.open('a') as f:subprocess.run([sys.executable,*arguments],cwd=ROOT,stdout=f,stderr=f,check=True)
 terminal=out/'terminal';runner=out/'aspect';compiler=out/'compiler';setup=out/'setup';translation=out/'translation'
 run(['standalone/build_terminal.py',*r['terminal_flags'],'--output-dir',str(terminal)])
 code="import sys;from pathlib import Path;sys.path.insert(0,'standalone');from build_aspect_process import main;main(parent_render=True,output=Path(sys.argv[1]),notice_bank=True,notice_sound=True,notice_input=True,notice_help=True,help_resource=True,serial_bank=True,register_handoff=True,custom_irq=True)"
 run(['-c',code,str(runner)])
 code="import sys;from pathlib import Path;sys.path.insert(0,'standalone');import build_aspect_compiler_dos as c;c.OUT=Path(sys.argv[1]);c.main()"
 run(['-c',code,str(compiler)])
 run(['standalone/build_setup.py','--mouse','--notice-sound','--custom-irq','--output-dir',str(setup)])
 run(['standalone/build_xlt_editor.py','--output-dir',str(translation)])
 products={n:d/n for n,d in [('TERMINAL.EXE',terminal),('ASPECT.EXE',runner),('ASPCOMP.EXE',compiler),('PRMEDIT.EXE',setup),('XLTEDIT.EXE',translation)]}
 for n,binary in products.items():assert sha(binary)==r['expected_files'][n],n+' differs from the reviewed candidate; see build.log'
 package=out/'package';m=stage(package,products,r['source_base_commit'],r['dos_directory'])
 assert m['files']==r['expected_files'],'Public package differs from the reviewed candidate'
 run(['standalone/archive_connection_test_package.py','--package',str(package),'--output',str(out/'archive')])
 archive=json.loads((out/'archive/result.json').read_text());assert archive['passed'] and archive['archive_sha256']==r['expected_archive_sha256']
 sources=['standalone/build_connection_candidate.py',str(recipe_path.relative_to(ROOT)),'standalone/archive_connection_test_package.py','tools/build-connection-candidate','tools/dev','nix/flake.nix','nix/flake.lock']
 result=dict(passed=True,source_base_commit=r['source_base_commit'],recipe_sha256=sha(recipe_path),files=m['files'],package_manifest_sha256=sha(package/'manifest.json'),archive_sha256=archive['archive_sha256'],sources={n:sha(ROOT/n) for n in sources},original_inputs=[],card_written=False,selector_changed=False,scope=__doc__+' The tracked recipe pins the reviewed payload and package source identity. Uses current source and fails if any public application byte differs; no configuration, originals or previous objects are copied into application builds. Physical acceptance and full original parity remain separate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Built reviewed candidate:',out/'archive/PCPLUSSE.ZIP');print('SHA256:',archive['archive_sha256']);print('No card, live service or selected-package changes.')
if __name__=='__main__':main()
