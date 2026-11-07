#!/usr/bin/env python3
"""Preserve non-Meta passive observers and native BIOS helper bytes."""
import argparse,json,subprocess
from pathlib import Path
from product_inputs import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--base-revision',default='4b84579');a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 revision=subprocess.check_output(['git','rev-parse','--verify',a.base_revision+'^{commit}'],cwd=ROOT,text=True).strip();rows=[];sources={};captures={}
 for n,variants in [('standalone/file_directory_bbs_watch.asm',[[],['FILE_VIEWER_ROUNDTRIP'],['EXTERNAL_VIEWER_ROUNDTRIP']]),('lab/bbs/audio_synchronet_editor_keys.asm',[[],['FILE_DIRECTORY_ROUNDTRIP'],['FILE_VIEWER_ROUNDTRIP']])]:
  original=out/Path(n).name;original.write_bytes(subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT));sources[n]=sha(ROOT/n)
  for i,flags in enumerate(variants):
   paths=[]
   for label,source in [('old',original),('new',ROOT/n)]:
    dest=out/(Path(n).stem+str(i)+label+'.COM');subprocess.run(['nasm','-fbin',*['-D'+f for f in flags],str(source),'-o',str(dest)],check=True);paths.append(dest);captures[str(dest.relative_to(ROOT))]=sha(dest)
   assert paths[0].read_bytes()==paths[1].read_bytes();rows.append(dict(source=n,flags=flags,sha256=sha(paths[0]),original_source_sha256=sha(original)))
 sources['lab/bbs/check_meta_front_helper_variants.py']=sha(Path(__file__))
 (out/'result.json').write_text(json.dumps(dict(passed=True,cases=rows,sources=sources,base_revision=revision,captures=captures),indent=2)+'\n');print('PASS unchanged observer/BIOS-helper variants:',len(rows))
if __name__=='__main__':main()
