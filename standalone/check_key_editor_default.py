#!/usr/bin/env python3
"""Compare default strict-reader EXE to pre-seam public source; special Git check."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 source='src/key_mapping/key_actions_dos.c';old=subprocess.check_output(['git','show',a.baseline+':'+source],cwd=ROOT);current=(ROOT/source).read_bytes()
 seam=b'#ifdef KEY_EDITOR_FS\n#include "key_file_fs.h"\n#define _dos_open key_file_open\n#define _dos_read key_file_read\n#define _dos_close key_file_close\n#endif\n';assert current.replace(seam,b'',1)==old
 reader=ROOT/'build/key-actions-dos';checks=json.loads((reader/'checks.json').read_text());assert checks['passed'] and checks['sources'][source]==sha(ROOT/source)
 (out/'key_actions_dos.c').write_bytes(old)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/key_mapping'),'-fe=BASELINE.EXE',str(out/'key_actions_dos.c'),str(reader/'real.c')],cwd=out,check=True)
 baseline=sha(out/'BASELINE.EXE');assert baseline==sha(reader/'KAREAL.EXE')==checks['binary_sha256']['KAREAL.EXE']
 result=dict(passed=True,baseline_commit=a.baseline,disabled_reader_binary_sha256=baseline,baseline_source_sha256=hashlib.sha256(old).hexdigest(),sources={source:sha(ROOT/source),'standalone/check_key_editor_default.py':sha(Path(__file__))},scope='Default reader diagnostic is byte-identical to pre-seam public source. Special check uses Git history; normal product/isolated builds do not. Not a full parent rebuild.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS default-disabled reader exact:',baseline)
if __name__=='__main__':main()
