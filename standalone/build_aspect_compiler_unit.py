#!/usr/bin/env python3
"""Build the DOS compiler declaration/procedure inventory diagnostic."""
import json,subprocess
from pathlib import Path
from build_aspect_compiler_lexer import ROOT,sha
OUT=ROOT/'build/aspect-compiler-unit'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 names=['compiler_lexer.c','compiler_lexer.h','compiler_unit.c','compiler_unit.h','compiler_unit_dump.c','compiler_unit_dump.h','compiler_unit_probe.c']
 sources=[ROOT/'src/aspect'/name for name in names]
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-s','-w4','-we','-k8192','-fm=ASPINV.map','-fe=ASPINV.EXE',*[str(p) for p in sources if p.suffix=='.c']],cwd=OUT,check=True)
 sources.extend([Path(__file__),ROOT/'standalone/build_aspect_compiler_lexer.py'])
 report=dict(binary_sha256=sha(OUT/'ASPINV.EXE'),sources={str(p.relative_to(ROOT)):sha(p) for p in sources},original_inputs=[],platform='8086DOS large-model C,8192B stack, owned far heap',scope='Compiler first-pass inventory only: globals, procedures, local/parameter layout, initializer and body source ranges. No expression/body validation, pruning, ASX output or runtime source compilation yet.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('ASPINV.EXE',report['binary_sha256'])
if __name__=='__main__':main()
